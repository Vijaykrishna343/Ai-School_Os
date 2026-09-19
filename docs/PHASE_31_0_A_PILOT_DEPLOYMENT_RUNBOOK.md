# PHASE 31.0-A — PILOT DEPLOYMENT RUNBOOK

**Target Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.0-A Pilot Environment Deployment & Go-Live Readiness  
**Target Environment:** Staging & Production Pilot Instances  
**Status:** READY WITH ENVIRONMENT LIMITATIONS (Docker daemon requires host activation)  

---

## 1. Deployment Topology Overview

The AI School OS is designed as a secure, containerized multi-tenant ERP platform composed of 4 core services:

```
                          [ Client Traffic ]
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │     Nginx Web Server      │
                    │       (Port 80/443)       │
                    └─────────────┬─────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
     ┌────────────────────────┐      ┌────────────────────────┐
     │  React 18 SPA Frontend │      │   FastAPI Core Engine  │
     │  (Static Asset Server) │      │      (Port 8000)       │
     └────────────────────────┘      └────────────┬───────────┘
                                                  │
                                                  ▼
                                     ┌────────────────────────┐
                                     │  PostgreSQL 16 DB      │
                                     │      (Port 5432)       │
                                     └────────────────────────┘
```

---

## 2. Infrastructure & Prerequisites

| Component | Minimum Specification | Recommended Production |
| :--- | :--- | :--- |
| **CPU** | 2 vCPU | 4 vCPU |
| **Memory** | 4 GB RAM | 8 GB RAM |
| **Disk Space** | 20 GB SSD | 50 GB SSD (NVMe) |
| **Operating System** | Linux (Ubuntu 22.04 LTS) / Windows Server | Debian 12 / Ubuntu 24.04 LTS |
| **Container Engine** | Docker Engine 24.0+ / Compose v2.20+ | Docker Engine 26.0+ |
| **PostgreSQL** | PostgreSQL 16.x Alpine | PostgreSQL 16.3 on Managed RDS |

---

## 3. Environment Configuration & Secrets Management

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the required environment variables:
   - `ENVIRONMENT=production`
   - `DEBUG=False`
   - `DATABASE_URL=postgresql://school_user:<SECURE_PASSWORD>@db:5432/school_erp`
   - `SECRET_KEY=<CRYPTOGRAPHICALLY_SECURE_64_CHAR_HEX>`
   - `ALLOWED_ORIGINS=https://app.schoolos.example.com`
   - `DOCUMENT_STORAGE_PATH=/app/storage/documents`

---

## 4. Container Launch & Service Startup Sequence

The `docker-compose.yml` configuration enforces strict dependency ordering:

1. **Database Layer (`db`)**:
   - Initializes `postgres:16-alpine`.
   - Healthcheck verifies readiness via `pg_isready`.
2. **Schema Migration Service (`migration`)**:
   - Starts only after `db` reports `service_healthy`.
   - Executes `python -m alembic upgrade head` to ensure single head `z9a045bc11z5`.
   - Exits cleanly (`service_completed_successfully`).
3. **Application API Backend (`backend`)**:
   - Starts only after `migration` completes successfully and `db` is healthy.
   - Runs non-root (`appuser:appuser`).
   - Listens on internal port `8000`.
4. **Web Proxy & Frontend (`frontend`)**:
   - Starts after `backend` healthcheck reports `service_healthy`.
   - Proxies `/api/`, `/health`, and `/metrics` to backend while serving SPA static assets.

Command to launch:
```bash
docker compose up -d --build
```

---

## 5. Post-Deployment Verification Checklist

Once services are running, execute health verification:

1. **Liveness Check**:
   ```bash
   curl -f http://localhost/health/live
   # Expected: {"status": "ok", "app": "AI School OS"}
   ```
2. **Readiness Check**:
   ```bash
   curl -f http://localhost/health/ready
   # Expected: {"status": "ready", "database": "connected"}
   ```
3. **Metrics Verification**:
   ```bash
   curl -f http://localhost/metrics
   # Expected: Prometheus formatted metrics stream
   ```
4. **Alembic Revision Check**:
   ```bash
   docker compose exec backend python -m alembic current
   # Expected: z9a045bc11z5 (head)
   ```

---

## 6. Rollback & Disaster Recovery Procedures

If a deployment failure occurs:

1. **Container Rollback**:
   ```bash
   docker compose down
   docker compose up -d --build
   ```
2. **Database Restore**:
   - Follow the disaster recovery runbook in `docs/PHASE_31_0_A_BACKUP_RESTORE_DRILL.md`.
   - Execute `python backend/scripts/restore_db.py --backup <LATEST_BACKUP> --confirm`.
