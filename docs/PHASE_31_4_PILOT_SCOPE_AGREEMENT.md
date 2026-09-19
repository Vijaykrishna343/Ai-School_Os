# PHASE 31.4 — PILOT MODULE SCOPE AGREEMENT

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.4 — Pilot Institution Acquisition & Pre-Onboarding Gate  
**Target Institution:** `[Pending Selection]`  

---

## 1. Modular Scope Definition & Classification

The pilot implementation scope is categorized into **Required Core Modules**, **Conditional Gateway Modules**, and **Optional Extended Modules**:

### A. Required Core Modules (Always Active)

| Module | Purpose | Status in Pilot |
| :--- | :--- | :---: |
| **Identity & Access** | Multi-tenant authentication, JWT sessions, fine-grained RBAC | **REQUIRED** |
| **Students** | Student directory, enrollment, section assignment, multi-child linking | **REQUIRED** |
| **Teachers** | Faculty profiles, department assignment, teacher cockpit | **REQUIRED** |
| **Parents** | Parent profiles, phone deduplication, ward relationships | **REQUIRED** |
| **Daily Attendance** | Roll-call attendance marking, status logs, duplicate conflict prevention | **REQUIRED** |
| **Homework** | Assignment creation, subject linking, section roster dispatch | **REQUIRED** |
| **Exams & Marks** | Exam schedules, subject marks entry, 10-point scale calculations | **REQUIRED** |
| **Report Cards** | Draft report card computation, leadership approval gate, publication | **REQUIRED** |
| **Fee Management** | Fee structures, student fee assignments, opening balance reconciliation | **REQUIRED** |
| **Parent Portal** | Mobile-responsive portal for attendance, marks, fees, and notifications | **REQUIRED** |
| **Executive Reports** | Administrative summary dashboards and CSV data export | **REQUIRED** |
| **Observability & DR** | Prometheus metrics, health checks, automated database backup CLI | **REQUIRED** |

### B. Conditional Gateway Modules (Requires Institutional Credentials)

| Module | Activation Requirement | Pilot Status |
| :--- | :--- | :---: |
| **Online Payments** | Razorpay / Stripe merchant sandbox or live credentials configured | `[ ] Included / [ ] Excluded` |
| **SMS Gateway** | SMS Provider API credentials configured in tenant settings | `[ ] Included / [ ] Excluded` |
| **WhatsApp Gateway** | Meta WhatsApp Business verify token and app secret configured | `[ ] Included / [ ] Excluded` |
| **Document Storage** | Persistent local or cloud volume storage configured | `[ ] Included / [ ] Excluded` |
| **AI Gateway** | Encrypted Gemini/OpenAI API key configured with strict SSRF controls | `[ ] Included / [ ] Excluded` |

### C. Optional Extended Modules (Upon Institutional Request)

| Module | Description | Pilot Status |
| :--- | :--- | :---: |
| **Transport** | Bus routes, stops, vehicle tracking, driver assignments | `[ ] Included / [ ] Excluded` |
| **Library** | Book catalog, barcode copy tracking, issue/return circulation | `[ ] Included / [ ] Excluded` |
| **Hostel** | Building/room/bed allocation, outpass approval, hostel fees | `[ ] Included / [ ] Excluded` |
| **Inventory & Assets**| Stock tracking, vendors, locations, physical asset register | `[ ] Included / [ ] Excluded` |
| **Admissions** | Inquiry tracking, admission cycles, applicant review pipeline | `[ ] Included / [ ] Excluded` |

---

## 2. Institutional Scope Approval Sign-Off

```text
Approved Scope Summary:
- Required Core Modules:         [X] Approved (All Core Modules)
- Conditional Modules Included:  _______________________________________________
- Optional Modules Included:     _______________________________________________

Institutional Pilot Owner Signature: __________________________________________
Date of Approval:                    __________________________________________
```
