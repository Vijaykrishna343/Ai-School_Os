# NEXT PHASE DISCOVERY AFTER PHASE 12.8

**Document Status**: COMPLETED  
**Date**: September 5, 2026  
**Baseline Certified**: Phase 12.8 — CLOSED (AI Administrative Settings & Tenant Feature Flags)  
**Target Next Phase**: Phase 25 — Payment Gateway & Online Fee Collection Engine  

---

## 1. OFFICIAL NEXT PHASE IDENTIFICATION

```text
========================================
NEXT OFFICIAL PHASE
========================================

Phase:
Phase 25

Title:
Payment Gateway & Online Fee Collection Engine

Objective:
Enable self-service online fee payments for parents and students via integrated payment gateways (Razorpay / Stripe), including payment order creation, secure cryptographic webhook processing, automated fee assignment settlement, payment transaction logging, and digital receipt generation.

Source Document:
docs/product/feature-roadmap.md (and docs/product/feature-gap-analysis.md)

Requirements:
1. Payment Gateway Abstraction Layer (Razorpay & Stripe integration).
2. Tenant-scoped Payment Gateway Credential & Configuration Management.
3. Payment Order Creation API (`/api/v1/payments/orders`) for pending student fee assignments.
4. Cryptographically Signed Webhook Listener (`/api/v1/payments/webhook/{provider}`) with signature validation and replay protection.
5. Automated Settlement Engine linking completed gateway transactions to `FeePayment` and `StudentFeeAssignment` records.
6. Parent Portal UI Integration allowing self-service fee payments via Gateway Checkout modal.
7. Payment Audit & Reconciliation Dashboard for Finance Admins.

Dependencies:
- Phase 3 / Phase 4 Fee Management Engine (`StudentFeeAssignment`, `FeePayment`, `FeeStructure`, `CashSession`)
- RBAC Subsystem (`backend/app/common/authorization.py` — invariant: 0 diff)
- Tenant Context & Multi-tenancy (`current_user.school_id`)

Expected Backend:
- Gateway SDK wrapper (`app/services/payment_gateway_service.py`)
- Payment API Endpoints (`app/api/v1/endpoints/payments.py`)
- Webhook Signature Verifier (`app/core/security/payment_webhooks.py`)
- Pydantic Schemas (`app/schemas/payment.py`)

Expected Frontend:
- Parent Portal Fee Payment Modal (`src/components/finance/ParentFeePaymentModal.tsx`)
- Payment Gateway JS SDK Loader (`src/lib/payments/gatewayLoader.ts`)
- Finance Online Transactions & Reconciliation Table (`src/pages/finance/OnlineTransactionsPage.tsx`)

Expected Database:
- `payment_orders` (table for tracking order id, gateway reference, student assignment, tenant id, status, amount)
- `payment_transactions` (table for raw webhook events, transaction ids, payment method details, failure reasons)

Expected API:
- `POST /api/v1/payments/orders` (Create Checkout Order)
- `POST /api/v1/payments/verify` (Frontend Verification Endpoint)
- `POST /api/v1/payments/webhook/{provider}` (Public Webhook Receiver)
- `GET /api/v1/payments/transactions` (Tenant Transaction Audit Log)

Expected Tests:
- `backend/tests/test_payment_gateway.py` (Gateway Order Creation & Webhook Signature Unit Tests)
- `backend/tests/test_payment_tenant_isolation.py` (Cross-Tenant Webhook Isolation Tests)
- `frontend/src/components/finance/__tests__/ParentFeePaymentModal.test.tsx` (Component Rendering & Payment Trigger Tests)
========================================
```

---

## 2. SOURCE EVIDENCE & ROADMAP AUDIT

1. **`docs/product/feature-roadmap.md`**:
   - Explicitly lists **Phase 25: Payment Gateway & Online Fee Collection Engine** as the primary functional gap following the completion of Phase 24 and the Phase 12 AI Subsystem.
2. **`docs/product/feature-gap-analysis.md`**:
   - Identifies parent online payment self-service as the top remaining operational capability required for production school deployment.
3. **`PHASE_12_PRODUCT_COMPLETENESS_AUDIT.md`**:
   - Confirms that Phase 12 (12.1 through 12.8) is 100% complete and certified, establishing Phase 25 as the official successor phase.

---

## 3. CURRENT IMPLEMENTATION AUDIT

### ALREADY IMPLEMENTED
- **Fee Infrastructure**: `StudentFeeAssignment`, `FeePayment`, `FeeStructure`, `FeeDiscount`, and `CashSession` models (`backend/app/models/fee.py`).
- **Manual Fee Collection**: Cash/Cheque/Bank Reference fee collection API and UI (`backend/app/api/v1/endpoints/fees.py`).
- **Parent Portal Context**: Parent-child relationship models and parent API endpoints for viewing student fee status.
- **Tenant Isolation Framework**: Strict tenant scoping via `current_user.school_id` across all database queries.

### PARTIALLY IMPLEMENTED
- **Fee Ledgers & Receipts**: System generates receipt numbers and tracks balance dues, but lacks digital payment gateway transaction IDs and payment gateway fee breakdown fields.

### MISSING
- **Payment Gateway Abstraction**: Interfaces and implementations for Razorpay / Stripe SDKs.
- **Payment Order & Transaction ORM Models**: Database tables to track pre-payment checkout orders and async webhook payment transaction records.
- **Cryptographic Webhook Handlers**: Server-to-server endpoint for receiving external payment gateway webhook callbacks securely.
- **Parent Self-Service Checkout UI**: Modal and client-side integration to invoke Razorpay Checkout or Stripe Elements inside the Parent Portal.
- **Alembic Database Migration**: Required for new payment tracking tables (must be created only when Phase 25 implementation starts).

### OUT OF SCOPE
- Core RBAC authorization definitions in `backend/app/common/authorization.py` (MUST NOT BE MODIFIED — 0 diff invariant).
- Existing Phase 12 AI Assistant and Admin Subsystems.

---

## 4. ARCHITECTURE & REUSE STRATEGY

To maintain high architectural integrity and prevent duplication:
1. **Reuse `FeePayment` Model**: When an online payment is verified (via client callback or webhook), automatically construct a standard `FeePayment` record, reusing the existing fee ledger accounting and receipt sequence generator.
2. **Reuse Tenant Context**: Bind all payment orders explicitly to `school_id`. Webhook signature verification will fetch the tenant-specific webhook secret based on the order's `school_id`.
3. **Reuse Audit Logging**: Emit standard security and audit log events (`AuditLog`) upon payment order creation, webhook verification success, and payment failure events.

---

## 5. SECURITY & TENANT ISOLATION CONTROL MATRIX

1. **Authorization & RBAC**:
   - `backend/app/common/authorization.py` remains untouched (**0 diff**).
   - Server-side route permissions strictly enforced via existing `PermissionDependency`.
2. **Webhook Cryptographic Integrity**:
   - Webhooks will calculate HMAC-SHA256 signatures using the tenant's secret key and compare with incoming HTTP headers (`X-Razorpay-Signature` or `Stripe-Signature`).
   - Timing-safe string comparison (`hmac.compare_digest`) will be used to prevent timing attacks.
3. **Idempotency & Replay Protection**:
   - Incoming webhook transactions will be checked against `payment_transactions.gateway_transaction_id` before applying fee credits to prevent double-crediting.
4. **Tenant Scope Verification**:
   - Webhook processing will strictly confirm that the student fee assignment belongs to the tenant owning the payment gateway configuration.

---

## 6. REGRESSION BASELINE & IMPLEMENTATION READINESS

- **Backend Baseline**: 892 passed / 0 failed
- **Frontend Baseline**: 133 passed / 0 failed
- **TypeScript Errors**: 0
- **Production Build**: PASS
- **Alembic Migration Head**: `e5j4x6s7b8c9` (Single head)
- **`authorization.py` Diff**: 0

### READINESS VERDICT: **READY**

The project codebase is fully prepared and structurally ready to begin **Phase 25 — Payment Gateway & Online Fee Collection Engine**. No source code or database migrations were created or modified during this discovery step.
