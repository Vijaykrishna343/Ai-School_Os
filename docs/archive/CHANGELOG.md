# Changelog

All notable changes to the AI School OS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Phase 4C] - 2026-08-13

### Security Hardening (Phase 4C.1)
- **Fixed**: `SEC-01` — Reject soft-deleted users in `get_current_user` during JWT authentication.
- **Fixed**: `SEC-02` — Enforce authenticated user's `school_id` on target class and section lookups in student promotion workflows.

### Database Hardening (Phase 4C.2)
- **Added**: Migration `p4c2_db_hardening` creating partial unique indexes `WHERE is_deleted = FALSE` across `AcademicYear`, `SchoolClass`, `Section`, `Student`, `StudentEnrollmentHistory`, and `TransferCertificate`.
- **Added**: Composite performance indexes `ix_attendances_school_date` and `ix_fee_assignments_school_year_student`.
- **Changed**: Enabled re-creation of entity names/codes after soft-deletion without unique constraint conflicts.

### API & Legacy Promotion Hardening (Phase 4C.3)
- **Added**: Progression matrix rule validation inside `StudentPromotionService.promote_student`.
- **Changed**: Marked legacy ad-hoc promotion OpenAPI routes (`/promote`, `/retain`, `/promote/bulk`, `/retain/bulk`) as `deprecated=True`.

### Production Configuration Hardening (Phase 4C.4)
- **Added**: Pydantic model validator enforcing fail-fast validation when `ENVIRONMENT == "production"`.
- **Added**: Rejection of `DEBUG=True` and default/insecure secret keys in production.
- **Added**: Environment-configurable `ALLOWED_ORIGINS` setting for CORS.
- **Added**: `.env.example` file with placeholder values.

### Deprecation Cleanup (Phase 4C.5)
- **Changed**: Replaced deprecated `HTTP_422_UNPROCESSABLE_ENTITY` with `HTTP_422_UNPROCESSABLE_CONTENT` in `ValidationException`.

### Documentation Restoration (Phase 4C.7)
- **Restored**: `01_Project_Vision.md`, `02_Requirements.md`, `03_Architecture.md`, `05_API_Design.md`, `07_Development_Log.md`, `CHANGELOG.md`, and `backend/README.md`.
- **Updated**: `04_Database_Design.md`.
