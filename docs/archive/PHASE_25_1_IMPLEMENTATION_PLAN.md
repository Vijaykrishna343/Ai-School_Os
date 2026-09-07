# PHASE 25.1 — IMPLEMENTATION PLAN

## GOAL
Establish the secure, multi-tenant persistence foundation for **Phase 25 — Payment Gateway & Online Fee Collection Engine**. This phase focuses exclusively on creating payment domain enums, ORM database models (`PaymentOrder`, `PaymentTransaction`), idempotency constraints, indexes, relationships, and the associated Alembic database migration.

> [!IMPORTANT]
> **Scope Scoping**: No payment gateway API endpoints, SDK integrations (Razorpay/Stripe), webhook listeners, or payment settlement logic will be implemented in Phase 25.1. Core authorization (`backend/app/common/authorization.py`) MUST remain at **0 diff**.

---

## PROPOSED CHANGES

### 1. Payment Domain Enums (`backend/app/common/enums/payment.py`)
#### [NEW] [payment.py](file:///c:/Projects/school-erp/backend/app/common/enums/payment.py)
Define native-compatible string enums:
- `PaymentProvider`: `RAZORPAY`, `STRIPE`, `OTHER`
- `PaymentOrderStatus`: `CREATED`, `PENDING`, `PAID`, `FAILED`, `CANCELLED`, `EXPIRED`
- `PaymentTransactionStatus`: `SUCCESS`, `FAILED`, `PENDING`, `REFUNDED`

---

### 2. Payment Models Package (`backend/app/models/payment/`)
#### [NEW] [__init__.py](file:///c:/Projects/school-erp/backend/app/models/payment/__init__.py)
#### [NEW] [payment_order.py](file:///c:/Projects/school-erp/backend/app/models/payment/payment_order.py)
- ORM model `PaymentOrder` inheriting from `CommonModel` (UUID `id`, `created_at`, `updated_at`, `is_deleted`).
- Foreign Keys: `school_id` (`schools.id`), `student_fee_assignment_id` (`student_fee_assignments.id`).
- Fields: `provider`, `gateway_order_id`, `amount` (`Numeric(12, 2)`), `currency` (default `"INR"`), `status`, `expires_at`, `extra_metadata` (`JSON`).
- Constraints: `CheckConstraint("amount > 0")`, Unique constraint on `(provider, gateway_order_id)`.
- Indexes: `school_id`, `student_fee_assignment_id`, `status`, `(school_id, status)`, `(school_id, created_at)`.

#### [NEW] [payment_transaction.py](file:///c:/Projects/school-erp/backend/app/models/payment/payment_transaction.py)
- ORM model `PaymentTransaction` inheriting from `CommonModel`.
- Foreign Keys: `school_id` (`schools.id`), `payment_order_id` (`payment_orders.id`).
- Fields: `provider`, `gateway_transaction_id`, `gateway_event_id`, `status`, `amount` (`Numeric(12, 2)`), `currency`, `payment_method`, `failure_reason`, `event_timestamp`, `raw_response` (`JSON`).
- Idempotency Constraint: Unique Index `uq_payment_transaction_provider_txn` on `(provider, gateway_transaction_id)` with `is_deleted = false/0`.
- Indexes: `school_id`, `payment_order_id`, `status`, `(school_id, created_at)`.

#### [MODIFY] [student_fee_assignment.py](file:///c:/Projects/school-erp/backend/app/models/fees/student_fee_assignment.py)
- Add relationship `payment_orders: Mapped[list["PaymentOrder"]] = orm_relationship(back_populates="assignment", cascade="all, delete-orphan")`.

#### [MODIFY] [__init__.py](file:///c:/Projects/school-erp/backend/app/models/__init__.py)
- Export `PaymentOrder`, `PaymentTransaction`, `PaymentProvider`, `PaymentOrderStatus`, `PaymentTransactionStatus` to enable Alembic model discovery.

---

### 3. Alembic Database Migration (`backend/alembic/versions/`)
#### [NEW] Migration Revision
- Create `payment_orders` table.
- Create `payment_transactions` table.
- Maintain single Alembic head from `e5j4x6s7b8c9`.

---

### 4. Comprehensive Foundation Tests (`backend/tests/test_payment_models.py`)
#### [NEW] [test_payment_models.py](file:///c:/Projects/school-erp/backend/tests/test_payment_models.py)
- Test 1: `PaymentOrder` creation and default field validation.
- Test 2: `PaymentTransaction` creation and order association.
- Test 3: Foreign key relationships (`PaymentOrder` -> `StudentFeeAssignment`, `PaymentTransaction` -> `PaymentOrder`).
- Test 4: Multi-tenant isolation verification (query filtering on `school_id`).
- Test 5: Idempotency & Unique constraint enforcement (`gateway_transaction_id` per provider).
- Test 6: Monetary precision check (`Numeric(12, 2)` exact decimal storage, no float rounding).
- Test 7: Valid state transitions (state machine acceptance/rejection).

---

## VERIFICATION PLAN

### Automated Tests
1. Model Unit & Idempotency Tests:
   `.\venv\Scripts\python.exe -m pytest backend/tests/test_payment_models.py`
2. Complete Backend Suite:
   `.\venv\Scripts\python.exe -m pytest -q` (Baseline: 892 passed)
3. Frontend Test Suite:
   `npm run test -- --run` (Baseline: 133 passed)
4. TypeScript Check:
   `npx tsc --noEmit` (Baseline: 0 errors)
5. Production Build:
   `npm run build`
6. Single Alembic Head Verification:
   `.\venv\Scripts\python.exe -m alembic heads`
7. Authorization Invariant Check:
   `git diff -- backend/app/common/authorization.py` (Expected: 0 diff)

---

## USER REVIEW REQUIRED

> [!NOTE]
> Database tables `payment_orders` and `payment_transactions` will be added to the schema. No existing tables are modified except adding relationship back-populators. `authorization.py` remains strictly untouched.
