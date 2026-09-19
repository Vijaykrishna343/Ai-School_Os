"""
Unit & Integration tests for Database Backup & Restore Tooling (Phase 30.8).
"""

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.backup_db import (
    calculate_sha256 as calc_backup_sha256,
    parse_postgres_url as parse_backup_url,
    run_backup,
    sanitize_database_url as sanitize_backup_url,
)
from scripts.restore_db import (
    calculate_sha256 as calc_restore_sha256,
    parse_postgres_url as parse_restore_url,
    run_restore,
    sanitize_database_url as sanitize_restore_url,
)


class TestBackupRestoreTooling:
    def test_sanitize_database_url(self):
        url = "postgresql://school_user:super_secret_password_123@db.example.com:5432/school_erp"
        sanitized = sanitize_backup_url(url)
        assert "super_secret_password_123" not in sanitized
        assert "school_user:***@db.example.com:5432" in sanitized

        url_no_pass = "postgresql://localhost:5432/school_erp"
        assert sanitize_backup_url(url_no_pass) == url_no_pass

    def test_parse_postgres_url(self):
        url = "postgresql://myuser:mypass@myhost:5433/mydb"
        params = parse_backup_url(url)
        assert params["host"] == "myhost"
        assert params["port"] == "5433"
        assert params["user"] == "myuser"
        assert params["password"] == "mypass"
        assert params["dbname"] == "mydb"

    def test_calculate_sha256(self, tmp_path):
        test_file = tmp_path / "sample.txt"
        content = b"AI School OS Production Backup Verification Data"
        test_file.write_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert calc_backup_sha256(test_file) == expected_hash
        assert calc_restore_sha256(test_file) == expected_hash

    def test_run_backup_sqlite(self, tmp_path):
        db_src = tmp_path / "source.db"
        db_src.write_bytes(b"SQLite Sample Header and Schema")

        storage_dir = tmp_path / "backups"
        db_url = f"sqlite:///{db_src}"

        backup_file = run_backup(
            storage_dir=str(storage_dir),
            retention_days=7,
            database_url=db_url,
        )

        backup_path = Path(backup_file)
        assert backup_path.exists()
        assert backup_path.name.endswith(".db")

        checksum_file = backup_path.parent / f"{backup_path.name}.sha256"
        assert checksum_file.exists()
        expected_hash = calc_backup_sha256(backup_path)
        with open(checksum_file, "r", encoding="utf-8") as f:
            line = f.read().strip()
        assert line.startswith(expected_hash)

    def test_run_backup_missing_db_url(self):
        with patch.dict(os.environ, {}, clear=True), patch("app.core.config.settings.DATABASE_URL", ""):
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            with pytest.raises(ValueError, match="DATABASE_URL must be provided"):
                run_backup(database_url=None)

    @patch("subprocess.run")
    def test_run_backup_postgres_success(self, mock_subproc, tmp_path):
        storage_dir = tmp_path / "backups"
        db_url = "postgresql://school_user:secret_pass@localhost:5432/school_erp"

        def fake_run(cmd, env, capture_output, text, check):
            # simulate pg_dump creating the output file
            out_file = Path(cmd[cmd.index("-f") + 1])
            out_file.write_bytes(b"PG_DUMP_CUSTOM_ARCHIVE_DATA")
            return MagicMock(returncode=0, stderr="")

        mock_subproc.side_effect = fake_run

        backup_file = run_backup(
            storage_dir=str(storage_dir),
            retention_days=10,
            database_url=db_url,
        )

        assert Path(backup_file).exists()
        assert backup_file.endswith(".dump")
        assert (Path(backup_file).parent / f"{Path(backup_file).name}.sha256").exists()

        # Verify password passed via env, not in CLI args
        call_args = mock_subproc.call_args
        cmd_executed = call_args[0][0]
        env_passed = call_args[1]["env"]
        assert "secret_pass" not in cmd_executed
        assert env_passed.get("PGPASSWORD") == "secret_pass"

    @patch("subprocess.run")
    def test_run_backup_postgres_failure(self, mock_subproc, tmp_path):
        storage_dir = tmp_path / "backups"
        db_url = "postgresql://school_user:secret_pass@localhost:5432/school_erp"

        mock_subproc.return_value = MagicMock(returncode=1, stderr="FATAL: password authentication failed")

        with pytest.raises(RuntimeError, match="pg_dump execution failed"):
            run_backup(
                storage_dir=str(storage_dir),
                database_url=db_url,
            )

    def test_run_restore_blocks_unconfirmed(self, tmp_path):
        backup_file = tmp_path / "test.dump"
        backup_file.write_bytes(b"DATA")

        with pytest.raises(PermissionError, match="--confirm flag is required"):
            run_restore(
                backup_file_path=str(backup_file),
                confirmed=False,
            )

    def test_run_restore_missing_file(self, tmp_path):
        non_existent = tmp_path / "missing.dump"
        with pytest.raises(FileNotFoundError):
            run_restore(
                backup_file_path=str(non_existent),
                confirmed=True,
            )

    def test_run_restore_checksum_mismatch(self, tmp_path):
        backup_file = tmp_path / "backup_AISchoolOS_test.dump"
        backup_file.write_bytes(b"ACTUAL_DUMP_CONTENT")

        checksum_file = tmp_path / "backup_AISchoolOS_test.dump.sha256"
        checksum_file.write_text("bad_checksum_hash_value  backup_AISchoolOS_test.dump", encoding="utf-8")

        with pytest.raises(ValueError, match="Checksum validation failed"):
            run_restore(
                backup_file_path=str(backup_file),
                target_database_url="sqlite:///dummy.db",
                verify_checksum=True,
                confirmed=True,
            )

    def test_run_restore_sqlite_success(self, tmp_path):
        backup_file = tmp_path / "backup_AISchoolOS_test.db"
        content = b"VALID_SQLITE_DATA"
        backup_file.write_bytes(content)

        checksum = hashlib.sha256(content).hexdigest()
        checksum_file = tmp_path / "backup_AISchoolOS_test.db.sha256"
        checksum_file.write_text(f"{checksum}  backup_AISchoolOS_test.db", encoding="utf-8")

        target_db = tmp_path / "restored.db"
        success = run_restore(
            backup_file_path=str(backup_file),
            target_database_url=f"sqlite:///{target_db}",
            verify_checksum=True,
            confirmed=True,
        )

        assert success is True
        assert target_db.exists()
        assert target_db.read_bytes() == content

    @patch("subprocess.run")
    def test_run_restore_postgres_success(self, mock_subproc, tmp_path):
        backup_file = tmp_path / "backup_AISchoolOS_test.dump"
        content = b"PG_CUSTOM_ARCHIVE"
        backup_file.write_bytes(content)

        checksum = hashlib.sha256(content).hexdigest()
        checksum_file = tmp_path / "backup_AISchoolOS_test.dump.sha256"
        checksum_file.write_text(f"{checksum}  backup_AISchoolOS_test.dump", encoding="utf-8")

        mock_subproc.return_value = MagicMock(returncode=0, stderr="")

        target_url = "postgresql://school_user:prod_pass@localhost:5432/school_erp"
        success = run_restore(
            backup_file_path=str(backup_file),
            target_database_url=target_url,
            verify_checksum=True,
            confirmed=True,
        )

        assert success is True
        call_args = mock_subproc.call_args
        cmd_executed = call_args[0][0]
        env_passed = call_args[1]["env"]
        assert "prod_pass" not in cmd_executed
        assert env_passed.get("PGPASSWORD") == "prod_pass"
        assert "--clean" in cmd_executed
        assert "--if-exists" in cmd_executed
        assert "--no-owner" in cmd_executed
