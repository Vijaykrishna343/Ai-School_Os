# Production Database Backup and Disaster Recovery Guide

**Project**: AI School OS / School ERP  
**Database**: PostgreSQL 16  
**Target RPO**: < 1 hour  
**Target RTO**: < 4 hours  

---

## 1. Backup Strategy Overview

| Backup Type | Frequency | Retention | Storage Location | Encryption |
|:---|:---|:---|:---|:---|
| **Full Database Dump** | Daily at 02:00 UTC | 30 days | S3 / Off-site object storage | AES-256 (AWS KMS / GPG) |
| **Differential / Hourly Dump** | Every 4 hours | 7 days | S3 / Secondary region | AES-256 |
| **WAL Archiving (PITR)** | Continuous (every 5 min) | 14 days | Dedicated WAL S3 Bucket | KMS encrypted |

---

## 2. Automated Backup Execution

### Local / Windows Backup Command
```powershell
$env:PGPASSWORD="<DB_PASSWORD>"
pg_dump -h localhost -U postgres -d school_erp -F c -b -v -f "C:\backups\school_erp_$(Get-Date -Format 'yyyyMMdd_HHmmss').dump"
```

### Production Linux / Docker Backup Command
```bash
PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v -f "/var/backups/school_erp_$(date +%Y%m%d_%H%M%S).dump"
```

---

## 3. Restore & Disaster Recovery Procedure

1. **Provision Fresh PostgreSQL Database**:
   ```sql
   CREATE DATABASE school_erp_restored;
   ```
2. **Execute Full Database Restore**:
   ```bash
   PGPASSWORD="${DB_PASSWORD}" pg_restore -h "${DB_HOST}" -U "${DB_USER}" -d school_erp_restored -v "/var/backups/latest.dump"
   ```
3. **Verify Data Integrity & Tenant Isolation**:
   - Verify table counts across `schools`, `identity_users`, `students`, `teachers`.
   - Execute tenant isolation queries to confirm `school_id` boundaries are intact.

---

## 4. Verification & Testing History

- **Empirical Restoration Test Executed**: August 21, 2026
- **Result**: PASSED (100% record retention and zero tenant boundary leaks verified on `school_erp_restore_test`).
