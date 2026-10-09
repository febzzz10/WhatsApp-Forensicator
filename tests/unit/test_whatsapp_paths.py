from wft.acquisition.whatsapp_paths import (
    WHATSAPP_PACKAGE,
    PathCandidate,
    is_eligible_artifact,
    is_encrypted_artifact,
    plan_database_paths,
)
from wft.application.services.adb_service import RootAccess


def test_plan_none_returns_public_paths_only():
    candidates = plan_database_paths(RootAccess.NONE)
    assert len(candidates) == 2
    assert all(c.artifact_type == "WHATSAPP_DATABASE" for c in candidates)
    assert all(c.requires_root is False for c in candidates)
    assert all(c.expected_handling == "ACQUIRE_VERBATIM" for c in candidates)
    paths = [c.remote_path for c in candidates]
    assert paths == [
        "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases",
        "/sdcard/WhatsApp/Databases",
    ]


def test_plan_su_includes_private_and_key_paths():
    candidates = plan_database_paths(RootAccess.SU)
    paths = [c.remote_path for c in candidates]
    assert "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases" in paths
    assert "/data/data/com.whatsapp/databases" in paths
    assert "/data/data/com.whatsapp/files/key" in paths

    rooted = [c for c in candidates if c.requires_root]
    assert len(rooted) == 2
    assert all(c.artifact_type in ("WHATSAPP_DATABASE", "WHATSAPP_KEY_MATERIAL") for c in rooted)
    assert {c.artifact_type for c in rooted} == {"WHATSAPP_DATABASE", "WHATSAPP_KEY_MATERIAL"}


def test_plan_adb_root_capable_does_not_imply_active_root():
    candidates = plan_database_paths(RootAccess.ADB_ROOT_CAPABLE)
    paths = [c.remote_path for c in candidates]
    assert "/sdcard/Android/media/com.whatsapp/WhatsApp/Databases" in paths
    assert "/data/data/com.whatsapp/databases" not in paths
    assert "/data/data/com.whatsapp/files/key" not in paths
    assert all(c.requires_root is False for c in candidates)


def test_plan_is_deterministic():
    first = plan_database_paths(RootAccess.SU)
    second = plan_database_paths(RootAccess.SU)
    assert [c.remote_path for c in first] == [c.remote_path for c in second]
    assert first[0] == second[0]


def test_package_is_com_whatsapp():
    assert WHATSAPP_PACKAGE == "com.whatsapp"
    for candidate in plan_database_paths(RootAccess.SU):
        assert "com.whatsupport" not in candidate.remote_path


def test_eligible_database_artifacts():
    for name in [
        "msgstore.db",
        "msgstore.db.crypt12",
        "msgstore.db.crypt14",
        "msgstore.db.crypt15",
        "wa.db",
        "calls.db",
        "axolotl.db",
        "msgstore.db-wal",
        "msgstore.db-journal",
    ]:
        assert is_eligible_artifact(name), name


def test_eligible_key_artifact_only_for_key_material():
    key_candidate = PathCandidate(
        remote_path="/data/data/com.whatsapp/files/key",
        artifact_type="WHATSAPP_KEY_MATERIAL",
        requires_root=True,
        expected_handling="ACQUIRE_VERBATIM",
        description="WhatsApp encryption key file",
    )
    assert is_eligible_artifact("key", key_candidate)
    assert not is_eligible_artifact("msgstore.db", key_candidate)


def test_ineligible_artifacts_rejected():
    for name in ["photo.jpg", "Backup.xml", ".nomedia", "msgstore.db.bak.old", "key2"]:
        assert not is_eligible_artifact(name), name


def test_encrypted_artifact_detection():
    assert is_encrypted_artifact("msgstore.db.crypt14")
    assert is_encrypted_artifact("msgstore.db.crypt15")
    assert is_encrypted_artifact("msgstore.db.crypt12")
    assert not is_encrypted_artifact("msgstore.db")
    assert not is_encrypted_artifact("wa.db")
