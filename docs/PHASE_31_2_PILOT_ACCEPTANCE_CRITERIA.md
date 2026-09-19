# PHASE 31.2 — PILOT ACCEPTANCE CRITERIA & SUCCESS METRICS

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Evaluation Scope:** Formal Pilot Acceptance Sign-Off Matrix  

---

## 1. Mandatory Acceptance Criteria Checklist

To achieve successful completion of the controlled real-school pilot, all mandatory criteria must be satisfied:

| Requirement ID | Domain | Acceptance Criterion | Verification Method | Status |
| :--- | :--- | :--- | :--- | :---: |
| **AC-01** | **Identity** | Authorized pilot users (Admin, Teachers, Parents) can log in securely | Live User Sign-In | `[ ]` |
| **AC-02** | **RBAC** | Fine-grained role permissions enforced; unprivileged actions blocked | Negative Auth Test | `[ ]` |
| **AC-03** | **Tenant Isolation**| Cross-tenant data access strictly denied across all endpoints | Multi-Tenant Check | `[ ]` |
| **AC-04** | **Data Reconciliation**| 100% of approved legacy records (Students, Staff, Parents) imported with 0 delta | Data Audit Tally | `[ ]` |
| **AC-05** | **Attendance** | Daily attendance marked, stored, and viewable by class teachers and parents | Daily Operations | `[ ]` |
| **AC-06** | **Homework** | Homework assignments published by teachers and visible to students/parents | Academic Flow | `[ ]` |
| **AC-07** | **Marks & Exams** | Exam marks entered, grades calculated, and draft report cards kept isolated | Grading Flow | `[ ]` |
| **AC-08** | **Report Cards** | Report cards published upon leadership approval and released to parents | Leadership Sign-Off| `[ ]` |
| **AC-09** | **Fee Management** | Fee structures assigned, opening balances verified, payments recorded with zero fake receipts | Financial Audit | `[ ]` |
| **AC-10** | **Parent Portal** | Parents access ward data with strict multi-child relationship scoping | Parent Feedback | `[ ]` |
| **AC-11** | **Notifications** | In-app notifications delivered to recipient inboxes; preference rules enforced | Notification Log | `[ ]` |
| **AC-12** | **Reports & Export**| School administrators can view summary dashboards and export CSV reports | Export Audit | `[ ]` |
| **AC-13** | **Disaster Recovery**| Daily database backups execute successfully with valid SHA-256 sidecars | Backup Log | `[ ]` |
| **AC-14** | **System Stability** | Zero unresolved P0 (catastrophic) and zero unresolved P1 (pilot-blocking) issues | Issue Register | `[ ]` |

---

## 2. Pilot Tracking Metrics

During the pilot duration, the Technical Operator and School Administrator will track the following metrics:

```text
================================================================================
                       PILOT FIELD OPERATIONAL METRICS
================================================================================
Active Pilot Users:                  [ Count of Unique Active Users ]
Daily Attendance Submissions:        [ Number of Section Days Logged ]
Homework Assignments Published:      [ Total Assignments Created ]
Exam Results Processed:              [ Total Student Subject Marks Logged ]
Fee Payments Recorded:               [ Total Fee Transactions Settled ]
In-App Notifications Delivered:      [ Total Notifications Processed ]
Disaster Recovery Backups Taken:     [ Total Automated Backups Logged ]
Total Support Tickets / Issues:      [ Count of Issues Logged ]
  - P0 (Critical Catastrophic):      0 (Mandatory for Certification)
  - P1 (Pilot Blocker):              0 (Mandatory for Certification)
  - P2 (Operational Impediment):     [ Count of Accepted Issues ]
  - P3 (Usability / Documentation):  [ Count of Logged Improvements ]
================================================================================
```

---

## 3. Formal Pilot Sign-Off Declaration

The pilot is certified as successful when the School Administrator and Technical Lead execute the formal sign-off:

```text
================================================================================
                   INSTITUTIONAL PILOT COMPLETION SIGN-OFF
================================================================================
School Legal Name:                   ___________________________________________
School Administrator Signature:      ___________________________________________
Technical Lead Signature:            ___________________________________________
Date of Certification:               ___________________________________________
Pilot Verdict:                       [ ] PILOT FIELD VALIDATED
                                     [ ] PILOT FIELD VALIDATED WITH ACCEPTED P2/P3
================================================================================
```
