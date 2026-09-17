# Phase 27.4.2 — Visitor Event Notifications Final Verification

## 1. Objective
Connect existing Phase 26 visitor workflows (`check_in_visitor`, `quick_check_in_visitor`, `check_out_visitor` in `visitor_service.py`) to the certified Phase 27.4.1 notification-trigger foundation (`NotificationTriggerService`). Automate host notifications upon successful visitor arrival and departure transactions without breaking transaction safety, tenant isolation, or privacy boundaries.

## 2. Visitor Event Sources
Authoritative backend service operations in `backend/app/services/visitor_service.py`:
- `check_in_visitor`: Registers and checks in a new visitor.
- `quick_check_in_visitor`: Transitions an `EXPECTED` visitor to `CHECKED_IN`.
- `check_out_visitor`: Transitions a `CHECKED_IN` visitor to `CHECKED_OUT`.

No frontend code or API endpoints initiate notification triggers directly; all dispatch is driven by canonical service operations.

## 3. Recipient Resolution
Authoritative host recipient resolver `_resolve_host_recipient` in `visitor_service.py`:
- Resolves host entities strictly matching `visitor.school_id`.
- `HostType.TEACHER`: Queries `Teacher` model (`school_id == visitor.school_id`). Target: `NotificationRecipientType.TEACHER`.
- `HostType.STAFF`: Queries `Teacher` or `IdentityUser` (`school_id == visitor.school_id`). Target: `NotificationRecipientType.STAFF`.
- `HostType.STUDENT`: Queries `Student` (`school_id == visitor.school_id`). If student has a linked `Parent` (`parent_id`), resolves `Parent` (`NotificationRecipientType.PARENT`). Fallback: `NotificationRecipientType.STUDENT`.
- Unresolved / `HostType.OTHER`: No notification staged.

Client-provided recipient IDs or override school IDs are ignored. Host relationship persisted on the visitor record is authoritative.

## 4. Check-In Notification
- Event key: `visitor_checkin`
- Staged before commit; dispatched via `after_commit` hook.
- Includes safe operational template variables: `visitor_name`, `purpose`, `pass_number`, `host_name`, `check_in_time`.
- Excludes sensitive PII (ID proof number, ID proof type, government ID credentials).

## 5. Quick Check-In Notification
- Operates on `EXPECTED` visitors transitioning to `CHECKED_IN`.
- Calls `_trigger_visitor_checkin_notification` prior to commit.
- Idempotency key: `visitor_checkin:{visitor.id}:{channel}` ensures exactly one arrival notification is staged even if quick check-in is retried.

## 6. Checkout Notification
- Event key: `visitor_checkout`
- Target channel: `NotificationChannel.IN_APP`.
- Idempotency key: `visitor_checkout:{visitor.id}:in_app`.
- Template variables: `visitor_name`, `purpose`, `pass_number`, `host_name`, `check_out_time`.

## 7. Template Keys
Defined in `DEFAULT_NOTIFICATION_TEMPLATES` in `notification_service.py`:
- `visitor_checkin` / `visitor.checkin`: `"Visitor Alert: {visitor_name} has arrived at the reception desk to meet you. Purpose: {purpose}. Gate Pass: {pass_number}."`
- `visitor_checkout` / `visitor.checkout`: `"Visitor Departure: {visitor_name} has checked out from the reception desk. Gate Pass: {pass_number}."`

## 8. Channel Policy
- Visitor Arrival: Target `IN_APP` channel; if phone number is present on resolved host recipient, also stages `SMS`.
- Visitor Departure: Target `IN_APP` channel.
- Dispatched independently per channel. Failure of one channel does not fail the entire operation.

## 9. Communication Preferences
- Evaluated via `UserCommunicationPreference` in `NotificationTriggerService.stage_notification_event`.
- Opted-out channels transition notification status to `CANCELLED`.

## 10. Post-Commit Architecture
- Notification staging occurs within ongoing visitor DB session (`db.add(notification)`).
- SQLA `after_commit` event hook executes background dispatch ONLY after `db.commit()` succeeds.
- If DB session rolls back, `after_commit` hook never fires; 0 notifications sent.

## 11. Failure Isolation
- Provider dispatch errors or background network timeouts update `notification.status = FAILED` in an isolated DB session.
- Visitor status (`CHECKED_IN` / `CHECKED_OUT`) remains committed and completely unaffected.

## 12. Idempotency
- Unique idempotency keys (`visitor_checkin:{visitor.id}:{channel}` and `visitor_checkout:{visitor.id}:in_app`).
- Duplicate trigger calls detect existing notification record by `(school_id, idempotency_key)` and skip re-creation.

## 13. Tenant Isolation
- Recipient resolution, visitor queries, and notification entity creation strictly enforce `school_id` scoping.
- Cross-tenant host references are rejected by host validation.

## 14. RBAC
- Notification generation inherits authorization context of the initiating visitor service operation.
- No privilege escalation in background dispatch worker.

## 15. PII Protection
- Government ID proof numbers (`id_proof_number`), proof types, passwords, and sensitive credentials are completely omitted from notification titles, bodies, and event metadata.

## 16. Audit Logging
- Existing visitor audit actions (`VISITOR_CHECK_IN`, `VISITOR_QUICK_CHECK_IN`, `VISITOR_CHECK_OUT`) logged without sensitive PII.

## 17. Focused Tests
- `backend/tests/test_visitor_notifications.py` (5 passed / 0 failed):
  - `test_check_in_visitor_triggers_arrival_notification`
  - `test_quick_check_in_triggers_exactly_one_notification`
  - `test_checkout_visitor_triggers_departure_notification`
  - `test_rollback_safety_sends_no_notification`
  - `test_tenant_isolation_cross_tenant_host`

## 18. Full Backend
- 1,030 passed / 0 failed

## 19. Full Frontend
- 144 passed / 0 failed (Vitest 21/21 suites)

## 20. TypeScript
- `npx tsc --noEmit`: PASS (0 errors)

## 21. Production Build
- `npm run build`: PASS (vite build succeeded in 7.50s)

## 22. Alembic
- Current head: `b5683cd19824` (single head, no database migration needed)

## 23. authorization.py
- `git diff -- app/identity/security/authorization.py`: 0 diff (0 lines changed)

## 24. Phase 26 Regression
- All visitor management, registration, check-in, quick check-in, checkout, reception inquiries, badges, and pre-registration tests pass.

## 25. Phase 27.1 Regression
- SMS/WhatsApp tenant configuration, credential encryption, and DLT metadata tests pass.

## 26. Phase 27.2 Regression
- Fast2SMS and Twilio SMS provider integration tests pass.

## 27. Phase 27.3 Regression
- Meta WhatsApp Cloud API provider integration tests pass.

## 28. Phase 27.4.1 Regression
- NotificationTriggerService foundation, post-commit dispatch, idempotency, and failure isolation tests pass.

## 29. Known Limitations
- Host notification delivery depends on configured channel providers or MockProvider fallback in non-configured test environments.

## 30. Strictly Deferred
- Phase 27.4.3: Fee receipt / payment confirmation notifications.
- Phase 27.4.4: Student absence and homework publication notifications.
- Phase 27.4.5: Cross-domain integration hardening.
- Phase 27.5: Communication analytics and broadcast campaigns.
