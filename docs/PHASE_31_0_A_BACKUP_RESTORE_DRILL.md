# PHASE 31.0-A — BACKUP & DISASTER RECOVERY RESTORE DRILL

**Date:** 2026-09-19  
**Platform Version:** AI School OS 1.0.0  
**Phase:** Phase 31.0-A Pilot Environment Deployment & Go-Live Readiness  
**Target Tooling:** `backend/scripts/backup_db.py` & `backend/scripts/restore_db.py`  
**Test Suite:** `backend/tests/test_backup_restore_cli.py`  

---

## 1. Disaster Recovery Overview & Objectives

The AI School OS backup and disaster recovery subsystem ensures that in the event of hardware failure, database corruption, or unintended data loss, the entire multi-tenant database state can be restored reliably with zero corruption and cryptographic checksum verification.

---

## 2. Backup CLI Specification (`backup_db.py`)

- **Format:** PostgreSQL custom archive format (`-Fc`) using `pg_dump`.
- **Integrity Sidecar:** Calculates SHA-256 digest of the output archive and writes `<backup_file>.sha256`.
- **Credential Hygiene:** Cleanses credentials from database URLs in standard output and log messages (`school_user:***@host:port/db`).
- **Retention Management:** Automatically purges timestamped backups older than `--retention-days` (default: 30 days).

### Backup Execution Example:
```bash
python backend/scripts/backup_db.py --storage-dir ./storage/backups --retention-days 30
```

---

## 3. Restore CLI Specification (`restore_db.py`)

- **Confirmation Safety Guard:** Requires explicit `--confirm` flag; aborts with `PermissionError` if omitted.
- **Pre-Restore Checksum Validation:** Reads sidecar `.sha256` and computes hash of backup file. If hashes do not match, aborts immediately without modifying the database.
- **Database Engine Compatibility:** Supports PostgreSQL restore via `pg_restore` (`--clean --if-exists`) as well as SQLite development fallback.

### Restore Execution Example:
```bash
python backend/scripts/restore_db.py --backup ./storage/backups/backup_20260919_154409.dump --confirm
```

---

## 4. Automated Backup / Restore Verification Test Matrix

All 12 unit and integration test cases in `backend/tests/test_backup_restore_cli.py` were executed with **100% pass rate**:

| Test Case | Objective | Result |
| :--- | :--- | :--- |
| `test_sanitize_database_url` | Verify password masking in logs | **PASSED** |
| `test_parse_postgres_url` | Verify URL parameter extraction | **PASSED** |
| `test_calculate_sha256` | Verify accurate SHA-256 computation | **PASSED** |
| `test_run_backup_sqlite` | Verify SQLite backup & sidecar file creation | **PASSED** |
| `test_run_backup_missing_db_url` | Verify fail-fast when DATABASE_URL missing | **PASSED** |
| `test_run_backup_postgres_success` | Verify pg_dump execution & manifest | **PASSED** |
| `test_run_backup_postgres_failure` | Verify error propagation on pg_dump error | **PASSED** |
| `test_run_restore_blocks_unconfirmed` | Verify safety block when `--confirm` omitted | **PASSED** |
| `test_run_restore_missing_file` | Verify error when backup file missing | **PASSED** |
| `test_run_restore_checksum_mismatch` | Verify fail-closed when checksum altered | **PASSED** |
| `test_run_restore_sqlite_success` | Verify SQLite restore execution | **PASSED** |
| `test_run_restore_postgres_success` | Verify pg_restore execution & clean restore | **PASSED** |

---

## 5. Live Environment Execution & Classification

- **Backup CLI Execution:** **VERIFIED** — Executed successfully via `scripts/test_pilot_e2e_field_validation.py` Step 10, generating valid PostgreSQL dump with SHA-256 integrity manifest in `storage/backups/`.
- **Negative Checksum Test:** **VERIFIED** — Corrupted checksum sidecar triggers immediate exception and aborts restore.
- **Docker Containerized DB Destruction & Live Re-creation:** **ENVIRONMENT-LIMITED** — Docker daemon unavailable on current host; execution validated on local PostgreSQL instance.
