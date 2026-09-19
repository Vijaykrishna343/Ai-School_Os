# Phase 30.8 — Production Deployment & Operational Hardening Report

**Certification Date**: September 19, 2026  
**Status**: **CERTIFIED & PRODUCTION READY**  
**Phase Scope**: Resolution of **GAP-03 (PostgreSQL Backup & Recovery)**, **GAP-04 (Production Deployment Packaging)**, and **GAP-06 (Observability & Prometheus Metrics)**.

---

## 1. Executive Summary

Phase 30.8 provides turnkey production packaging, native PostgreSQL database backup and restoration tooling, Prometheus observability, and Nginx reverse proxy architecture with full payment webhook compatibility for the AI School OS.

All established invariants (tenant isolation, RBAC, payment HMAC verification, encrypted credentials, monotonic state transitions, financial decimal precision) remain 100% intact with **0 diff** on `backend/app/identity/security/authorization.py` and zero new database migrations (`z9a045bc11z5 (head)` preserved).

---

## 2. Backup & Recovery Architecture (GAP-03)

### 2.1 Native PostgreSQL Backup Tooling (`backend/scripts/backup_db.py`)
- **Engine**: Executes `pg_dump -Fc` (PostgreSQL Custom Archive Format) to produce compressed, reliable backups.
- **Credential Protection**:
  - Automatically parses database credentials from `DATABASE_URL` or `Settings`.
  - Sets `PGPASSWORD` strictly within the subprocess environment; never exposes passwords in CLI arguments, process tables, or log files.
  - Sanitizes logged database URLs (e.g. `postgresql://school_user:***@db:5432/school_erp`).
- **Checksum Sidecars**:
  - Calculates SHA-256 hash of the created archive and writes `{backup_file}.sha256` sidecar (`{hash}  {filename}`).
- **Retention Management**:
  - Automatically prunes expired backup files older than configurable `retention_days` (default: 30 days).
- **SQLite Support**:
  - Automatically falls back to safe file copy when running against SQLite databases.

### 2.2 Safe Disaster Recovery Restore (`backend/scripts/restore_db.py`)
- **Engine**: Executes `pg_restore --clean --if-exists --no-owner` for deterministic restoration without schema collision.
- **Safety Safeguard**:
  - Enforces explicit `--confirm` flag (or `confirmed=True`) to prevent accidental destruction/overwrite of live databases.
- **Checksum Verification**:
  - Validates archive integrity against the SHA-256 sidecar file before initiating restore; fails closed with error code 1 on checksum mismatch or missing sidecar.
- **Clean Error Handling**:
  - Captures `pg_restore` outputs and returns standard non-zero exit codes on failure.

---

## 3. Production Deployment & Nginx Architecture (GAP-04)

### 3.1 Architecture Overview

```text
       Internet / School LAN
                 ↓
      Nginx Frontend (Port 80)
      [frontend/nginx.conf]
        ↙                  ↘
  Static SPA Assets      FastAPI Backend (Port 8000)
    (React / Vite)         [Uvicorn ASGI]
                           ↙            ↘
              PostgreSQL 16 DB     Prometheus Scraper
              [school_erp_data]       [/metrics]
```

### 3.2 Nginx Configuration (`frontend/nginx.conf`)
- **SPA Routing**: Serves production build files from `/usr/share/nginx/html` with `try_files $uri $uri/ /index.html`.
- **API Reverse Proxy**: Routes `/api/` traffic to `http://backend:8000/api/`.
- **Payment Webhook Transparency (Crucial Security Invariant)**:
  - Configures `client_max_body_size 20M; proxy_pass_request_body on; proxy_pass_request_headers on; proxy_buffering off; proxy_request_buffering on;`
  - Guarantees byte-for-byte fidelity of raw HTTP request bodies for **Razorpay** and **Stripe** HMAC-SHA256 signature verification.
- **Security Headers**:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Asset Caching & Compression**: Gzip compression enabled for static JS/CSS with 30-day cache headers.

### 3.3 Containerization (`Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`)
- **`frontend/Dockerfile`**: Multi-stage Node 20 build -> Nginx Alpine runner with healthcheck probe.
- **`Dockerfile` (Backend)**: Multi-stage Python 3.14-slim build -> non-root `appuser` execution with `postgresql-client` installed.
- **`docker-compose.yml` Services**:
  1. `db`: PostgreSQL 16 Alpine with persistent volume `school_erp_pgdata` and healthcheck (`pg_isready`).
  2. `migration`: Init container that runs `python -m alembic upgrade head` and exits successfully before backend startup.
  3. `backend`: FastAPI app starting only after `db` is healthy and `migration` completes. Exposes internal port 8000 and mounts `school_erp_document_storage`.
  4. `frontend`: Nginx proxy and static asset server listening on port 80 (or `${PORT}`).

---

## 4. Observability & Prometheus Metrics (GAP-06)

### 4.1 Prometheus Collector (`backend/app/common/metrics.py`)
- **Endpoint**: `GET /metrics` returning `text/plain; version=0.0.4; charset=utf-8`.
- **Thread-Safe Metrics Registry**:
  - `school_erp_http_requests_total`: Counter by `method`, `endpoint`, `status`.
  - `school_erp_http_request_duration_seconds`: Histogram with latency buckets `[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]` by `method`, `endpoint`.
  - `school_erp_http_requests_in_progress`: Gauge tracking active concurrent requests.
  - `school_erp_database_connected`: Gauge indicating PostgreSQL database connectivity (1=healthy, 0=disconnected).
  - `school_erp_app_info`: Gauge with build `version` and `environment`.
- **Bounded Label Cardinality & PII Protection**:
  - `normalize_route_path()` replaces UUIDs (`/[0-9a-fA-F-]{36}`) and numeric IDs (`/\d+`) with `{id}`.
  - Strips query parameters to ensure metric labels never contain student IDs, parent IDs, tokens, or PII.

---

## 5. Operations & Disaster Recovery Guide

### 5.1 Performing a Database Backup
```bash
# Manual or cron execution
python backend/scripts/backup_db.py --storage-dir /var/backups/school_erp --retention-days 30
```
Output artifacts:
- `/var/backups/school_erp/backup_AISchoolOS_YYYYMMDD_HHMMSS.dump`
- `/var/backups/school_erp/backup_AISchoolOS_YYYYMMDD_HHMMSS.dump.sha256`

### 5.2 Performing a Disaster Recovery Restore
```bash
# Verify checksum and restore with explicit safety confirmation
python backend/scripts/restore_db.py /var/backups/school_erp/backup_AISchoolOS_20260919_120000.dump --confirm
```

---

## 6. Verification Results

| Verification Suite | Target / Command | Result | Duration |
| :--- | :--- | :--- | :--- |
| **Backup & Restore CLI Tests** | `pytest tests/test_backup_restore_cli.py` | **12 / 12 passed** | 0.39s |
| **Prometheus Metrics Tests** | `pytest tests/test_prometheus_metrics.py` | **3 / 3 passed** | 1.26s |
| **Production Health & Backup Tests** | `pytest tests/test_production_health_and_backup.py` | **4 / 4 passed** | 8.35s |
| **Payment Webhook Gateway Tests** | `pytest tests/test_payment_webhooks.py` | **14 / 14 passed** | 12.28s |
| **Full Backend Pytest Regression** | `pytest -q` (Whole Backend) | **1,270 / 1,270 passed, 7 warnings** | 5806.13s (1h 36m) |
| **Frontend Vitest Suite** | `npx vitest run` (30 test files) | **214 / 214 passed** | 37.05s |
| **Frontend TypeScript Check** | `npx tsc --noEmit` | **0 errors** | 4.10s |
| **Frontend Production Build** | `npm run build` | **Succeeded (`dist/`)** | 9.37s |
| **Docker Compose Validation** | `docker compose config` | **100% valid YAML syntax** | Instant |
| **Database Migrations** | `alembic heads` & `alembic current` | `z9a045bc11z5 (head)` | Single linear head |
| **Security Invariant** | `authorization.py` | **0 diff** | Verified |
| **Secret Scan** | Whole repository credential search | **0 real secrets** | Verified |

---

## 7. Changed Files Summary

- [`.gitignore`](file:///c:/Projects/school-erp/.gitignore): Added `storage/backups/`, `*.dump`, `*.dump.sha256`, `*.sql.sha256`.
- [`.env.example`](file:///c:/Projects/school-erp/.env.example): Updated with comprehensive production configuration template.
- [`Dockerfile`](file:///c:/Projects/school-erp/Dockerfile): Added `postgresql-client` to backend runner container.
- [`docker-compose.yml`](file:///c:/Projects/school-erp/docker-compose.yml): Added multi-container stack (`db`, `migration`, `backend`, `frontend`).
- [`backend/scripts/backup_db.py`](file:///c:/Projects/school-erp/backend/scripts/backup_db.py): Implemented native `pg_dump` with SHA-256 sidecars and credential sanitization.
- [`backend/scripts/restore_db.py`](file:///c:/Projects/school-erp/backend/scripts/restore_db.py): Implemented native `pg_restore` with safety `--confirm` and checksum validation.
- [`backend/app/common/metrics.py`](file:///c:/Projects/school-erp/backend/app/common/metrics.py): Implemented thread-safe Prometheus metrics collector with route normalization.
- [`backend/app/main.py`](file:///c:/Projects/school-erp/backend/app/main.py): Registered metrics middleware and exposed `GET /metrics`.
- [`backend/tests/test_backup_restore_cli.py`](file:///c:/Projects/school-erp/backend/tests/test_backup_restore_cli.py): Created 12 unit/integration tests for backup/restore.
- [`backend/tests/test_prometheus_metrics.py`](file:///c:/Projects/school-erp/backend/tests/test_prometheus_metrics.py): Created 3 tests for `/metrics` endpoint and exposition formatting.
- [`frontend/Dockerfile`](file:///c:/Projects/school-erp/frontend/Dockerfile): Created multi-stage Vite build and Nginx runner.
- [`frontend/nginx.conf`](file:///c:/Projects/school-erp/frontend/nginx.conf): Created Nginx SPA router, API proxy, and webhook body transparency config.
- [`docs/PHASE_30_8_PRODUCTION_OPERATIONAL_HARDENING.md`](file:///c:/Projects/school-erp/docs/PHASE_30_8_PRODUCTION_OPERATIONAL_HARDENING.md): Created phase certification document.
