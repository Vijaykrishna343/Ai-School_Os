# PHASE 31.2 — PILOT OPERATIONS RUNBOOK & DAILY RHYTHM

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Target Audience:** Technical Operators, System Administrators, Support Engineers  

---

## 1. Daily Operational Schedule & Rhythms

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 07:30 - 08:30  PRE-FLIGHT & START-OF-DAY HEALTH CHECK                      │
│                - Verify /health/live, /health/ready, and DB connectivity    │
│                - Confirm previous night's database backup SHA-256 sidecar   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 08:30 - 09:30  MORNING ATTENDANCE ROLL-CALL WINDOW                          │
│                - Class teachers mark and submit section attendance          │
│                - Monitor system for duplicate submission or latency spikes  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 09:30 - 15:30  REGULAR SCHOOL HOURS OPERATIONAL WINDOW                      │
│                - Homework creation, marks entry, fee counter collections   │
│                - Parent portal interactions and in-app notifications        │
│                - Support engineer logs any user issues in Issue Register    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 15:30 - 16:30  ACADEMIC & FINANCIAL DAILY RECONCILIATION                    │
│                - Review daily fee collection totals                         │
│                - Audit daily attendance completion rate                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 16:30 - 17:30  END-OF-DAY BACKUP & SYSTEM WRAP-UP                           │
│                - Execute automated / manual database backup via backup_db.py│
│                - Review P0/P1/P2/P3 issue register and plan follow-ups      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Issue Severity Escalation Protocols

| Severity | Definition | Target Response Time | Action & Escalation Path |
| :--- | :--- | :--- | :--- |
| **P0 (Catastrophic)** | System down, data loss, security breach, financial mismatch | `< 15 Minutes` | Immediate operational hold; contact Lead Engineer & Technical Operator. |
| **P1 (Pilot Blocker)** | Essential workflow failing (attendance, fees) with no workaround | `< 1 Hour` | Priority investigation; apply operational workaround or schedule hotfix. |
| **P2 (Major Defect)** | Important issue with viable operational workaround | `< 24 Hours` | Document in Issue Register; resolve in regular deployment cycle. |
| **P3 (Cosmetic/Polish)** | UI alignment, typo, minor usability feedback | Next Release | Log as product enhancement backlog item. |

### Placeholder Emergency Contacts:
- **Technical Lead / On-Call Operator:** `ops-support@schoolos.example.com`
- **School Pilot Administrator:** `pilot-admin@school.example.com`

---

## 3. Disaster Recovery & Emergency Procedures

1. **Daily Backup Execution:**
   ```bash
   python backend/scripts/backup_db.py --storage-dir ./storage/backups --retention-days 30
   ```
2. **Backup Verification:**
   Verify generated `.dump` file and sidecar `.sha256` exist and match calculated hash.
3. **Emergency Database Restoration:**
   ```bash
   python backend/scripts/restore_db.py --backup ./storage/backups/backup_<TIMESTAMP>.dump --confirm
   ```
