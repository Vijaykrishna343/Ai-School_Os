# PHASE 31.2 — DATA ONBOARDING & MIGRATION CHECKLIST

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Target Audience:** Data Migration Engineers, School IT Administrators  

---

## 1. Data Ingestion Order & Entity Dependency Graph

To preserve relational integrity across multi-tenant foreign keys, data must be migrated strictly in the following sequence:

```
  1. Parents ─────────┐
                      ├──▶ 3. Students ────▶ 4. Fee Structures ────▶ 5. Outstanding Balances
  2. Teachers ────────┘        │
                               ▼
                        6. Historical Marks
```

---

## 2. Entity CSV Schema Specifications

### A. Stage 1 — Parents (`parents.csv`)
- **Required Columns:** `first_name`, `last_name`, `phone`
- **Optional Columns:** `email`, `relationship_type` (`FATHER`, `MOTHER`, `GUARDIAN`), `address_line1`, `city`, `district`, `state`, `country`, `postal_code`, `occupation`, `annual_income`
- **Validation Rules:** `phone` must be numeric (10 digits). Deduplication automatically matches existing parent records by phone.

### B. Stage 2 — Teachers (`teachers.csv`)
- **Required Columns:** `first_name`, `last_name`, `employee_id`
- **Optional Columns:** `email`, `phone`, `gender`, `qualification`, `joining_date`, `address_line1`, `city`, `district`, `state`, `country`, `postal_code`, `specialization`, `experience_years`
- **Validation Rules:** `employee_id` must be unique per school. If location fields are omitted, school defaults are applied.

### C. Stage 3 — Students (`students.csv`)
- **Required Columns:** `first_name`, `last_name`, `admission_number`, `class_name`, `section_name`
- **Optional Columns:** `date_of_birth`, `gender`, `roll_number`, `parent_phone`, `address_line1`, `city`, `district`, `state`, `country`, `postal_code`, `emergency_contact_phone`
- **Validation Rules:** `admission_number` must be unique within the school. `class_name` and `section_name` must match configured classes. `parent_phone` links student to existing parent record.

### D. Stage 4 — Fee Structures (`fee_structures.csv`)
- **Required Columns:** `fee_structure_name`, `class_name`, `item_name`, `item_amount`, `fee_category`
- **Optional Columns:** `frequency`, `due_date`, `is_mandatory`
- **Validation Rules:** `fee_category` must match `TUITION`, `TRANSPORT`, `HOSTEL`, `EXAM`, `LIBRARY`, `LAB`, or `OTHER`. `item_amount` must be non-negative Decimal.

### E. Stage 5 — Outstanding Balances (`outstanding_balances.csv`)
- **Required Columns:** `admission_number`, `fee_structure_name`, `balance_amount`
- **Optional Columns:** `due_date`, `remarks`
- **Validation Rules:** `balance_amount` must be greater than zero.
- **Ledger Invariant:** Migrating opening balances assigns starting debt balance without creating any fake `FeePayment` receipts.

### F. Stage 6 — Historical Marks (`historical_marks.csv`)
- **Required Columns:** `admission_number`, `subject_name`, `exam_name`, `marks_obtained`, `max_marks`
- **Optional Columns:** `passing_marks`, `teacher_remarks`, `academic_year`
- **Validation Rules:** `0 <= marks_obtained <= max_marks`. Resolves and upserts into `StudentExamResult`.

---

## 3. Two-Stage Execution & Dry-Run Guarantee

1. **Dry-Run Preview (`/api/v1/import/{entity}/preview`):**
   - Parses the uploaded CSV file.
   - Runs full schema and foreign-key validation inside a database rollback savepoint (`db.begin_nested()`).
   - Generates summary of valid rows, invalid rows, duplicates, and missing references.
   - **Guarantees zero persistent database mutations.**
2. **Transactional Commit (`/api/v1/import/{entity}/commit`):**
   - Commits valid records to the database within an atomic transaction.
   - If `atomic_mode=true` is enabled, rolls back all records if any single row encounters an error.

---

## 4. Data Reconciliation Protocol

Upon completing migration for each entity, the Technical Operator and School Administrator must complete and sign off on the reconciliation tally:

| Entity | Source Records | Preview Valid | Preview Rejected | Committed to DB | Mismatch (Delta) | Sign-Off |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Parents** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
| **Teachers** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
| **Students** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
| **Fee Structures** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
| **Outstanding Balances** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
| **Historical Marks** | `[ ]` | `[ ]` | `[ ]` | `[ ]` | `0` | `[ ] Approved` |
