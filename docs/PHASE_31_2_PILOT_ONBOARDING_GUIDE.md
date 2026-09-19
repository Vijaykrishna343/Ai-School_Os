# PHASE 31.2 — PILOT ONBOARDING GUIDE & INSTITUTIONAL HANDBOOK

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Target Audience:** School Leadership, Technical Operators, System Administrators  
**Status:** PILOT ONBOARDING PACKAGE READY (Awaiting Institutional Selection)  

---

## 1. Introduction & Pilot Purpose

The AI School OS is a multi-tenant school enterprise resource planning (ERP) platform designed for comprehensive academic, operational, and financial administration.

The purpose of the controlled pilot is to:
1. Validate system usability and reliability with authorized school users under real-world operating workflows.
2. Confirm seamless data migration and reconciliation from legacy records.
3. Establish operational rhythms (daily attendance, homework dispatch, exam grading, fee receipts, parent communication) with zero business disruption.

---

## 2. Institutional Privacy & Data Security Principles

> [!IMPORTANT]
> **Strict Data Privacy Policy**: Personal Identifiable Information (PII) of students, parents, and faculty must NEVER be shared through unsecured channels, public repositories, or unencrypted emails.

* **Authorized Transmission:** Data files for bulk onboarding must be provided directly to the authorized Technical Operator via secure encrypted storage or directly uploaded through the authenticated web console.
* **No Plaintext Secrets:** Passwords and credentials must never appear in CSV migration templates. Passwords are generated securely with salted Argon2id/bcrypt hashes upon initial user invitation.
* **Dry-Run Savepoint Isolation:** All data migration activities support a zero-mutation preview (`POST /api/v1/import/{entity}/preview`), allowing school administrators to verify field mappings and data integrity before committing any changes.

---

## 3. Pilot Scope & Supported Modules

| Module | Pilot Scope | Status | Description |
| :--- | :--- | :--- | :--- |
| **Identity & Access** | Core / Mandatory | Required | Tenant-isolated user authentication, RBAC, session management |
| **Student Management** | Core / Mandatory | Required | Student profiles, class/section enrollment, family relationships |
| **Staff & Teachers** | Core / Mandatory | Required | Faculty profiles, department linking, teacher assignments |
| **Daily Attendance** | Core / Mandatory | Required | Morning/period attendance marking, present/absent/late tracking |
| **Homework Dispatch** | Core / Mandatory | Required | Homework creation, file attachments, section-wide publishing |
| **Exams & Grading** | Core / Mandatory | Required | Exam scheduling, mark entry, 10-point scale grade calculations |
| **Report Cards** | Core / Mandatory | Required | Draft report card computation, leadership approval, parent release |
| **Fee Management** | Core / Mandatory | Required | Fee structure definition, student fee assignments, opening balances |
| **Online Payments** | Extended / Conditional | Conditional | Razorpay / Stripe gateway integration (requires merchant setup) |
| **Notifications** | Extended / Conditional | Conditional | In-app notification center; SMS / WhatsApp (requires gateway setup) |
| **Parent Portal** | Core / Mandatory | Required | Multi-child ward dashboard, attendance, fees, report card access |
| **Teacher Cockpit** | Core / Mandatory | Required | Teacher daily dashboard, timetable, assigned rosters |
| **Executive Reports** | Core / Mandatory | Required | Administrative analytics dashboards and CSV data export |
| **Transport / Hostel / Library** | Extended / Optional | Optional | Optional specialized modules enabled upon institutional request |

---

## 4. Phased Pilot Onboarding Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. INSTITUTIONAL SELECTION & PILOT AGREEMENT                                │
│    - Formal pilot agreement and authorized institutional scope definition    │
│    - Designation of School Administrator, Pilot Owner, & Technical Operator  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. ENVIRONMENT INITIALIZATION & TENANT PROVISIONING                         │
│    - Provision dedicated school tenant and initial Academic Year            │
│    - Initialize class structures (Grades, Sections, Subjects)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. DATA PREPARATION & RECONCILIATION MIGRATION                              │
│    - Format legacy CSV files using official schema templates                 │
│    - Execute Dry-Run Previews (0 DB mutations) -> Operator Review           │
│    - Execute Two-Phase Transactional Commits -> Reconcile entity counts      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. USER ROLE ONBOARDING & TRAINING                                          │
│    - Generate authorized School Admin, Teacher, and Parent accounts         │
│    - Conduct role-specific training sessions using Training Guides           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. CONTROLLED FIELD VALIDATION & DAILY OPERATIONS                           │
│    - Execute daily operations according to Pilot Operations Runbook         │
│    - Log all observations and feedback in Pilot Issue Register               │
│    - Evaluate acceptance criteria against Pilot Acceptance Matrix           │
└─────────────────────────────────────────────────────────────────────────────┘
```
