from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from PySide6.QtCore import Signal, QObject, QRunnable

from wft.ui.workers.worker_base import CancellationToken, thread_pool
from wft.application.services.adb_service import (
    AdbService, AdbDevice, AdbState, AdbError,
)
from wft.application.services.evidence_service import EvidenceService
from wft.application.services.audit_service import AuditService
from wft.infrastructure.hashing.hashing_service import HashingService
from wft.infrastructure.filesystem.file_store import FileStore


def _now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class AdbOperationType(Enum):
    SCAN = "scan"
    START_SERVER = "start_server"
    KILL_SERVER = "kill_server"
    DEVICE_DETAILS = "device_details"
    VALIDATE_PATH = "validate_path"
    IMPORT_USER_EXPORT = "import_user_export"
    COPY_ACCESSIBLE_MEDIA = "copy_accessible_media"
    RECORD_DEVICE_METADATA = "record_device_metadata"
    EXTRACT_WHATSAPP_DATABASES = "extract_whatsapp_databases"


ACCESSIBLE_MEDIA_PATHS: list[str] = [
    "/sdcard/DCIM/Camera",
    "/sdcard/DCIM/Screenshots",
    "/sdcard/Pictures",
    "/sdcard/Download",
    "/sdcard/Movies",
    "/sdcard/Music",
]


class AdbOperationSignals(QObject):
    started = Signal()
    progress = Signal(str, int, int)
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()


def _make_adb_service(configured_path: Optional[str] = None) -> AdbService:
    svc = AdbService(configured_path=configured_path)
    svc.find_adb()
    return svc


class AdbOperationWorker(QRunnable):
    def __init__(
        self,
        operation: AdbOperationType,
        configured_path: Optional[str] = None,
        serial: Optional[str] = None,
        timeout: int = 10,
        token: Optional[CancellationToken] = None,
        _service_override: Optional[AdbService] = None,
        case_dir: Optional[Path] = None,
        db_path: Optional[Path] = None,
        evidence_service: Optional[EvidenceService] = None,
        audit_service: Optional[AuditService] = None,
        hash_service: Optional[HashingService] = None,
        file_store: Optional[FileStore] = None,
        examiner_id: Optional[int] = None,
        case_id: Optional[int] = None,
    ) -> None:
        super().__init__()
        self._operation = operation
        self._configured_path = configured_path
        self._serial = serial
        self._timeout = timeout
        self._token = token or CancellationToken()
        self._service_override = _service_override
        self._case_dir = case_dir
        self._db_path = db_path
        self._evidence_service = evidence_service
        self._audit_service = audit_service
        self._hash_service = hash_service
        self._file_store = file_store
        self._examiner_id = examiner_id
        self._case_id = case_id
        self.signals = AdbOperationSignals()

    def run(self) -> None:
        if self._token.cancelled:
            self.signals.cancelled.emit()
            self.signals.finished.emit(None)
            return
        self.signals.started.emit()
        try:
            svc = self._service_override or _make_adb_service(self._configured_path)
            result = self._do_operation(svc)
            if self._token.cancelled:
                self.signals.cancelled.emit()
                self.signals.finished.emit(None)
            else:
                self.signals.finished.emit(result)
        except Exception as exc:
            if self._token.cancelled:
                self.signals.cancelled.emit()
                self.signals.finished.emit(None)
            else:
                self.signals.error.emit(str(exc))

    def _do_operation(self, svc: AdbService) -> object:
        if self._operation == AdbOperationType.SCAN:
            return self._scan(svc)
        elif self._operation == AdbOperationType.START_SERVER:
            svc.start_server(timeout=self._timeout)
            return True
        elif self._operation == AdbOperationType.KILL_SERVER:
            svc.kill_server(timeout=self._timeout)
            return True
        elif self._operation == AdbOperationType.DEVICE_DETAILS:
            if not self._serial:
                raise AdbError("Serial required for device details")
            return svc.get_device_details(self._serial, timeout=self._timeout)
        elif self._operation == AdbOperationType.VALIDATE_PATH:
            return svc.validate_path(self._configured_path or "")
        elif self._operation == AdbOperationType.COPY_ACCESSIBLE_MEDIA:
            return self._copy_accessible_media(svc)
        elif self._operation == AdbOperationType.RECORD_DEVICE_METADATA:
            return self._record_device_metadata(svc)
        elif self._operation == AdbOperationType.EXTRACT_WHATSAPP_DATABASES:
            return self._extract_whatsapp_databases(svc)
        return None

    def _scan(self, svc: AdbService) -> tuple:
        adb_state = svc.get_state()
        devices: list[AdbDevice] = []
        if adb_state == AdbState.CONNECTED and not self._token.cancelled:
            devices = svc.list_devices(timeout=self._timeout)
        return (adb_state, devices)

    def _record_device_metadata(self, svc: AdbService) -> object:
        from wft.application.services.acquisition_results import DeviceMetadataResult
        from wft.infrastructure.database.uow import UnitOfWork
        from wft.application.services.evidence_service import EvidenceRepository

        if not self._serial:
            raise AdbError("Serial required to record device metadata")
        if not self._case_dir or not self._db_path or not self._evidence_service:
            raise AdbError("Case context required to record device metadata")
        if not self._hash_service:
            raise AdbError("Hash service required to record device metadata")

        self.signals.progress.emit("Collecting device metadata...", 10, 100)
        device = svc.get_device_details(self._serial, timeout=self._timeout)

        self.signals.progress.emit("Serialising metadata...", 40, 100)
        metadata = {
            "schema_version": "1.0",
            "acquisition_timestamp_utc": _now_utc(),
            "device_serial": device.serial,
            "device_model": device.model,
            "device_manufacturer": device.manufacturer,
            "android_version": device.android_version,
            "sdk_version": device.sdk_version,
            "product_name": device.product,
            "device_name": device.device_name,
            "transport_id": device.transport_id,
            "connection_type": device.connection_type,
            "authorisation_state": device.state.value,
            "device_state": device.state.value,
        }
        recorded = sum(1 for v in metadata.values() if v is not None and v != "")

        import json
        content = json.dumps(metadata, indent=2, ensure_ascii=False)

        ts = _now_utc().replace(":", "-").replace("Z", "")
        rel_dir = "derived/metadata"
        rel_path = "{}/device_metadata_{}_{}.json".format(rel_dir, ts, self._serial[:8])
        if self._file_store:
            dest = self._file_store.resolve(rel_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            dest = self._case_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)

        self.signals.progress.emit("Writing metadata artifact...", 60, 100)
        dest.write_text(content, encoding="utf-8")
        hash_value = self._hash_service.sha256(dest)

        self.signals.progress.emit("Registering evidence...", 80, 100)
        case_id = self._case_id if self._case_id is not None else 0
        evidence_code = "META-{:04d}".format(abs(hash(hash_value)) % 10000)

        from wft.infrastructure.database.uow import UnitOfWork
        uow = UnitOfWork(self._db_path)
        with uow:
            item_data = {
                "case_id": case_id,
                "evidence_code": evidence_code,
                "title": "Device Metadata - {} ({})".format(
                    device.model or "Unknown", device.serial[:8]
                ),
                "source_type": "METADATA_ACQUISITION",
                "acquisition_method": "ADB_LOGICAL",
                "state": "VERIFIED",
                "imported_at_utc": _now_utc(),
                "created_at_utc": _now_utc(),
                "updated_at_utc": _now_utc(),
            }
            repo = EvidenceRepository(uow.db)
            item_id = repo.create_item(item_data)

            file_data = {
                "evidence_item_id": item_id,
                "file_code": "F001",
                "original_filename": dest.name,
                "original_source_path": str(dest.resolve()),
                "stored_relative_path": rel_path,
                "size_bytes": dest.stat().st_size,
                "imported_at_utc": _now_utc(),
                "is_original_copy": 1,
                "is_read_only": 0,
                "verification_status": "VALIDATED",
                "created_at_utc": _now_utc(),
                "updated_at_utc": _now_utc(),
            }
            file_id = repo.add_file(file_data)

            hash_entry = {
                "evidence_file_id": file_id,
                "algorithm": "SHA256",
                "hash_value": hash_value,
                "purpose": "ACQUISITION",
                "calculated_at_utc": _now_utc(),
                "calculated_by_tool_version": "1.0.0a1",
                "created_at_utc": _now_utc(),
            }
            repo.add_hash(hash_entry)

            if self._audit_service:
                self._audit_service.record_event(
                    uow.db, case_id,
                    "DEVICE_METADATA_RECORDED",
                    "Device metadata recorded: {} fields from {}".format(
                        recorded, device.serial[:8]
                    ),
                    component_name="adb_scan_worker",
                    object_type="evidence_item",
                    object_id=str(item_id),
                    examiner_id=self._examiner_id,
                )
            uow.commit()

        self.signals.progress.emit("Metadata recording complete.", 100, 100)
        return DeviceMetadataResult(
            artifact_path=rel_path,
            evidence_id=item_id,
            hash_value=hash_value,
            fields_recorded=recorded,
        )

    def _copy_accessible_media(self, svc: AdbService) -> object:
        from wft.application.services.acquisition_results import MediaAcquisitionResult
        from wft.infrastructure.database.uow import UnitOfWork

        if not self._serial:
            raise AdbError("Serial required to copy media")
        if not self._case_dir:
            raise AdbError("Case directory required to copy media")

        destination = str(self._case_dir / "originals" / "adb_media")
        dest_dir = Path(destination)
        dest_dir.mkdir(parents=True, exist_ok=True)

        copied_count = 0
        skipped_count = 0
        failed_count = 0
        total_bytes = 0
        evidence_ids: list[int] = []
        warnings: list[str] = []

        self.signals.progress.emit("Enumerating media directories...", 5, 100)

        all_files: list[tuple[str, int]] = []
        for source_path in ACCESSIBLE_MEDIA_PATHS:
            if self._token.cancelled:
                return MediaAcquisitionResult(
                    destination=destination, copied_count=copied_count,
                    skipped_count=skipped_count, failed_count=failed_count,
                    total_bytes=total_bytes, evidence_ids=evidence_ids,
                    warnings=warnings + ["Cancelled by user"],
                )
            try:
                entries = svc.list_directory(self._serial, source_path, timeout=10)
                for entry in entries:
                    if not entry or entry.startswith("."):
                        continue
                    full_path = "{}/{}".format(source_path, entry)
                    all_files.append((full_path, 0))
            except (AdbError, OSError) as exc:
                warnings.append("Could not list {}: {}".format(source_path, exc))

        total = len(all_files)
        if total == 0:
            self.signals.progress.emit("No media files found.", 100, 100)
            return MediaAcquisitionResult(
                destination=destination, copied_count=0,
                skipped_count=0, failed_count=0,
                total_bytes=0, evidence_ids=[], warnings=warnings,
            )

        for idx, (remote_path, _) in enumerate(all_files):
            if self._token.cancelled:
                return MediaAcquisitionResult(
                    destination=destination, copied_count=copied_count,
                    skipped_count=skipped_count, failed_count=failed_count,
                    total_bytes=total_bytes, evidence_ids=evidence_ids,
                    warnings=warnings + ["Cancelled by user"],
                )

            progress_pct = int(5 + (idx / total) * 90)
            self.signals.progress.emit(
                "Copying {}/{}: {}".format(idx + 1, total, remote_path),
                progress_pct, 100,
            )

            try:
                local_rel = remote_path.lstrip("/").replace("/", "_")
                local_path = dest_dir / local_rel
                if local_path.exists():
                    skipped_count += 1
                    continue

                svc.pull_file(self._serial, remote_path, local_path, timeout=60)
                size = local_path.stat().st_size
                total_bytes += size
                copied_count += 1
            except AdbError as exc:
                failed_count += 1
                warnings.append("Failed to copy {}: {}".format(remote_path, exc))

        self.signals.progress.emit("Registering evidence...", 95, 100)

        case_id = self._case_id if self._case_id is not None else 0
        if copied_count > 0 and self._evidence_service and self._db_path:
            uow = UnitOfWork(self._db_path)
            with uow:
                evidence_code = "MEDIA-ADB-{:04d}".format(abs(hash(str(dest_dir))) % 10000)
                item_data = {
                    "case_id": case_id,
                    "evidence_code": evidence_code,
                    "title": "ADB Media Acquisition - {} files".format(copied_count),
                    "source_type": "MEDIA_DIRECTORY",
                    "acquisition_method": "ADB_LOGICAL",
                    "state": "VERIFIED",
                    "imported_at_utc": _now_utc(),
                    "created_at_utc": _now_utc(),
                    "updated_at_utc": _now_utc(),
                }
                from wft.application.services.evidence_service import EvidenceRepository
                repo = EvidenceRepository(uow.db)
                item_id = repo.create_item(item_data)
                evidence_ids.append(item_id)

                file_data = {
                    "evidence_item_id": item_id,
                    "file_code": "F001",
                    "original_filename": "adb_media_acquisition",
                    "original_source_path": destination,
                    "stored_relative_path": "originals/adb_media",
                    "size_bytes": total_bytes,
                    "imported_at_utc": _now_utc(),
                    "is_original_copy": 1,
                    "is_read_only": 0,
                    "verification_status": "VALIDATED",
                    "created_at_utc": _now_utc(),
                    "updated_at_utc": _now_utc(),
                }
                repo.add_file(file_data)

                if self._audit_service:
                    self._audit_service.record_event(
                        uow.db, case_id,
                        "MEDIA_ACQUIRED",
                        "ADB media acquisition: {} copied, {} skipped, {} failed".format(
                            copied_count, skipped_count, failed_count
                        ),
                        component_name="adb_scan_worker",
                        object_type="evidence_item",
                        object_id=str(item_id),
                        examiner_id=self._examiner_id,
                    )
                uow.commit()

        self.signals.progress.emit("Media acquisition complete.", 100, 100)
        return MediaAcquisitionResult(
            destination=destination,
            copied_count=copied_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            total_bytes=total_bytes,
            evidence_ids=evidence_ids,
            warnings=warnings,
        )

    def _extract_whatsapp_databases(self, svc: AdbService) -> object:
        """Acquire WhatsApp database artefacts from a USB ADB device.

        Public (non-root) paths are always attempted; private database/key
        paths only when `su` root access is actually available. Encrypted
        crypt12/14/15 backups are acquired byte-for-byte and remain
        decryption-pending. No parsing and no decryption happen here.
        """
        from wft.application.services.acquisition_results import (
            WhatsAppDatabaseArtifact, WhatsAppDatabaseExtractionResult,
        )
        from wft.infrastructure.database.uow import UnitOfWork
        from wft.application.services.evidence_service import EvidenceRepository
        from wft.acquisition.whatsapp_paths import (
            is_eligible_artifact, is_encrypted_artifact, plan_database_paths,
        )

        if not self._serial:
            raise AdbError("Serial required to extract WhatsApp databases")
        if not self._case_dir or not self._db_path:
            raise AdbError("Case context required to extract WhatsApp databases")
        if not self._hash_service:
            raise AdbError("Hash service required to extract WhatsApp databases")

        case_dir = Path(self._case_dir)
        serial = self._serial
        dest_rel = "originals/adb_databases"

        def build_result(status, artifacts, failures, unavailable, warnings, root_access,
                         item_id=None, audit_hash=None):
            return WhatsAppDatabaseExtractionResult(
                status=status,
                device_serial=serial,
                root_access=root_access.value,
                destination=str(case_dir / dest_rel),
                artifacts=artifacts,
                failures=failures,
                unavailable_paths=unavailable,
                warnings=warnings,
                evidence_item_id=item_id,
                audit_event_hash=audit_hash,
            )

        self.signals.progress.emit("Detecting device capabilities...", 5, 100)
        root_access = svc.detect_root(serial, timeout=self._timeout)
        self.signals.progress.emit(
            "Root access state: {}".format(root_access.value), 10, 100
        )

        candidates = plan_database_paths(root_access)
        failures: list[str] = []
        unavailable: list[str] = []
        warnings: list[str] = []
        to_pull: list[tuple[object, str]] = []

        self.signals.progress.emit("Enumerating WhatsApp database paths...", 15, 100)
        for candidate in candidates:
            if self._token.cancelled:
                return build_result(
                    "CANCELLED", [], failures, unavailable,
                    warnings + ["Cancelled by user"], root_access,
                )
            try:
                entries = svc.list_directory(
                    serial, candidate.remote_path, timeout=self._timeout
                )
            except (AdbError, OSError) as exc:
                unavailable.append(
                    "{} (not present: {})".format(candidate.remote_path, exc)
                )
                continue
            eligible = [e for e in entries if is_eligible_artifact(e, candidate)]
            if not eligible:
                unavailable.append(
                    "{} (no eligible WhatsApp artefacts)".format(candidate.remote_path)
                )
                continue
            base = candidate.remote_path.rstrip("/")
            for name in eligible:
                to_pull.append((candidate, "{}/{}".format(base, name)))

        if self._token.cancelled:
            return build_result(
                "CANCELLED", [], failures, unavailable,
                warnings + ["Cancelled by user"], root_access,
            )

        if not to_pull:
            return build_result("NO_FILES_FOUND", [], failures, unavailable, warnings, root_access)

        dest_dir = case_dir / dest_rel
        dest_dir.mkdir(parents=True, exist_ok=True)

        artifacts: list[WhatsAppDatabaseArtifact] = []
        total = len(to_pull)
        for index, (candidate, remote_path) in enumerate(to_pull):
            if self._token.cancelled:
                status = "PARTIAL" if artifacts else "CANCELLED"
                return build_result(
                    status, artifacts, failures, unavailable,
                    warnings + ["Cancelled by user"], root_access,
                )

            pct = int(20 + (index / total) * 65)
            self.signals.progress.emit(
                "Acquiring {}/{}: {}".format(index + 1, total, remote_path), pct, 100
            )

            local_name = remote_path.lstrip("/").replace("/", "_")
            if (dest_dir / local_name).exists():
                local_name = "{}_{}".format(
                    local_name, _now_utc().replace(":", "-").replace(".", "-")
                )
            local_rel = "{}/{}".format(dest_rel, local_name)
            local_path = case_dir / local_rel

            try:
                svc.pull_file(serial, remote_path, local_path, timeout=self._timeout * 6)
            except (AdbError, OSError) as exc:
                failures.append("{} (pull failed: {})".format(remote_path, exc))
                continue

            try:
                digest = self._hash_service.sha256(local_path)
            except Exception as exc:
                raise AdbError(
                    "Hashing failed for {}: {}".format(remote_path, exc)
                )

            if self._file_store:
                try:
                    self._file_store.set_read_only(local_rel)
                except OSError:
                    pass

            artifacts.append(
                WhatsAppDatabaseArtifact(
                    remote_path=remote_path,
                    local_path=local_rel,
                    size_bytes=local_path.stat().st_size,
                    sha256=digest,
                    encrypted=is_encrypted_artifact(Path(remote_path).name),
                    artifact_type=candidate.artifact_type,
                    requires_root=candidate.requires_root,
                )
            )

        encrypted_count = sum(1 for a in artifacts if a.encrypted)
        if encrypted_count:
            warnings.append(
                "{} encrypted artefact(s) acquired byte-for-byte; "
                "decryption pending (not performed by this tool).".format(encrypted_count)
            )

        if artifacts and failures:
            status = "PARTIAL"
        elif failures and not artifacts:
            return build_result("FAILED", artifacts, failures, unavailable, warnings, root_access)
        else:
            status = "ACQUIRED"

        self.signals.progress.emit("Registering evidence...", 92, 100)

        case_id = self._case_id if self._case_id is not None else 0
        evidence_code = "WADB-{:04d}".format(
            abs(hash("{}:{}".format(serial, _now_utc()))) % 10000
        )
        audit_hash = None
        item_id = None
        try:
            uow = UnitOfWork(self._db_path)
            with uow:
                repo = EvidenceRepository(uow.db)
                item_id = repo.create_item(
                    {
                        "case_id": case_id,
                        "evidence_code": evidence_code,
                        "title": "WhatsApp Database Acquisition - {} ({} files)".format(
                            serial[:8], len(artifacts)
                        ),
                        "description": (
                            "ADB logical acquisition of WhatsApp database artefacts. "
                            "Root access state: {}. Encrypted artefacts: {}. Failures: {}."
                        ).format(root_access.value, encrypted_count, len(failures)),
                        "source_type": "WHATSAPP_DATABASE_ACQUISITION",
                        "acquisition_method": "ADB_LOGICAL",
                        "source_application": "com.whatsapp",
                        "source_device_identifier": serial,
                        "state": "VERIFIED",
                        "imported_at_utc": _now_utc(),
                        "created_at_utc": _now_utc(),
                        "updated_at_utc": _now_utc(),
                    }
                )
                for code_index, artifact in enumerate(artifacts, start=1):
                    file_id = repo.add_file(
                        {
                            "evidence_item_id": item_id,
                            "file_code": "F{:03d}".format(code_index),
                            "original_filename": Path(artifact.remote_path).name,
                            "original_source_path": artifact.remote_path,
                            "stored_relative_path": artifact.local_path,
                            "size_bytes": artifact.size_bytes,
                            "imported_at_utc": _now_utc(),
                            "is_original_copy": 1,
                            "is_read_only": 1,
                            "verification_status": "VALIDATED",
                            "created_at_utc": _now_utc(),
                            "updated_at_utc": _now_utc(),
                        }
                    )
                    artifact.evidence_file_id = file_id
                    repo.add_hash(
                        {
                            "evidence_file_id": file_id,
                            "algorithm": "SHA256",
                            "hash_value": artifact.sha256,
                            "purpose": "ACQUISITION",
                            "calculated_at_utc": _now_utc(),
                            "calculated_by_tool_version": "1.0.0a1",
                            "created_at_utc": _now_utc(),
                        }
                    )
                if self._audit_service:
                    audit_hash = self._audit_service.record_event(
                        uow.db,
                        case_id,
                        "WHATSAPP_DATABASES_ACQUIRED",
                        "WhatsApp database acquisition: {} acquired, {} failed, "
                        "{} unavailable paths, root={}".format(
                            len(artifacts), len(failures), len(unavailable),
                            root_access.value,
                        ),
                        component_name="adb_scan_worker",
                        object_type="evidence_item",
                        object_id=str(item_id),
                        examiner_id=self._examiner_id,
                        details={
                            "device_serial": serial,
                            "root_access": root_access.value,
                            "acquisition_method": "ADB_LOGICAL",
                            "artifact_count": len(artifacts),
                            "encrypted_artifact_count": encrypted_count,
                            "failure_count": len(failures),
                            "unavailable_path_count": len(unavailable),
                            "failures": failures,
                            "unavailable_paths": unavailable,
                            "artifacts": [
                                {
                                    "remote_path": a.remote_path,
                                    "sha256": a.sha256,
                                    "encrypted": a.encrypted,
                                }
                                for a in artifacts
                            ],
                        },
                    )
                uow.commit()
        except AdbError:
            raise
        except Exception as exc:
            raise AdbError("Evidence registration failed: {}".format(exc))

        self.signals.progress.emit("Database acquisition complete.", 100, 100)
        return build_result(status, artifacts, failures, unavailable, warnings, root_access,
                            item_id=item_id, audit_hash=audit_hash)

    def cancel(self) -> None:
        self._token.cancel()


def run_adb_operation(
    operation: AdbOperationType,
    configured_path: Optional[str] = None,
    serial: Optional[str] = None,
    timeout: int = 10,
    token: Optional[CancellationToken] = None,
    on_finished: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
) -> AdbOperationWorker:
    worker = AdbOperationWorker(
        operation=operation,
        configured_path=configured_path,
        serial=serial,
        timeout=timeout,
        token=token,
    )
    if on_finished:
        worker.signals.finished.connect(on_finished)
    if on_error:
        worker.signals.error.connect(on_error)
    thread_pool.start(worker)
    return worker
