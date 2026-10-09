from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from wft.infrastructure.database.connection import DatabaseConnection
from wft.infrastructure.database.uow import UnitOfWork
from wft.infrastructure.logging.logging_service import LoggingService
from wft.infrastructure.database.artefact_repositories import (
    ContactRepository,
    GroupRepository,
    ConversationRepository,
    MessageRepository,
    CallRepository,
    MediaRepository,
    ParserRunRepository,
)
from wft.application.services.search_index_service import SearchIndexService
from wft.parsers.contracts.interfaces import ParserAdapter, ParseContext
from wft.parsers.exports.text_export_parser import TextExportParser
from wft.parsers.exports.zip_export_parser import ZipExportParser
from wft.parsers.adapters.whatsapp_sqlite_adapter import WhatsAppSQLiteAdapter
from wft.parsers.sqlite.schema_fingerprinter import SchemaFingerprinter, SchemaRegistry, build_default_registry


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


_INSTALLED_PARSERS: list[ParserAdapter] = [
    TextExportParser(),
    ZipExportParser(),
    WhatsAppSQLiteAdapter(),
]


class ParseService:
    def __init__(
        self,
        log: LoggingService,
        parsers: Optional[list[ParserAdapter]] = None,
        search_index_service: Optional[SearchIndexService] = None,
    ) -> None:
        self._log = log
        self._parsers = parsers or list(_INSTALLED_PARSERS)
        self._search_index_svc = search_index_service or SearchIndexService()
        self._fingerprinter = SchemaFingerprinter()
        self._schema_registry = SchemaRegistry()
        build_default_registry(self._schema_registry)

    def select_parser(self, source_path: Path) -> Optional[tuple[ParserAdapter, dict]]:
        for parser in self._parsers:
            try:
                inspection = parser.inspect(source_path)
                if parser.supports(inspection):
                    return parser, inspection
            except Exception as exc:
                self._log.warning(f"Parser {parser.adapter_id} inspection failed: {exc}")
        return None

    def parse_evidence(
        self,
        case_id: int,
        evidence_item_id: int,
        source_file_id: int,
        source_path: Path,
        db_path: Path,
        case_dir: Path,
        display_timezone: str = "UTC",
    ) -> dict:
        selection = self.select_parser(source_path)
        if not selection:
            uow = UnitOfWork(db_path)
            with uow:
                uow.db.execute(
                    "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
                    ("UNSUPPORTED", _now_utc(), evidence_item_id),
                )
                uow.commit()
            return {
                "success": False,
                "status": "UNSUPPORTED",
                "error": "No parser supports this file",
                "message_count": 0,
                "contact_count": 0,
                "group_count": 0,
                "call_count": 0,
                "media_count": 0,
                "warnings": [],
            }

        parser, inspection = selection

        uow = UnitOfWork(db_path)
        with uow:
            run_repo = ParserRunRepository(uow.db)

            run_id = run_repo.create({
                "case_id": case_id,
                "evidence_item_id": evidence_item_id,
                "source_evidence_file_id": source_file_id,
                "parser_name": parser.adapter_id,
                "parser_version": parser.adapter_version,
                "adapter_id": parser.adapter_id,
                "adapter_version": parser.adapter_version,
                "schema_fingerprint": inspection.get("schema_fingerprint"),
            })

            working_dir = case_dir / "working" / f"P{run_id:04d}"
            working_dir.mkdir(parents=True, exist_ok=True)

            try:
                context = WorkingParseContext(
                    case_id=case_id,
                    evidence_item_id=evidence_item_id,
                    source_file_id=source_file_id,
                    working_copy_path=working_dir,
                    timezone=display_timezone,
                )
                parse_result = parser.parse(source_path, context)

                total_warnings = parse_result.get("warnings", [])
                for w in total_warnings:
                    run_repo.add_warning({
                        "parser_run_id": run_id,
                        "warning_code": "PARSE_WARNING",
                        "severity": "WARNING",
                        "message": str(w),
                    })

                contacts_batch = parse_result.get("contacts", [])
                messages_batch = parse_result.get("messages", [])
                groups_batch = parse_result.get("groups", [])
                group_participants_batch = parse_result.get("group_participants", [])
                calls_batch = parse_result.get("calls", [])
                media_batch = parse_result.get("media", [])

                contact_repo = ContactRepository(uow.db)
                group_repo = GroupRepository(uow.db)
                conversation_repo = ConversationRepository(uow.db)
                message_repo = MessageRepository(uow.db)
                call_repo = CallRepository(uow.db)
                media_repo = MediaRepository(uow.db)

                stored_contact_ids: dict[str, int] = {}
                for c in contacts_batch:
                    cid = contact_repo.upsert_by_code(case_id, {
                        "contact_code": c.get("contact_code", ""),
                        "whatsapp_identifier": c.get("whatsapp_identifier"),
                        "phone_number_raw": c.get("phone_number_raw"),
                        "display_name": c.get("display_name"),
                        "given_name": c.get("given_name"),
                        "family_name": c.get("family_name"),
                        "is_business": c.get("is_business", False),
                        "is_blocked": c.get("is_blocked"),
                        "is_saved_contact": c.get("is_saved_contact"),
                        "origin": c.get("origin", "PARSED"),
                        "confidence_level": "HIGH",
                    })
                    stored_contact_ids[c.get("contact_code", "")] = cid

                    run_repo.add_mapping({
                        "parser_run_id": run_id,
                        "source_table": "wa_contacts" if "whatsapp_identifier" in c else "contacts_parsed",
                        "source_column": "display_name",
                        "internal_entity": "contact",
                        "internal_field": "display_name",
                    })

                stored_group_ids: dict[str, int] = {}
                for g in groups_batch:
                    gid = group_repo.upsert_by_wa_id(case_id, {
                        "group_code": g.get("group_code", ""),
                        "whatsapp_group_identifier": g.get("whatsapp_group_identifier"),
                        "subject": g.get("subject"),
                        "origin": g.get("origin", "PARSED"),
                        "confidence_level": "HIGH",
                    })
                    stored_group_ids[g.get("whatsapp_group_identifier", "")] = gid

                for gp in group_participants_batch:
                    g_wa_id = gp.get("group_identifier", "")
                    gid = stored_group_ids.get(g_wa_id)
                    if gid:
                        participant_code = gp.get("participant_identifier", "")
                        matched_cid = None
                        for code, cid in stored_contact_ids.items():
                            if code.endswith(participant_code[-20:]) if participant_code else False:
                                matched_cid = cid
                                break
                        group_repo.add_participant({
                            "group_id": gid,
                            "contact_id": matched_cid,
                            "participant_identifier": participant_code,
                            "role": gp.get("role"),
                            "origin": "PARSED",
                            "confidence_level": "HIGH",
                        })

                conversation_cache: dict[str, int] = {}
                for m in messages_batch:
                    sender_code = m.pop("sender_contact_code", None) or m.get("sender_code")
                    sender_cid = stored_contact_ids.get(sender_code) if sender_code else None

                    conv_key = m.get("conversation_code", "") or sender_code or "_system"
                    conv_type = "DIRECT"
                    group_conv_key = m.get("group_conversation_code")

                    if conv_key not in conversation_cache:
                        if group_conv_key and group_conv_key in stored_group_ids:
                            gid = stored_group_ids[group_conv_key]
                            conv_id = conversation_repo.upsert_by_group(case_id, gid, m.get("group_name", ""))
                            conversation_cache[conv_key] = conv_id
                        elif sender_cid:
                            conv_id = conversation_repo.upsert_by_contact(
                                case_id, sender_cid, m.get("sender_name") or ""
                            )
                            conversation_cache[conv_key] = conv_id
                        else:
                            conv_id = conversation_repo.create(case_id, {
                                "conversation_code": f"UNK-{len(conversation_cache)+1:06d}",
                                "conversation_type": "UNKNOWN",
                                "title": m.get("sender_name") or "Unknown",
                                "origin": "PARSED",
                            })
                            conversation_cache[conv_key] = conv_id
                    else:
                        conv_id = conversation_cache[conv_key]

                    msg_id = message_repo.create(case_id, {
                        "message_code": m.get("message_code", f"MSG-{hash(str(m)):08x}"),
                        "conversation_id": conv_id,
                        "sender_contact_id": sender_cid,
                        "source_record_id": m.get("source_record_id"),
                        "source_table": m.get("source_table"),
                        "direction": m.get("direction", "UNKNOWN"),
                        "message_type": m.get("message_type", "TEXT"),
                        "text_content": m.get("text_content"),
                        "timestamp_raw": m.get("timestamp_raw"),
                        "timestamp_epoch_value": m.get("timestamp_epoch_value"),
                        "timestamp_epoch_unit": m.get("timestamp_epoch_unit"),
                        "sent_at_utc": m.get("sent_at_utc"),
                        "is_deleted_marker": m.get("is_deleted_marker", False),
                        "is_forwarded": m.get("is_forwarded", False),
                        "origin": m.get("origin", "PARSED"),
                        "source_evidence_file_id": source_file_id,
                        "parser_run_id": run_id,
                    })

                    if m.get("sent_at_utc"):
                        message_repo.update_timestamps(conv_id, m["sent_at_utc"])

                    run_repo.add_timeline_event({
                        "case_id": case_id,
                        "event_code": f"TL-{run_id}-{msg_id}",
                        "event_type": "MESSAGE",
                        "title": m.get("text_content", "(no content)")[:100],
                        "occurred_at_utc": m.get("sent_at_utc"),
                        "artefact_type": "message",
                        "artefact_id": msg_id,
                        "conversation_id": conv_id,
                        "contact_id": sender_cid,
                        "evidence_item_id": evidence_item_id,
                        "origin": "PARSED",
                    })

                media_refs = parse_result.get("media_refs", [])
                for mr in media_refs:
                    media_repo.create(case_id, {
                        "media_code": mr.get("media_code", f"MEDIA-{hash(str(mr)):08x}"),
                        "original_filename": mr.get("text_content", "Media"),
                        "declared_mime_type": mr.get("mime_type") or "application/octet-stream",
                        "is_missing": True,
                        "origin": mr.get("origin", "PARSED"),
                        "source_evidence_file_id": source_file_id,
                        "parser_run_id": run_id,
                    })

                for md in media_batch:
                    media_repo.create(case_id, {
                        "media_code": md.get("media_code", f"MEDIA-{hash(str(md)):08x}"),
                        "original_filename": md.get("original_filename"),
                        "declared_mime_type": md.get("declared_mime_type") or "application/octet-stream",
                        "detected_mime_type": md.get("detected_mime_type"),
                        "size_bytes": md.get("size_bytes"),
                        "sha256": md.get("sha256"),
                        "width_pixels": md.get("width_pixels"),
                        "height_pixels": md.get("height_pixels"),
                        "duration_milliseconds": md.get("duration_milliseconds"),
                        "origin": md.get("origin", "PARSED"),
                        "source_evidence_file_id": source_file_id,
                        "parser_run_id": run_id,
                    })

                for c in calls_batch:
                    conv_id = None
                    call_repo.create(case_id, {
                        "call_code": c.get("call_code", f"CALL-{hash(str(c)):08x}"),
                        "conversation_id": c.get("conversation_id"),
                        "source_record_id": c.get("source_record_id"),
                        "call_type": c.get("call_type", "UNKNOWN"),
                        "direction": c.get("direction", "UNKNOWN"),
                        "timestamp_raw": c.get("timestamp_raw"),
                        "started_at_utc": c.get("started_at_utc"),
                        "duration_seconds": c.get("duration_seconds"),
                        "was_answered": c.get("was_answered"),
                        "origin": c.get("origin", "PARSED"),
                        "source_evidence_file_id": source_file_id,
                        "parser_run_id": run_id,
                    })

                wc = len(total_warnings)
                ec = 0
                parsed_total = (
                    len(contacts_batch) + len(messages_batch) + len(groups_batch)
                    + len(calls_batch) + len(media_batch) + len(media_refs)
                )
                status = "COMPLETED" if parsed_total > 0 else "PARTIAL"

                run_repo.complete(
                    run_id, status, parsed_total, wc, ec,
                    "\n".join(total_warnings[:10]) if total_warnings else None,
                )

                uow.db.execute(
                    "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
                    ("PARSED" if status == "COMPLETED" else "PARTIALLY_PARSED", _now_utc(), evidence_item_id),
                )

                if messages_batch:
                    indexed = self._search_index_svc.create_index(uow.db)
                    self._log.info(
                        f"FTS index {'updated' if indexed else 'not available'} "
                        f"({len(messages_batch)} messages)"
                    )
                uow.commit()

                self._log.info(
                    f"Parser {parser.adapter_id} v{parser.adapter_version} "
                    f"completed: {parsed_total} artefacts, {wc} warnings"
                )

                return {
                    "success": True,
                    "status": status,
                    "run_id": run_id,
                    "parser_id": parser.adapter_id,
                    "parser_version": parser.adapter_version,
                    "message_count": len(messages_batch),
                    "contact_count": len(contacts_batch),
                    "group_count": len(groups_batch),
                    "call_count": len(calls_batch),
                    "media_count": len(media_batch) + len(media_refs),
                    "warnings": total_warnings,
                }

            except Exception as exc:
                run_repo.complete(run_id, "FAILED", 0, 0, 1, str(exc))
                uow.commit()

                uow.db.execute(
                    "UPDATE evidence_items SET state = ?, updated_at_utc = ? WHERE id = ?",
                    ("FAILED", _now_utc(), evidence_item_id),
                )
                uow.commit()
                self._log.error(f"Parser failed for evidence {evidence_item_id}: {exc}")

                return {
                    "success": False,
                    "status": "FAILED",
                    "error": str(exc),
                    "message_count": 0,
                    "contact_count": 0,
                    "group_count": 0,
                    "call_count": 0,
                    "media_count": 0,
                    "warnings": [str(exc)],
                }

    def list_supported_types(self) -> list[dict]:
        result: list[dict] = []
        for parser in self._parsers:
            caps = parser.capabilities()
            result.append({
                "adapter_id": parser.adapter_id,
                "version": parser.adapter_version,
                "supported": caps.get("supported", []),
                "partially_supported": caps.get("partially_supported", []),
            })
        return result

    def inspect_path(self, source_path: Path) -> Optional[dict]:
        for parser in self._parsers:
            try:
                inspection = parser.inspect(source_path)
                if parser.supports(inspection):
                    inspection["adapter_id"] = parser.adapter_id
                    inspection["adapter_version"] = parser.adapter_version
                    return inspection
            except Exception:
                continue
        return None


class WorkingParseContext:
    def __init__(
        self,
        case_id: int,
        evidence_item_id: int,
        source_file_id: int,
        working_copy_path: Path,
        timezone: str,
    ) -> None:
        self.case_id = case_id
        self.evidence_item_id = evidence_item_id
        self.source_file_id = source_file_id
        self.working_copy_path = working_copy_path
        self.timezone = timezone

