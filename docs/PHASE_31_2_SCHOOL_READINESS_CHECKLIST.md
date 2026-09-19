# PHASE 31.2 — INSTITUTIONAL & SCHOOL READINESS CHECKLIST

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Target Audience:** School Leadership & Pilot Implementation Team  

---

## 1. Institutional Governance & Stakeholder Profile

To be completed by the prospective pilot institution:

- **School Legal Name:** `[To be populated upon pilot agreement]`
- **School Identifier / Code:** `[Unique alphanumeric code e.g. SCH-01]`
- **School Location & District:** `[City, State, Country]`
- **Primary School Administrator:** `[Name, Role, Official Email]`
- **Institutional Pilot Owner:** `[Name, Title, Official Contact]`
- **Designated Technical Operator:** `[Name, Title, Technical Email]`
- **Target Pilot Launch Date:** `[YYYY-MM-DD]`
- **Target Pilot Duration:** `[e.g. 14 Days / 30 Days]`
- **Participating Cohort Scope:** `[e.g. Grades 8 to 10 / Whole School]`

---

## 2. Infrastructure & Device Readiness

| Infrastructure Element | Specification Requirement | School Readiness State |
| :--- | :--- | :--- |
| **Internet Connectivity** | Minimum 10 Mbps broadband / 4G backup | `[ ] Confirmed` |
| **Client Web Browsers** | Chrome 110+, Edge 110+, Firefox 110+, Safari 16+ | `[ ] Confirmed` |
| **Administrator Workstations** | Desktop / Laptop with 1080p display | `[ ] Confirmed` |
| **Teacher Devices** | Laptops, Tablets, or Smartphones with modern browser | `[ ] Confirmed` |
| **Parent Devices** | Smartphones with iOS / Android web browser | `[ ] Confirmed` |
| **Local Hosting / Server** | Required only if running on-premise (Linux/Windows) | `[ ] Confirmed / Cloud Staging` |

---

## 3. Security, Access & Data Policies

- [ ] **Data Access Authorization:** Explicit institutional consent to provision pilot tenant and ingest authorized school records.
- [ ] **Role Assignment Matrix:** Approved list of authorized personnel for School Admin, Teacher, Accounts, and Parent accounts.
- [ ] **Password Policy:** All users briefed to use secure passwords (minimum 8 characters, mixed character types).
- [ ] **Incident Response Protocol:** Designated communication channel between School Administrator and Technical Operator for P0/P1 issue escalation.

---

## 4. Communication & Gateway Prerequisites (Optional)

- [ ] **SMS Gateway:** Provider API credentials (Twilio / Fast2SMS) configured in encrypted tenant settings (if SMS enabled).
- [ ] **WhatsApp Business API:** Meta verify token and app secrets configured (if WhatsApp enabled).
- [ ] **In-App Notification Center:** Always active by default (zero external credentials required).

---

## 5. Payment Gateway Prerequisites (Optional)

- [ ] **Merchant Account:** Razorpay or Stripe test/sandbox merchant account provisioned.
- [ ] **Key Configuration:** `Key ID`, `Key Secret`, and `Webhook Secret` configured securely via `/settings` (never shared via insecure documents).
- [ ] **Fee Settlement Policy:** Offline cash/cheque counter collection enabled alongside online payment options.
