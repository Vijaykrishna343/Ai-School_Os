# PHASE 31.4 — SCHOOL DATA REQUEST TEMPLATE & PRIVACY SPECIFICATION

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.4 — Pilot Institution Acquisition & Pre-Onboarding Gate  
**Target Audience:** School Data Custodians, IT Administrators  

---

## 1. Data Minimization & Privacy Protection Rules

> [!WARNING]
> **Strict Prohibition on Sensitive Secrets**: Never include passwords, PINs, API keys, payment card details, bank account credentials, or government ID private keys in CSV migration templates.

### Data Minimization Guidelines:
- **Collect Only Required Attributes:** Do not provide unnecessary personal, medical, or family financial background data.
- **Secure File Transfer:** CSV templates must be provided directly through the authenticated `/import` web console or transferred via secure encrypted media.
- **Dry-Run Preview:** All files will be validated in a zero-mutation dry run prior to permanent database commit.

---

## 2. Entity Migration Specifications

### A. Parents Dataset (`parents.csv`)
- **Purpose:** Establish primary family contacts and emergency communication channels.
- **Required Columns:** `first_name`, `last_name`, `phone` (10-digit primary phone).
- **Optional Columns:** `email`, `relationship_type` (`FATHER`, `MOTHER`, `GUARDIAN`), `address_line1`, `city`, `district`, `state`, `postal_code`, `occupation`.
- **Validation Rule:** Primary phone number is used for automatic deduplication of multi-child families.

### B. Teachers Dataset (`teachers.csv`)
- **Purpose:** Onboard faculty and assign classroom rosters.
- **Required Columns:** `first_name`, `last_name`, `employee_id` (Unique per school).
- **Optional Columns:** `email`, `phone`, `gender`, `qualification`, `joining_date`, `address_line1`, `city`, `district`, `state`, `postal_code`, `specialization`.
- **Validation Rule:** Missing address fields default safely to school location defaults.

### C. Students Dataset (`students.csv`)
- **Purpose:** Enroll student cohort and link to academic classes and parents.
- **Required Columns:** `first_name`, `last_name`, `admission_number`, `class_name`, `section_name`.
- **Optional Columns:** `date_of_birth` (YYYY-MM-DD), `gender`, `roll_number`, `parent_phone`, `address_line1`, `city`, `postal_code`.
- **Validation Rule:** `admission_number` must be unique; `parent_phone` links student to parent record.

### D. Fee Structures Dataset (`fee_structures.csv`)
- **Purpose:** Establish academic fee heads (Tuition, Lab, Exam fees).
- **Required Columns:** `fee_structure_name`, `class_name`, `item_name`, `item_amount`, `fee_category` (`TUITION`, `LAB`, `EXAM`, `TRANSPORT`, `OTHER`).
- **Validation Rule:** `item_amount` must be a valid non-negative Decimal.

### E. Outstanding Balances Dataset (`outstanding_balances.csv`)
- **Purpose:** Carry forward prior-term opening balance arrears.
- **Required Columns:** `admission_number`, `fee_structure_name`, `balance_amount`.
- **Ledger Invariant:** Recorded strictly as starting balance debt; generates **zero fake `FeePayment` receipts**.

### F. Historical Marks Dataset (`historical_marks.csv`)
- **Purpose:** Ingest prior term examination results.
- **Required Columns:** `admission_number`, `subject_name`, `exam_name`, `marks_obtained`, `max_marks`.
- **Validation Rule:** `0 <= marks_obtained <= max_marks`.
