# AI School OS — RBAC & Permission Model Architecture

## 1. Two-Tier Authorization Architecture

AI School OS enforces a two-tier authorization model:

### Level 1: Platform Level (Super Admin)
- **Role**: `Super Admin`
- **Scope**: Multi-tenant / Global platform operations.
- **Capabilities**: View/manage all schools, create/activate/suspend/block schools, view platform analytics, manage system-level roles and global permissions, inspect platform audit logs.

### Level 2: School Level (Tenant Scoped)
- **Scope**: Strictly bound to `current_user.school_id`.
- **System Roles**:
  1. `School Admin` (Administrative owner/operator of the specific school)
  2. `Principal` (School-wide operational & academic authority)
  3. `Vice Principal` (Operational & academic assistant)
  4. `Teacher` (Classroom & subject instruction authority)
  5. `Class Teacher` (Teacher with class-level administrative responsibilities)
  6. `Receptionist` (Front-office, admissions, parent/visitor registry)
  7. `Accountant` (Fees, billing, payments, financial ledger)
  8. `Parent` (Relationship-scoped to linked children)
  9. `Student` (Self-scoped to personal profile and results)
- **Custom School Roles**: School-specific roles (e.g., `Librarian`, `Transport Manager`) created by School Admin for their own tenant (`school_id = current_user.school_id`).

---

## 2. Authorization Evaluation Pipeline

```
REQUEST
  ↓
1. Authenticated JWT Access Token? (Reject expired, invalid, or refresh tokens)
  ↓
2. User Active & Non-Deleted? (is_active == True, is_deleted == False)
  ↓
3. School Active? (school.status permits access OR caller is Super Admin)
  ↓
4. Required Permission Granted? (Check non-deleted roles & non-deleted permissions)
  ↓
5. Tenant/School Scope Matching? (current_user.school_id == target_resource.school_id OR Super Admin)
  ↓
6. Resource Ownership / Relationship Scope? (Child-scoped for Parent, Self-scoped for Student, Section-scoped for Teacher)
  ↓
ALLOW ACCESS
```

---

## 3. Core Security Invariants

1. **No Privilege Escalation**: School-level administrators can NEVER assign `Super Admin` or platform-level permissions.
2. **System Role Protection**: System roles cannot be modified, deleted, or re-permissioned by school administrators.
3. **Global Permission Protection**: Permission definitions are managed strictly by Super Admin.
4. **Strict Tenant Boundaries**: Frontend-supplied `school_id` parameters are ignored for school users; `school_id` is derived authoritatively from `current_user.school_id`.
5. **Soft-Delete Exclusions**: Soft-deleted roles (`is_deleted=True`) or permissions (`is_deleted=True`) NEVER grant authorization.
6. **School Suspension Enforcement**: If a school status is `SUSPENDED` or `BLOCKED`, all school-scoped APIs return `403 Forbidden` for school users while remaining accessible to Super Admin.
7. **Resource-Level Isolation**:
   - Parent access is strictly scoped to linked children (`parent_id`).
   - Student access is strictly self-scoped (`student_id`).
   - Teacher access is responsibility/section-scoped.
