# AI School OS — Backend Service

Backend REST API for **AI School OS**, a modern multi-tenant School ERP System built with FastAPI, SQLAlchemy 2.0, Alembic, and PostgreSQL.

---

## Technical Stack

- **Framework**: FastAPI (Python 3.14+)
- **ORM & Database**: SQLAlchemy 2.0 (PostgreSQL / SQLite for testing)
- **Migrations**: Alembic
- **Authentication & Security**: PyJWT (HS256 access and refresh tokens), Passlib (Bcrypt)
- **Configuration & Validation**: Pydantic v2 & Pydantic Settings

---

## Key Architecture & Hardening Features

- **Multi-Tenant Security**: Data access is strictly scoped per school (`school_id`). Soft-deleted user accounts are rejected immediately upon token verification.
- **Partial Unique Indexes**: Entity names (classes, sections, academic years, roll numbers, TCs) enforce partial unique indexes (`WHERE is_deleted = FALSE`), allowing entity re-creation after soft-deletion.
- **Academic Progression Engine**: Supports prospective plan generation, plan SHA-256 hash verification, header-based idempotency locking, and atomic rollover transactions.
- **Production Configuration Validation**: In production mode (`ENVIRONMENT=production`), system startup fails fast if `DEBUG=True` or default placeholder secrets are used.

---

## Local Development & Setup

### 1. Prerequisites
- Python 3.14+
- Virtual environment (`venv`)

### 2. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```

### 3. Database Migrations
Run database migrations using Alembic:
```bash
alembic upgrade head
```

### 4. Running Dev Server
Start the FastAPI development server:
```bash
uvicorn app.main:app --reload
```

---

## Running the Test Suite

Execute the complete pytest suite:
```bash
python -m pytest -v
```

Execute focused hardening tests:
```bash
python -m pytest tests/test_db_hardening.py tests/test_legacy_promotion_hardening.py tests/test_production_config.py -v
```
