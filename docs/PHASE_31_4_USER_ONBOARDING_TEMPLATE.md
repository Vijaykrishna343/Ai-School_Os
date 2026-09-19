# PHASE 31.4 — USER ONBOARDING & ROLE PROVISIONING TEMPLATE

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.4 — Pilot Institution Acquisition & Pre-Onboarding Gate  
**Target Institution:** `[Pending Selection]`  

---

## 1. Authorized Pilot User Onboarding Register

*(To be populated by the designated School Administrator prior to user activation)*

| User Role | Required Users | Official Name | Official Email / Phone | Account Status | Training Status |
| :--- | :---: | :--- | :--- | :---: | :---: |
| **School Administrator** | 1 - 2 | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| **Principal / Vice Principal** | 1 | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| **Class Teachers** | 2 - 5 | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| **Accounts / Fee Operator** | 1 | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| **Pilot Parent Accounts** | 5 - 10 | `PENDING` | `PENDING` | `PENDING` | `PENDING` |
| **Pilot Student Accounts** | Optional | `PENDING` | `PENDING` | `PENDING` | `PENDING` |

---

## 2. Role Permission & Access Control Summary

- **School Administrator:** Full administrative rights (`school.update`, `user.create`, `user.manage`, `reports.view`, `settings.manage`).
- **Principal:** Executive oversight, academic configuration review, and report card publication sign-off.
- **Teacher:** Daily attendance marking (`attendance.create`), homework publication (`homework.create`), and mark entry (`marks.create`).
- **Accounts Operator:** Counter fee collection (`fees.collect`), receipt issuance, and fee statement reporting.
- **Parent:** Self-service portal access restricted strictly to their registered wards (`student.view`, `attendance.view`, `fees.view`, `report_card.view`, `notification.view`).
