import os
import pytest
from pathlib import Path

from scripts.backup_db import run_backup, calculate_sha256
from scripts.restore_db import run_restore
from scripts.validate_schema_integrity import audit_schema_integrity


def test_01_backup_generates_sha256_checksum(tmp_path):
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)

    assert os.path.exists(backup_file)
    checksum_file = f"{backup_file}.sha256"
    assert os.path.exists(checksum_file)

    with open(checksum_file, "r") as f:
        content = f.read().strip()
    expected_hash = calculate_sha256(Path(backup_file))
    assert expected_hash in content


def test_02_restore_verifies_sha256_checksum(tmp_path):
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    target_db = str(tmp_path / "restored_school.db")

    success = run_restore(backup_file, target_database_url=f"sqlite:///{target_db}")
    assert success is True
    assert os.path.exists(target_db)


def test_03_restore_rejects_corrupt_checksum(tmp_path):
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    checksum_file = f"{backup_file}.sha256"

    # Corrupt checksum file
    with open(checksum_file, "w") as f:
        f.write("0000000000000000000000000000000000000000000000000000000000000000  bad_file\n")

    target_db = str(tmp_path / "corrupt_restored.db")

    with pytest.raises(ValueError, match="Checksum validation failed"):
        run_restore(backup_file, target_database_url=f"sqlite:///{target_db}")


def test_04_schema_integrity_audit():
    metrics = audit_schema_integrity()
    assert metrics["total_models"] > 10
    assert metrics["tables_with_primary_key"] == metrics["total_models"]
    assert metrics["tenant_isolated_models"] > 5
