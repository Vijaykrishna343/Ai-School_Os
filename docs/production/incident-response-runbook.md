# AI School OS — Production Incident Response & Operational Runbook

**Platform:** AI School OS / School ERP  
**Version:** 1.0.0  
**Target Environment:** Production  
**Scope:** SRE, DevOps, and Platform Engineering Operational Procedures  

---

## 1. Incident Severity Classification Model

| Severity | Definition | Target Response (MTTD/MTTA) | Target Mitigation (MTTR) | Escalation Path |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Total platform outage, database failure, active security breach, or total data corruption. | < 5 minutes | < 30 minutes | Lead SRE + Engineering Lead + Security Officer |
| **SEV-2 (Major)** | Core functional degradation (e.g., login failure, payment webhook outage, Redis failure causing 503 on rate limits). | < 15 minutes | < 2 hours | Primary On-Call SRE + Backend Lead |
| **SEV-3 (Minor)** | Non-blocking functional issues (e.g., reporting generation delay, non-critical background task retry, minor UI glitch). | < 1 hour | < 1 business day | On-Call Engineer |

---

## 2. Standard Diagnostic & Observability Tooling

### Health & Readiness Probes
```bash
# 1. Process Liveness Probe (Does not touch database)
curl -i http://localhost:8000/health/live

# 2. Database Connectivity Readiness Probe (Executes SELECT 1)
curl -i http://localhost:8000/readyz
```

### Metrics & Correlation Logs
```bash
# Query Prometheus Metrics (Requires METRICS_AUTH_TOKEN)
curl -H "Authorization: Bearer $METRICS_AUTH_TOKEN" http://localhost:8000/metrics

# Trace Request Logs via Correlation ID
# Output format: %(asctime)s | %(levelname)-8s | [cid:%(correlation_id)s] | %(name)s | %(message)s
docker compose logs backend | grep "[cid:TARGET_CORRELATION_ID]"
```

---

## 3. Incident Response Playbooks

### Playbook 1 — Application Outage (HTTP 502 / 503 / Backend Unresponsive)
* **Symptoms:** Nginx returns `502 Bad Gateway`; `/health/live` times out; container exited.
* **Immediate Checks:**
  1. Inspect container process state: `docker compose ps`
  2. Inspect backend error logs: `docker compose logs --tail=100 backend`
* **Resolution Steps:**
  1. Check for out-of-memory (OOM) or unhandled exceptions.
  2. Restart backend container: `docker compose restart backend`
  3. Verify liveness: `curl -f http://localhost:8000/health/live`
* **Rollback Action:** If deployment caused failure, rollback to previous image tag: `docker compose up -d --no-deps backend`.

---

### Playbook 2 — Database Outage & Readiness Failure
* **Symptoms:** `/readyz` returns `HTTP 503 {"status": "not_ready", "database": "disconnected"}`.
* **Immediate Checks:**
  1. Inspect PostgreSQL container health: `docker compose ps db`
  2. Check database logs: `docker compose logs --tail=100 db`
  3. Test direct container socket: `docker compose exec db pg_isready -U school_user -d school_erp`
* **Resolution Steps:**
  1. If disk full, expand storage volume (`pgdata`).
  2. If connection pool exhausted, restart db or increase PostgreSQL connection limits.
  3. If database crashed, restart: `docker compose restart db`.
* **Data-Safety Warning:** Never delete or wipe `school_erp_pgdata` volume during incident triage.

---

### Playbook 3 — Redis Outage (Rate Limiter Fail-Closed in Production)
* **Symptoms:** Login / auth endpoints return `HTTP 503 Service Unavailable` due to Phase G fail-closed rate-limiter policy.
* **Immediate Checks:**
  1. Check Redis health: `docker compose exec redis redis-cli ping`
  2. Inspect Redis logs: `docker compose logs --tail=100 redis`
* **Resolution Steps:**
  1. Restart Redis container: `docker compose restart redis`
  2. Verify ping: `redis-cli ping` returns `PONG`.
  3. Verify rate-limiter clears and allows login requests.

---

### Playbook 4 — Failed Database Migration
* **Symptoms:** `migration` container exited with non-zero code; `backend` container refuses to start due to `service_completed_successfully` dependency block.
* **Immediate Checks:**
  1. Inspect migration logs: `docker compose logs migration`
  2. Check current Alembic head: `python -m alembic current`
* **Resolution Steps:**
  1. Fix the faulty migration script or resolve conflicting constraints.
  2. If schema is corrupted, restore the pre-deployment database backup (`backup_db.py`).
  3. Re-run migration: `docker compose up migration`.

---

### Playbook 5 — Authentication Outage & Token Revocation
* **Symptoms:** Valid users rejected with 401; unexpected token validation errors.
* **Immediate Checks:**
  1. Check `SECRET_KEY` configuration consistency across instances.
  2. Check server clock synchronization (NTP drift causes premature JWT expiration).
  3. Inspect auth logs: `docker compose logs backend | grep "Authentication"`
* **Emergency Revocation:** If a token leak is suspected, rotate `SECRET_KEY` in environment secrets and restart backend (invalidates all active JWT sessions instantly).

---

### Playbook 6 — Payment & Webhook Signature Verification Failures
* **Symptoms:** Payments completed on gateway (Razorpay / Stripe) but status remains `PENDING` in School ERP.
* **Immediate Checks:**
  1. Verify webhook secret in config: `RAZORPAY_WEBHOOK_SECRET` / `STRIPE_WEBHOOK_SECRET`.
  2. Check Nginx raw body forwarding (`proxy_buffering off`, `proxy_pass_request_body on`).
  3. Inspect webhook logs: `docker compose logs backend | grep "webhook"`
* **Resolution Steps:**
  1. Correct mismatched webhook secret in tenant settings or environment.
  2. Replay failed webhooks from payment gateway dashboard.

---

### Playbook 7 — Backup Subsystem Failure
* **Symptoms:** Scheduled backup did not produce `.dump` / `.sha256`; disk full error.
* **Immediate Checks:**
  1. Check destination storage space: `df -h`
  2. Inspect backup logs: `docker compose logs ...` or scheduler output.
* **Manual Execution & Verification:**
  ```bash
  python backend/scripts/backup_db.py --storage-dir /app/storage/backups --retention-days 30
  ```
  Verify output file and non-zero byte size with matching `.sha256` sidecar.

---

### Playbook 8 — Suspected Security Incident / Breach Containment
* **Symptoms:** Suspicious admin activity, abnormal rate of failed logins, unauthorized data access.
* **Containment Protocol:**
  1. **Isolate Traffic:** Place Nginx in maintenance mode or restrict ingress to administrative IP allowlist.
  2. **Invalidate Sessions:** Rotate `SECRET_KEY` and flush Redis session store (`redis-cli flushall`).
  3. **Preserve Forensic Logs:** Capture all container logs and correlation IDs to immutable storage.
  4. **Audit Tenant Access:** Verify multi-tenant isolation filters in `backend/app/common/authorization.py`.

---

### Playbook 9 — Data Corruption Disaster Recovery Restore
* **Symptoms:** Critical table deletion, unrecoverable data corruption.
* **Restore Protocol:**
  1. Stop application traffic: `docker compose stop backend frontend`
  2. Identify latest verified backup in storage:
     ```bash
     ls -la /app/storage/backups/
     ```
  3. Execute safe restore with SHA-256 verification and explicit confirmation:
     ```bash
     python backend/scripts/restore_db.py /app/storage/backups/backup_AISchoolOS_YYYYMMDD_HHMMSS.dump --confirm
     ```
  4. Verify table row counts and schema integrity (`SELECT 1`).
  5. Restart backend and verify readiness (`/readyz`).
  6. Resume traffic.

---

### Playbook 10 — Application Version Rollback
* **Rollback Protocol:**
  1. Switch container image tag in `docker-compose.yml` or deployment pipeline to previous stable release tag.
  2. Run `docker compose up -d backend frontend`.
  3. Verify post-rollback smoke tests (`/health/live`, `/readyz`, login flow).
  4. Document incident timeline and root cause in Post-Mortem.

---

## 4. Post-Incident Review Protocol

For every **SEV-1** or **SEV-2** incident:
1. Conduct blameless post-mortem within 48 hours.
2. Document:
   - Root Cause Analysis (5 Whys)
   - Timeline of Detection, Escalation, Mitigation, and Resolution
   - Preventive Action Items & Automated Alert Adjustments
