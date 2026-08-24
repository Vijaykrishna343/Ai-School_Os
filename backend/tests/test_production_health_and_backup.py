import os
import shutil
import pytest
from fastapi.testclient import TestClient

from scripts.backup_db import run_backup
from scripts.restore_db import run_restore


def test_01_healthz_liveness_probe_returns_200_ok(client: TestClient):
    # Test root endpoint
    res1 = client.get("/healthz")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"

    # Test api/v1 endpoint
    res2 = client.get("/api/v1/healthz")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"


def test_02_readyz_readiness_probe_executes_db_ping(client: TestClient):
    # Test root endpoint
    res1 = client.get("/readyz")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ready"
    assert res1.json()["database"] == "connected"

    # Test api/v1 endpoint
    res2 = client.get("/api/v1/readyz")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ready"
    assert res2.json()["database"] == "ok"


def test_03_backup_script_execution(tmp_path):
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    assert os.path.exists(backup_file)
    assert "backup_AISchoolOS_" in backup_file


def test_04_restore_script_execution(tmp_path):
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    
    restore_success = run_restore(backup_file, target_database_url=f"sqlite:///{tmp_path}/restored_school.db")
    assert restore_success is True
    assert os.path.exists(f"{tmp_path}/restored_school.db")
