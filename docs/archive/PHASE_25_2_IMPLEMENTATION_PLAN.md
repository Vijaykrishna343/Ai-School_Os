# PHASE 25.2 — IMPLEMENTATION PLAN: PAYMENT GATEWAY ABSTRACTION

## GOAL
Implement a provider-independent, multi-tenant capable Payment Gateway Abstraction Layer for the AI School OS platform. This abstraction decouples application and settlement logic from specific payment providers (Razorpay, Stripe) using clean adapters, normalized Pydantic DTOs, cryptographic webhook signature verification, exact `Decimal` monetary math, error normalization, and factory-based resolution.

> [!IMPORTANT]
> **Strict Phase Boundary**: No public payment API endpoints (`/api/v1/payments/*`), automated fee settlement logic, parent checkout UI, database schema modifications, or Alembic migrations will be created in Phase 25.2. Core authorization (`backend/app/common/authorization.py`) MUST remain at **0 diff**.

---

## PROPOSED CHANGES

### 1. Payment Schemas & DTOs (`backend/app/schemas/payment.py`)
#### [NEW] [payment.py](file:///c:/Projects/school-erp/backend/app/schemas/payment.py)
Define strongly-typed, provider-neutral Pydantic models:
- `GatewayOrderRequest`: `amount` (`Decimal > 0`), `currency` (`INR`/`USD`), `receipt`, `customer_name`, `customer_email`, `customer_phone`, `notes`.
- `GatewayOrderResponse`: `provider`, `gateway_order_id`, `amount` (`Decimal`), `currency`, `status`, `created_at`, `raw_response`.
- `GatewayPaymentVerificationRequest`: `provider`, `gateway_order_id`, `gateway_payment_id`, `gateway_signature`.
- `GatewayPaymentVerificationResult`: `is_valid`, `provider`, `gateway_order_id`, `gateway_payment_id`, `message`.
- `GatewayWebhookEvent`: `provider`, `event_id`, `event_type`, `gateway_order_id`, `gateway_transaction_id`, `amount`, `currency`, `status`, `event_timestamp`, `raw_payload`.

---

### 2. Payment Exceptions & Error Normalization (`backend/app/common/exceptions/payment.py`)
#### [NEW] [payment.py](file:///c:/Projects/school-erp/backend/app/common/exceptions/payment.py)
Define an application-level payment error hierarchy:
- `PaymentGatewayError(Exception)`: Base payment error.
- `PaymentAuthenticationError`: Invalid API keys or credentials.
- `PaymentInvalidRequestError`: Invalid request parameters or zero/negative amounts.
- `PaymentProviderUnavailableError`: Network failures or timeout exceptions.
- `PaymentSignatureVerificationError`: HMAC / webhook signature mismatch or forgery.
- `PaymentConfigurationError`: Missing provider credentials.
- `PaymentUnsupportedProviderError`: Unrecognized or unsupported provider request.

---

### 3. Payment Gateway Architecture (`backend/app/services/payment_gateways/`)
#### [NEW] [__init__.py](file:///c:/Projects/school-erp/backend/app/services/payment_gateways/__init__.py)
#### [NEW] [base.py](file:///c:/Projects/school-erp/backend/app/services/payment_gateways/base.py)
Define abstract contract `BasePaymentGateway(abc.ABC)` with abstract methods:
- `provider`: Returns `PaymentProvider`.
- `create_order(request: GatewayOrderRequest)`: Abstract order creation.
- `verify_payment_signature(request: GatewayPaymentVerificationRequest)`: Client verification.
- `verify_webhook_signature(payload: str | bytes, signature: str, secret: str)`: Cryptographic HMAC check.
- `parse_webhook_event(payload: str | bytes, signature: str | None, secret: str | None)`: Normalizes raw webhook events to `GatewayWebhookEvent`.

#### [NEW] [razorpay_adapter.py](file:///c:/Projects/school-erp/backend/app/services/payment_gateways/razorpay_adapter.py)
- Concrete implementation `RazorpayGatewayAdapter(BasePaymentGateway)`.
- Converts `Decimal` amounts to paise via exact integer math: `int((amount * Decimal("100")).quantize(Decimal("1")))`.
- Computes timing-safe HMAC-SHA256 signature verification for client callbacks (`razorpay_order_id|razorpay_payment_id`) and webhooks (`X-Razorpay-Signature`).
- Normalizes Razorpay events (e.g. `payment.authorized`, `order.paid`, `payment.failed`) to `GatewayWebhookEvent`.

#### [NEW] [stripe_adapter.py](file:///c:/Projects/school-erp/backend/app/services/payment_gateways/stripe_adapter.py)
- Concrete implementation `StripeGatewayAdapter(BasePaymentGateway)`.
- Converts `Decimal` amounts to cents via exact integer math.
- Computes timing-safe HMAC-SHA256 signature verification for Stripe webhooks (`t={timestamp},v1={sig}`).
- Normalizes Stripe events (e.g. `payment_intent.succeeded`, `checkout.session.completed`, `payment_intent.payment_failed`) to `GatewayWebhookEvent`.

---

### 4. Gateway Service & Factory (`backend/app/services/payment_gateway_service.py`)
#### [NEW] [payment_gateway_service.py](file:///c:/Projects/school-erp/backend/app/services/payment_gateway_service.py)
- Provide `PaymentGatewayFactory` for resolving `BasePaymentGateway` instances based on `PaymentProvider` (`RAZORPAY`, `STRIPE`).
- Safely accepts optional tenant credentials to construct isolated, non-leaking gateway adapters.
- Raises `PaymentUnsupportedProviderError` when passed unsupported provider types.

---

### 5. Application Core Configuration (`backend/app/core/config.py`)
#### [MODIFY] [config.py](file:///c:/Projects/school-erp/backend/app/core/config.py)
- Add non-secret default configuration keys for gateway resolution (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`).

---

### 6. Comprehensive Abstraction Tests (`backend/tests/test_payment_gateway.py`)
#### [NEW] [test_payment_gateway.py](file:///c:/Projects/school-erp/backend/tests/test_payment_gateway.py)
Deterministic tests using mocks and stubs (0 real external network calls):
1. **Factory Resolution**: Razorpay and Stripe resolve correctly; unsupported provider fails closed with `PaymentUnsupportedProviderError`.
2. **Order Creation & Decimal Precision**: Verifies exact integer smallest-unit conversion for `100.00`, `100.50`, `999.99`, `12345.67` without floating-point rounding errors.
3. **Payment Verification**: Valid signature passes; modified payload or invalid signature fails with `PaymentSignatureVerificationError`.
4. **Webhook Signature Verification**:
   - Razorpay: Valid `X-Razorpay-Signature` PASS, tampered payload FAIL.
   - Stripe: Valid `Stripe-Signature` (`t=...,v1=...`) PASS, tampered payload FAIL.
5. **Webhook Normalization**: Correctly normalizes provider events into `GatewayWebhookEvent`.
6. **Error Normalization**: Normalizes authentication, invalid request, and timeout errors into application payment exceptions.
7. **Credential & Tenant Safety**: Verifies no secrets leak in DTOs, exception strings, or logs, and adapter instances maintain strict isolation.

---

## VERIFICATION PLAN

### Automated Tests
1. Gateway Abstraction Unit Tests:
   `.\venv\Scripts\python.exe -m pytest tests/test_payment_gateway.py -v`
2. All Payment Unit Tests:
   `.\venv\Scripts\python.exe -m pytest tests/test_payment_models.py tests/test_payment_gateway.py -v`
3. Full Backend Test Suite:
   `.\venv\Scripts\python.exe -m pytest -q` (Target: 897+ passed / 0 failed)
4. Frontend Vitest Suite:
   `npm run test -- --run` (Target: 133 passed / 0 failed)
5. TypeScript Check:
   `npx tsc --noEmit` (Target: 0 errors)
6. Production Build:
   `npm run build`
7. Alembic Migration Check:
   `.\venv\Scripts\python.exe -m alembic heads` (Target: Single head `f6k5y7t8c9d0`)
8. Authorization Invariant Check:
   `git diff -- backend/app/common/authorization.py` (Target: 0 diff)

---

## USER REVIEW REQUIRED

> [!NOTE]
> This phase introduces pure python service abstractions, schemas, and test suites. No database migrations, API routes, or authorization rules are modified.
