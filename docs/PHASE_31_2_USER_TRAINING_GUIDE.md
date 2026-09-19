# PHASE 31.2 — USER TRAINING GUIDE & WORKFLOW MANUAL

**Platform:** AI School OS 1.0.0  
**Phase:** Phase 31.2 — Pilot Onboarding Package & Institutional Readiness  
**Target Audience:** School Administrators, Teachers, Accounts Staff, Parents  

---

## 1. School Administrator Workflows

### Workflow AD-01: System Login & Dashboard Navigation
- **Goal:** Access the school administrative console and review high-level metrics.
- **Role:** School Admin / Principal.
- **Steps:**
  1. Open web browser to the designated application URL (e.g. `https://app.schoolos.example.com`).
  2. Enter assigned administrator email and password. Click **Sign In**.
  3. Review top metrics: Total Enrolled Students, Faculty Count, Daily Attendance Percentage, Fee Collection Status.
- **Expected Result:** Dashboard loads with live school metrics.
- **Common Error:** `401 Unauthorized` (Incorrect credentials).
- **Remediation:** Verify keyboard caps-lock; request password reset from Technical Operator.

### Workflow AD-02: Academic Structure & Section Management
- **Goal:** Verify and configure classes, sections, and subjects for the current academic year.
- **Role:** School Admin.
- **Steps:**
  1. Navigate to **Academics** in the sidebar.
  2. Select **Classes & Sections** tab to view active grades (e.g. Grade 10, Grade 8).
  3. Click **Add Section** or **Add Subject** if new classes require creation.
- **Expected Result:** Academic structure reflects school roster.

---

## 2. Teacher Workflows

### Workflow TC-01: Morning Roll-Call Attendance
- **Goal:** Record daily attendance for an assigned class section.
- **Role:** Class Teacher.
- **Steps:**
  1. Log in and navigate to **Attendance** (or click **Take Attendance** in Teacher Cockpit).
  2. Select Date (defaults to today), Class (e.g. Grade 10), and Section (e.g. 10-A).
  3. Review the student roster. All students default to `PRESENT`.
  4. Click individual toggle buttons to mark students `ABSENT` or `LATE`.
  5. Click **Submit Attendance**.
- **Expected Result:** Success notification banner appears. Daily attendance summary updates immediately.
- **Common Error:** `409 Conflict` (Attendance already submitted for this date).
- **Remediation:** Click **Edit Attendance** if updating an existing submission.

### Workflow TC-02: Homework Creation & Section Dispatch
- **Goal:** Create and publish a homework assignment to students and parents.
- **Role:** Subject Teacher.
- **Steps:**
  1. Navigate to **Homework** > Click **Create Assignment**.
  2. Select Class, Section, and Subject (e.g. Grade 10-A, Mathematics).
  3. Enter Title (e.g. *Chapter 4: Quadratic Equations Exercises*), Description, and Due Date.
  4. Click **Publish Assignment**.
- **Expected Result:** Assignment is published to section roster and appears on student/parent portals.

### Workflow TC-03: Examination Mark Entry
- **Goal:** Enter subject marks for an exam schedule.
- **Role:** Subject Teacher / Exam Coordinator.
- **Steps:**
  1. Navigate to **Exams** > Select active exam (e.g. *Term 1 Final Examination*).
  2. Select Subject and Class Section.
  3. Enter obtained marks for each student (ensuring `0 <= marks <= max_marks`).
  4. Click **Save Marks**.
- **Expected Result:** Marks saved and grade calculated automatically according to school grading scale.

---

## 3. Accounts & Fee Operator Workflows

### Workflow AC-01: Fee Collection & Receipt Generation
- **Goal:** Collect offline fee payment and issue formal receipt.
- **Role:** Accounts Staff / Fee Operator.
- **Steps:**
  1. Navigate to **Fees** > **Collect Fees**.
  2. Search for student by Admission Number or Name.
  3. Select fee items to be settled (e.g. *Term 1 Tuition Fee*).
  4. Select Payment Mode (`CASH`, `CHEQUE`, `BANK_TRANSFER`, `UPI`).
  5. Enter Reference Number (if applicable) and click **Record Payment**.
- **Expected Result:** Payment recorded in ledger, student outstanding balance decremented, and printable receipt generated.

---

## 4. Parent Self-Service Workflows

### Workflow PT-01: Parent Portal Access & Multi-Child Switching
- **Goal:** Log in, view child progress, and monitor attendance, homework, and fees.
- **Role:** Parent / Guardian.
- **Steps:**
  1. Open application URL and enter parent phone/email and password.
  2. If multiple children are enrolled (e.g. Aarav and Ananya), select the active child from the top selector.
  3. Review Child Attendance calendar, upcoming Homework due dates, and Published Report Cards.
  4. Navigate to **Fee Dues** to view current fee statement and receipts.
- **Expected Result:** Instant, transparent visibility into child academic and financial status.
- **Security Guarantee:** Parent cannot view records of children outside their authorized family relationship.
