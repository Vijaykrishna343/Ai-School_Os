# Engineering Standards

## 1. Naming Conventions

### Tables
- Use plural nouns.
- Example:
  - schools
  - branches
  - students

### Columns
- Use snake_case.
- Example:
  - created_at
  - updated_at
  - admission_number

### Foreign Keys
Use:

<entity>_id

Example:

school_id
branch_id
student_id

---

## 2. Primary Keys

- UUID for every table.
- Never expose sequential IDs.

---

## 3. Audit Fields

Every table contains:

- id
- created_at
- updated_at

---

## 4. Soft Delete Policy

Every table supports soft delete.

Fields:

- is_deleted
- deleted_at
- deleted_by_user_id

No record is permanently deleted through the application.

---

## 5. Status Policy

Status represents business state.

Examples:

School:
- ACTIVE
- INACTIVE

Student:
- ACTIVE
- PROMOTED
- TC
- COMPLETED

Branch:
- ACTIVE
- INACTIVE

Status is different from deletion.

---

## 6. Time Standard

- Store timestamps in UTC.
- Convert to local timezone only in the UI.

---

## 7. Database Migrations

- Every schema change uses Alembic.
- Never modify production tables manually.

---

## 8. SQLAlchemy Models

- Every model inherits from BaseModel.
- No duplicate audit fields.

---

## 9. Pydantic Schemas

Separate schemas for:
- Create
- Update
- Response

Never expose SQLAlchemy models directly.

---

## 10. API Standards

- RESTful endpoints.
- Proper HTTP status codes.
- Validation on every request.

---

## 11. Git Workflow

Every sprint:

- Working code
- Migration
- Documentation
- Commit

---

## 12. Documentations

Every feature includes:

- Database changes
- API endpoints
- Business rules
- Testing notes