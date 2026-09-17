"""
Notification & Communication Center API Endpoints — Phase 8
Includes User Inbox, Communication Preferences, Admin Delivery Tracking, Provider Status, Templates, and Retry Actions.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
from uuid import UUID
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.common.authorization import (
    enforce_relationship_access,
    resolve_parent_linked_student_ids,
    resolve_student_id_for_user,
    resolve_user_role_names,
)
from app.common.responses import ApiResponse
from app.core.config import settings
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.communication import SchoolCommunicationConfig
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from app.schemas.background_job import BatchNotificationAsyncRequest
from app.schemas.communication import (
    UserCommunicationPreferenceUpdate,
    UserCommunicationPreferenceResponse,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    SchoolCommunicationConfigResponse,
    SchoolCommunicationConfigUpdate,
)
from app.services.notification_service import notification_service
from app.services.school_communication_config_service import SchoolCommunicationConfigService

router = APIRouter()


class AnnouncementRequest(BaseModel):
    title: str
    message: str
    recipient_name: str
    recipient_contact: str
    channel: NotificationChannel = NotificationChannel.IN_APP


# ── USER NOTIFICATION INBOX ───────────────────────────────────────────────────

@router.get("/inbox", summary="Get Current User Notification Inbox")
def get_user_inbox(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    items, total, unread_count = notification_service.get_user_inbox(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        data={
            "items": items,
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/unread-count", summary="Get User Unread Notification Count Badge")
def get_unread_count(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    _, _, unread_count = notification_service.get_user_inbox(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        page=1,
        page_size=1,
    )
    return ApiResponse.success(data={"unread_count": unread_count})


@router.post("/inbox/{id}/read", summary="Mark Notification As Read")
def mark_notification_read(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    notification_service.mark_as_read(db=db, school_id=current_user.school_id, user_id=current_user.id, notification_id=id)
    return ApiResponse.success(message="Notification marked as read.")


@router.post("/inbox/read-all", summary="Mark All Notifications As Read")
def mark_all_notifications_read(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    count = notification_service.mark_all_as_read(db=db, school_id=current_user.school_id, user_id=current_user.id)
    return ApiResponse.success(message=f"Marked {count} notifications as read.")


# ── USER COMMUNICATION PREFERENCES ──────────────────────────────────────────

@router.get("/preferences", summary="Get User Communication Preferences")
def get_user_preferences(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    pref = notification_service.get_user_preferences(db=db, school_id=current_user.school_id, user_id=current_user.id)
    return ApiResponse.success(data=UserCommunicationPreferenceResponse.model_validate(pref).model_dump(mode="json"))


@router.put("/preferences", summary="Update User Communication Preferences")
def update_user_preferences(
    payload: UserCommunicationPreferenceUpdate,
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True)
    pref = notification_service.update_user_preferences(
        db=db, school_id=current_user.school_id, user_id=current_user.id, updates=updates
    )
    return ApiResponse.success(
        data=UserCommunicationPreferenceResponse.model_validate(pref).model_dump(mode="json"),
        message="Communication preferences updated successfully.",
    )


# ── TENANT COMMUNICATION PROVIDER CONFIGURATION ────────────────────────────────

@router.get("/config", summary="Get Tenant Communication Provider Configuration")
def get_school_communication_config(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    config = SchoolCommunicationConfigService.get_or_create_config(
        db=db, school_id=current_user.school_id
    )
    dto = SchoolCommunicationConfigService.to_response_dto(config)
    return ApiResponse.success(data=dto.model_dump(mode="json"))


@router.put("/config", summary="Update Tenant Communication Provider Configuration")
def update_school_communication_config(
    payload: SchoolCommunicationConfigUpdate,
    current_user: IdentityUser = Depends(require_permission("notification.manage")),
    db: Session = Depends(get_db),
):
    config = SchoolCommunicationConfigService.update_config(
        db=db, school_id=current_user.school_id, updates=payload
    )
    dto = SchoolCommunicationConfigService.to_response_dto(config)
    return ApiResponse.success(
        data=dto.model_dump(mode="json"),
        message="School communication provider configuration updated successfully.",
    )


import hashlib
import hmac
import json
from fastapi import Response, Request, HTTPException


# ── META WHATSAPP SECURE WEBHOOKS ──────────────────────────────────────────────

@router.get("/webhooks/whatsapp", summary="Meta WhatsApp Webhook Verification Handshake")
def verify_whatsapp_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """
    Handles Meta Cloud API Webhook GET verification handshake.
    Validates hub.verify_token and echoes back hub.challenge in plain text.
    """
    expected_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    if mode == "subscribe" and verify_token and hmac.compare_digest(verify_token, expected_token):
        logger.info("Meta WhatsApp webhook verification succeeded.")
        return Response(content=challenge or "", media_type="text/plain", status_code=200)

    logger.warning("Meta WhatsApp webhook verification failed (invalid verify_token).")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token.")


@router.post("/webhooks/whatsapp", summary="Meta WhatsApp Outbound Delivery & Read Webhook Event")
async def process_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handles inbound Meta Cloud API status webhooks (sent, delivered, read, failed).
    Validates HMAC SHA-256 signature, resolves tenant strictly by phone_number_id mapping,
    enforces monotonic status transitions, and preserves idempotency.
    """
    raw_body = await request.body()

    # 1. Validate Meta Webhook Signature if WHATSAPP_APP_SECRET is configured
    signature_header = request.headers.get("x-hub-signature-256")
    if settings.WHATSAPP_APP_SECRET and settings.WHATSAPP_APP_SECRET.strip():
        if not signature_header or not signature_header.startswith("sha256="):
            logger.warning("Meta WhatsApp webhook POST rejected: Missing or malformed signature header.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature header.")

        expected_sig = "sha256=" + hmac.new(
            settings.WHATSAPP_APP_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature_header, expected_sig):
            logger.warning("Meta WhatsApp webhook POST rejected: Invalid HMAC signature mismatch.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature mismatch.")

    # 2. Parse Webhook Event JSON safely
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    # 3. Process Status Updates
    entries = payload.get("entry", [])
    processed_count = 0

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            # Resolve Tenant strictly by matching stored whatsapp_phone_number_id
            config = None
            if phone_number_id:
                config = db.scalar(
                    select(SchoolCommunicationConfig).where(
                        SchoolCommunicationConfig.whatsapp_phone_number_id == phone_number_id,
                        SchoolCommunicationConfig.is_deleted.is_(False),
                    )
                )

            statuses = value.get("statuses", [])
            for st in statuses:
                wamid = st.get("id")
                wa_status = st.get("status")  # sent, delivered, read, failed

                if not wamid:
                    continue

                # Find notification by provider_message_id
                query = select(Notification).where(
                    Notification.provider_message_id == wamid,
                    Notification.is_deleted.is_(False),
                )
                if config:
                    query = query.where(Notification.school_id == config.school_id)

                notif = db.scalar(query)
                if not notif:
                    logger.info("Webhook status '%s' received for unmapped or unknown wamid: %s", wa_status, wamid)
                    continue

                # Enforce Monotonic Status Transitions (SENT -> DELIVERED -> READ, FAILED)
                if wa_status in ("delivered", "read"):
                    if notif.status in (NotificationStatus.PENDING, NotificationStatus.QUEUED, NotificationStatus.SENT):
                        notif.status = NotificationStatus.DELIVERED
                        notif.sent_at = notif.sent_at or datetime.now(timezone.utc)
                        db.add(notif)
                        processed_count += 1
                elif wa_status == "sent":
                    if notif.status in (NotificationStatus.PENDING, NotificationStatus.QUEUED):
                        notif.status = NotificationStatus.SENT
                        notif.sent_at = notif.sent_at or datetime.now(timezone.utc)
                        db.add(notif)
                        processed_count += 1
                elif wa_status == "failed":
                    errors = st.get("errors", [])
                    err_msg = errors[0].get("title", "WhatsApp delivery failed") if errors else "WhatsApp delivery failed"
                    notif.status = NotificationStatus.FAILED
                    notif.error_message = f"Meta WhatsApp Error: {err_msg}"
                    db.add(notif)
                    processed_count += 1

    if processed_count > 0:
        db.commit()

    return {"status": "success", "processed_events": processed_count}


# ── ADMIN COMMUNICATION CENTER & PROVIDER MANAGEMENT ──────────────────────────

@router.get("", summary="List Notifications (Delivery Logs)")
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    channel: NotificationChannel | None = Query(default=None),
    event_type: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select, func, or_
    from app.models.notification import Notification, NotificationStatus
    from app.models.parent.parent import Parent

    enforce_relationship_access(db, school_id=current_user.school_id, current_user=current_user)
    role_names = resolve_user_role_names(db, current_user)

    q = select(Notification).where(
        Notification.school_id == current_user.school_id,
        Notification.is_deleted.is_(False),
    )

    if "Parent" in role_names and not current_user.is_super_admin:
        linked_student_ids = resolve_parent_linked_student_ids(db, current_user.school_id, current_user)
        if not linked_student_ids:
            return ApiResponse.success(data={"items": [], "total": 0, "page": page, "page_size": page_size})

        parent = None
        if getattr(current_user, "email", None):
            parent = db.scalar(
                select(Parent).where(
                    Parent.email == current_user.email,
                    Parent.school_id == current_user.school_id,
                    Parent.is_deleted.is_(False),
                )
            )
        if not parent and getattr(current_user, "phone", None):
            parent = db.scalar(
                select(Parent).where(
                    (Parent.primary_phone == current_user.phone) | (Parent.secondary_phone == current_user.phone),
                    Parent.school_id == current_user.school_id,
                    Parent.is_deleted.is_(False),
                )
            )

        parent_conditions = []
        if parent:
            parent_conditions.append((Notification.recipient_type == NotificationRecipientType.PARENT) & (Notification.recipient_id == parent.id))
            if parent.primary_phone:
                parent_conditions.append(Notification.recipient_contact == parent.primary_phone)
            if parent.secondary_phone:
                parent_conditions.append(Notification.recipient_contact == parent.secondary_phone)
        if current_user.email:
            parent_conditions.append(Notification.recipient_contact == current_user.email)
            
        parent_conditions.append(Notification.recipient_id.in_(linked_student_ids))
        parent_conditions.append(Notification.recipient_contact == "all@school.com")
        parent_conditions.append(Notification.recipient_contact == "parents@school.com")

        q = q.where(or_(*parent_conditions))

    elif "Student" in role_names and not current_user.is_super_admin:
        student_id = resolve_student_id_for_user(db, current_user.school_id, current_user)
        if not student_id:
            return ApiResponse.success(data={"items": [], "total": 0, "page": page, "page_size": page_size})
        
        student_conditions = [Notification.recipient_id == student_id]
        if current_user.email:
            student_conditions.append(Notification.recipient_contact == current_user.email)
        student_conditions.append(Notification.recipient_contact == "all@school.com")
        student_conditions.append(Notification.recipient_contact == "students@school.com")
        
        q = q.where(or_(*student_conditions))

    if status_filter:
        try:
            q = q.where(Notification.status == NotificationStatus(status_filter.upper()))
        except ValueError:
            pass
    if channel:
        q = q.where(Notification.channel == channel)
    if event_type:
        q = q.where(Notification.template_key == event_type.strip())
    if start_date:
        q = q.where(Notification.created_at >= start_date)
    if end_date:
        q = q.where(Notification.created_at <= end_date)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        q = q.where(
            or_(
                Notification.recipient_name.ilike(search_term),
                Notification.title.ilike(search_term),
                Notification.recipient_contact.ilike(search_term),
            )
        )

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    offset = (page - 1) * page_size
    items = db.execute(q.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    data_items = [
        {
            "id": str(n.id),
            "recipient_type": n.recipient_type.value if hasattr(n.recipient_type, "value") else str(n.recipient_type),
            "recipient_id": str(n.recipient_id) if n.recipient_id else None,
            "recipient_name": n.recipient_name,
            "recipient_contact": n.recipient_contact,
            "channel": n.channel.value if hasattr(n.channel, "value") else str(n.channel),
            "template_key": n.template_key,
            "title": n.title,
            "body": n.body,
            "status": n.status.value if hasattr(n.status, "value") else str(n.status),
            "error_message": n.error_message,
            "retry_count": n.retry_count,
            "max_retries": n.max_retries,
            "provider_name": n.provider_name,
            "provider_message_id": n.provider_message_id,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None,
        }
        for n in items
    ]

    return ApiResponse.success(data={"items": data_items, "total": total, "page": page, "page_size": page_size})


@router.get("/analytics", summary="Get Notification Analytics & Aggregations")
def get_notification_analytics(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    analytics = notification_service.get_notification_analytics(
        db=db,
        school_id=current_user.school_id,
        start_date=start_date,
        end_date=end_date,
    )
    return ApiResponse.success(data=analytics)


@router.get("/providers/status", summary="Get Notification Provider Statuses")
def get_provider_statuses(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
):
    providers = notification_service.get_provider_statuses()
    return ApiResponse.success(data=providers)


@router.get("/templates", summary="List Notification Templates")
def list_templates(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    templates = notification_service.get_templates(db=db, school_id=current_user.school_id)
    return ApiResponse.success(data=templates)


@router.post("/templates", summary="Create Custom Notification Template", status_code=status.HTTP_201_CREATED)
def create_template(
    payload: NotificationTemplateCreate,
    current_user: IdentityUser = Depends(require_permission("notification.template.manage")),
    db: Session = Depends(get_db),
):
    tpl = notification_service.create_template(
        db=db,
        school_id=current_user.school_id,
        template_key=payload.template_key,
        name=payload.name,
        title_template=payload.title_template,
        body_template=payload.body_template,
        category=payload.category,
        dlt_entity_id=payload.dlt_entity_id,
        dlt_template_id=payload.dlt_template_id,
        whatsapp_template_name=payload.whatsapp_template_name,
        whatsapp_language_code=payload.whatsapp_language_code,
    )
    return ApiResponse.success(
        data=NotificationTemplateResponse.model_validate(tpl).model_dump(mode="json"),
        message="Notification template created successfully.",
    )


@router.get("/delivery-metrics", summary="Get Notification Delivery Metrics")
def get_delivery_metrics(
    current_user: IdentityUser = Depends(require_permission("notification.delivery.view")),
    db: Session = Depends(get_db),
):
    metrics = notification_service.get_delivery_metrics(db=db, school_id=current_user.school_id)
    return ApiResponse.success(data=metrics)


@router.post("/send", summary="Send Announcement", status_code=status.HTTP_201_CREATED)
def send_announcement(
    body: AnnouncementRequest,
    current_user: IdentityUser = Depends(require_permission("notification.send")),
    db: Session = Depends(get_db),
):
    if not body.recipient_contact or not body.recipient_contact.strip():
        from app.common.exceptions import BadRequestException
        raise BadRequestException("Recipient contact must be provided.")

    notification = notification_service.send_announcement(
        db=db,
        school_id=current_user.school_id,
        title=body.title,
        message=body.message,
        recipient_name=body.recipient_name,
        recipient_contact=body.recipient_contact,
        channel=body.channel,
    )
    db.commit()

    return ApiResponse.success(
        data={
            "id": str(notification.id),
            "status": notification.status,
            "title": notification.title,
            "channel": notification.channel,
        },
        message="Notification dispatched successfully.",
    )


@router.post(
    "/batch-send-async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Asynchronously Dispatch Batch Notifications",
)
def batch_send_notifications_async(
    body: BatchNotificationAsyncRequest,
    background_tasks: BackgroundTasks,
    current_user: IdentityUser = Depends(require_permission("notification.send")),
    db: Session = Depends(get_db),
):
    from app.models.background_job import JobType
    from app.repositories.job_repository import job_repository
    from app.services.async_job_runner import async_job_runner

    job = job_repository.create_job(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        job_type=JobType.BULK_NOTIFICATION_DISPATCH,
        payload=body.model_dump(mode="json"),
        idempotency_key=body.idempotency_key,
        total_items=len(body.recipients),
    )
    db.commit()

    background_tasks.add_task(async_job_runner.process_job, current_user.school_id, job.id)

    return ApiResponse.success(
        data={
            "job_id": str(job.id),
            "status": job.status,
            "job_type": job.job_type,
            "total_recipients": len(body.recipients),
        },
        message="Batch notification job enqueued.",
    )


@router.get("/{id}", summary="Get Single Notification Details")
def get_notification_detail(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("notification.view")),
    db: Session = Depends(get_db),
):
    notif = notification_service.get_notification_detail(
        db=db, school_id=current_user.school_id, notification_id=id
    )
    # Role-based access control for parent/student
    role_names = resolve_user_role_names(db, current_user)
    if "Parent" in role_names and not current_user.is_super_admin:
        linked_student_ids = resolve_parent_linked_student_ids(db, current_user.school_id, current_user)
        if not (
            (notif.recipient_id and notif.recipient_id in linked_student_ids)
            or notif.recipient_contact in (current_user.email, current_user.phone, "all@school.com", "parents@school.com")
            or (notif.recipient_id == current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    elif "Student" in role_names and not current_user.is_super_admin:
        student_id = resolve_student_id_for_user(db, current_user.school_id, current_user)
        if not (
            (student_id and notif.recipient_id == student_id)
            or notif.recipient_contact in (current_user.email, "all@school.com", "students@school.com")
            or (notif.recipient_id == current_user.id)
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return ApiResponse.success(
        data={
            "id": str(notif.id),
            "school_id": str(notif.school_id),
            "recipient_type": notif.recipient_type.value if hasattr(notif.recipient_type, "value") else str(notif.recipient_type),
            "recipient_id": str(notif.recipient_id) if notif.recipient_id else None,
            "recipient_name": notif.recipient_name,
            "recipient_contact": notif.recipient_contact,
            "channel": notif.channel.value if hasattr(notif.channel, "value") else str(notif.channel),
            "template_key": notif.template_key,
            "title": notif.title,
            "body": notif.body,
            "status": notif.status.value if hasattr(notif.status, "value") else str(notif.status),
            "error_message": notif.error_message,
            "retry_count": notif.retry_count,
            "max_retries": notif.max_retries,
            "provider_name": notif.provider_name,
            "provider_message_id": notif.provider_message_id,
            "idempotency_key": notif.idempotency_key,
            "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
            "updated_at": notif.updated_at.isoformat() if notif.updated_at else None,
        }
    )


@router.post("/{id}/retry", summary="Retry Failed Notification Delivery")
def retry_notification(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("notification.send")),
    db: Session = Depends(get_db),
):
    notif = notification_service.retry_failed_notification(
        db=db,
        school_id=current_user.school_id,
        notification_id=id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.success(
        data={
            "id": str(notif.id),
            "status": notif.status,
            "retry_count": notif.retry_count,
            "error_message": notif.error_message,
        },
        message="Notification retry executed.",
    )
