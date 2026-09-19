# AI School OS — Enterprise Multi-Tenant School ERP Platform

[![CI Pipeline](https://github.com/Vijaykrishna343/Ai-School_Os/actions/workflows/ci.yml/badge.svg)](https://github.com/Vijaykrishna343/Ai-School_Os/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Vijaykrishna343/Ai-School_Os)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

---

## 1. Overview & Platform Purpose

**AI School OS** is a modern, enterprise-grade, multi-tenant School Management & Enterprise Resource Planning (ERP) platform. Built from the ground up to support single-school and multi-school networks, it unifies academic governance, student administration, faculty operations, financial fee collection, examination grading, parent communication, and operational logistics into an integrated, secure, and observable cloud system.

---

## 2. Core ERP Capabilities & Functional Modules

- **Multi-Tenancy & School Provisioning:** Complete tenant data isolation (`school_id`), school lifecycle management (`ACTIVE`, `SUSPENDED`, `BLOCKED`), tier-based quotas, and Platform Super Admin controls.
- **Identity, RBAC & ABAC:** Dual-token JWT authentication, inactive account rejection, rate limiting, fine-grained role permissions, and relationship-based access control (e.g. parent-to-ward scoping).
- **Student Information System (SIS):** Student enrollment dossiers, class/section allocation, roll numbers, document vaults, transfer certificates (TC), and progression history.
- **Parent Portal & Self-Service:** Multi-child ward switching, real-time attendance logs, homework feeds, published report cards, fee payment tracking, and in-app notifications.
- **Teacher Classroom Cockpit:** Daily roll-call attendance, homework authoring with attachments, timetable schedules, substitutions, mark entry, and staff leave management.
- **Academics & Timetable:** Academic years, terms, classes, sections, subjects CRUD with pagination, room/faculty clash detection, and class progression rules.
- **Examinations & Report Cards:** Multi-assessment setups, 10-point grade scales, `ROUND_HALF_UP` calculations, leadership publication approval gates, and draft isolation.
- **Fee Management & Finance:** Fee structures, student fee assignments, opening balance reconciliation, cash counter sessions, and printable tax receipts with strict `Decimal` monetary precision.
- **Online Payment Gateways:** Server-authoritative `PaymentOrder` lifecycle with Razorpay HMAC-SHA256 and Stripe webhook signature verification, timing-safe checks, and idempotent replay protection.
- **Specialized Operational Modules:**
  - **Admissions & Inquiries:** Applicant tracking and automated student enrollment conversion.
  - **Transport Management:** Fleet vehicles, driver logs, routes, stops, and student bus allocations.
  - **Library Circulation:** Book catalog, barcode copies, loans, fine accruals, and reservations.
  - **Inventory & Asset Register:** Stock movements, multi-location inventory, suppliers, and physical asset assignment tracking.
  - **Hostel Management:** Buildings, rooms, bed allocations, outpasses, and fee billing integration.
  - **Reception & Visitors:** Inquiries, visitor passes, and check-in/check-out auditing.
- **Multi-Channel Notification Center:** In-app notification inbox, user communication preferences, and provider abstractions for SMS & WhatsApp.
- **AI Gateway & Analytics:** Enterprise AI Gateway with strict SSRF & loopback IP protection, encrypted credential storage, student risk analytics, communication drafting, report card remarks, and timetable generation heuristics.
- **Legacy Data Migration (GAP-05):** 6-entity bulk CSV onboarding (Parents, Teachers, Students, Fee Structures, Outstanding Balances, Historical Marks) with dry-run savepoint zero-mutation guarantees and atomic rollback.
- **Disaster Recovery & Observability:** Automated backup CLI (`backup_db.py`) with SHA-256 integrity sidecars, safety-guarded restore CLI (`restore_db.py`), Prometheus `/metrics`, and `/health/live` / `/health/ready` probes.

---

## 3. Technology Stack

### Backend
- **Language & Framework:** Python 3.14 / FastAPI (Asynchronous ASGI)
- **Database ORM:** SQLAlchemy 2.0 / Alembic (Transactional DDL)
- **Database Engine:** PostgreSQL 16
- **Security & Crypto:** Argon2id / bcrypt, PyJWT, Cryptography (Fernet)
- **Testing:** pytest, pytest-cov, anyio

### Frontend
- **Language & Framework:** TypeScript 5 / React 18 / Vite 5
- **State & Server Cache:** TanStack Query (React Query)
- **Routing & Navigation:** React Router v6
- **Icons & UI Utilities:** Lucide React, Tailwind CSS / Vanilla CSS
- **Testing:** Vitest, Testing Library, jsdom

### Infrastructure & Deployment
- **Web Proxy:** Nginx (Reverse proxy with webhook raw-body transparency)
- **Containerization:** Docker / Docker Compose
- **Metrics & Observability:** Prometheus / OpenMetrics format

---

## 4. Repository Structure

```text
school-erp/
├── .github/
│   └── workflows/ci.yml         # GitHub Actions CI/CD Pipeline
├── backend/
│   ├── alembic/                 # Database migrations (Single head: z9a045bc11z5)
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API endpoints
│   │   ├── core/                # Configuration, database engine, security
│   │   ├── identity/            # Core authentication & authorization engine
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   └── services/            # Domain business logic & external gateways
│   ├── scripts/                 # Backup & restore disaster recovery tooling
│   └── tests/                   # 152 test files (1282 backend tests)
├── frontend/
│   ├── public/                  # Static assets & icons
│   ├── src/
│   │   ├── components/          # Reusable UI components & layouts
│   │   ├── pages/               # Application route views & workspaces
│   │   ├── services/api/        # Typed API client services
│   │   └── test/                # 30 Vitest test suites (214 frontend tests)
│   ├── nginx.conf               # Production Nginx reverse proxy configuration
│   └── Dockerfile               # Multi-stage production frontend Dockerfile
├── docs/                        # Architecture, runbooks, checklists & audit reports
├── scripts/                     # Pilot validation harnesses & utility scripts
├── docker-compose.yml           # Production & Staging multi-container orchestration
├── Dockerfile                   # Multi-stage production backend Dockerfile
└── .env.example                 # Production configuration template
```

---

## 5. Local Development Setup

### Prerequisites
- Python 3.11+ (Python 3.14 recommended)
- Node.js 20+ and npm 10+
- PostgreSQL 16 running on port `5432`

### 1. Backend Setup
```bash
# Navigate to backend and create virtual environment
cd backend
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env to set your PostgreSQL credentials and SECRET_KEY

# Run database migrations
python -m alembic upgrade head

# Start backend development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
# Open a new terminal in the frontend directory
cd frontend

# Install Node dependencies
npm ci

# Start frontend Vite development server
npm run dev
```

The application will be accessible at `http://localhost:5173` (Frontend) and `http://localhost:8000` (Backend API).

---

## 6. Automated Testing & Verification Suites

### Run Backend Regression Suite
```powershell
$env:PYTHONPATH="backend;."
backend\venv\Scripts\python.exe -m pytest backend/tests -q
```
*Baseline:* **1282 passed (100% pass rate)** across 152 test files.

### Run Frontend Unit & Integration Tests
```bash
cd frontend
npm test
```
*Baseline:* **214 passed (100% pass rate)** across 30 test files.

### Run TypeScript Verification & Production Build
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 7. Docker Production Deployment

To start the complete containerized stack (PostgreSQL, Schema Migration, FastAPI Backend, React Frontend/Nginx):

```bash
# Validate compose configuration
docker compose config

# Launch container stack
docker compose up -d --build
```

### Verify Service Health
- **Liveness Probe:** `curl http://localhost/health/live`
- **Readiness Probe:** `curl http://localhost/health/ready`
- **Prometheus Metrics:** `curl http://localhost/metrics`

---

## 8. Backup & Disaster Recovery CLI

### Create Timestamped Database Backup
```bash
python backend/scripts/backup_db.py --storage-dir ./storage/backups --retention-days 30
```
Generates a PostgreSQL custom format archive (`.dump`) and cryptographic SHA-256 checksum sidecar (`.sha256`).

### Restore Database from Backup
```bash
python backend/scripts/restore_db.py --backup ./storage/backups/backup_<TIMESTAMP>.dump --confirm
```
Enforces `--confirm` safety flag and validates SHA-256 integrity before executing restoration.

---

## 9. Security & Governance Invariants

- **Zero Diff Core Security Engine:** `backend/app/identity/security/authorization.py` is an immutable, hardened security guard.
- **Single Migration Head:** Alembic version history is strictly linear at head `z9a045bc11z5`.
- **Zero Real Data Commitment:** All fixtures and repository assets use synthetic test data. Real student/parent PII is strictly forbidden in version control.
- **Zero Fake Payment Records:** Legacy migration of opening balances creates starting debt allocations with zero fictitious `FeePayment` receipts.

---

## 10. Pilot Readiness Status

The AI School OS is certified as **ERP FEATURE COMPLETE: READY FOR REAL-SCHOOL PILOT**.
Complete operational runbooks, pre-onboarding checklists, data migration templates, and training guides are available in the [docs/](docs/) directory.
