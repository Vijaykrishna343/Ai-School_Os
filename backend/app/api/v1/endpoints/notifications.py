"""
Notification & Communication Center API Endpoints — Phase 8
Includes User Inbox, Communication Preferences, Admin Delivery Tracking, Provider Status, Templates, and Retry Actions.
"""
from __future__ import annotations

from uuid import UUID
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.authorization import (
    enforce_relationship_access,
    resolve_parent_linked_student_ids,
    resolve_student_id_for_user,
    resolve_user_role_names,
)
from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.notification import NotificationChannel, NotificationRecipientType
from app.schemas.background_job import BatchNotificationAsyncRequest
from app.schemas.communication import (
    UserCommunicationPreferenceUpdate,
    UserCommunicationPreferenceResponse,
    NotificationTemplateCreate,
)
from app.services.notification_service import notification_service

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


# ── ADMIN COMMUNICATION CENTER & PROVIDER MANAGEMENT ──────────────────────────

@router.get("", summary="List Notifications (Delivery Logs)")
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    channel: NotificationChannel | None = Query(default=None),
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

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    offset = (page - 1) * page_size
    items = db.execute(q.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    data_items = [
        {
            "id": str(n.id),
            "recipient_name": n.recipient_name,
            "recipient_contact": n.recipient_contact,
            "channel": n.channel,
            "template_key": n.template_key,
            "title": n.title,
            "body": n.body,
            "status": n.status,
            "error_message": n.error_message,
            "retry_count": n.retry_count,
            "max_retries": n.max_retries,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]

    return ApiResponse.success(data={"items": data_items, "total": total, "page": page, "page_size": page_size})


@router.get("/providers/status", summary="Get Notification Provider Statuses")
def get_provider_statuses(
    current_user: IdentityUser = Depends(require_permission("notification.view")),
):
    providers = notification_service.get_provider_statuses()
    return ApiResponse.success(data=providers)


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


@router.post("/{id}/retry", summary="Retry Failed Notification Delivery")
def retry_notification(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("notification.send")),
    db: Session = Depends(get_db),
):
    notif = notification_service.retry_failed_notification(db=db, school_id=current_user.school_id, notification_id=id)
    return ApiResponse.success(
        data={
            "id": str(notif.id),
            "status": notif.status,
            "retry_count": notif.retry_count,
            "error_message": notif.error_message,
        },
        message="Notification retry executed.",
    )


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
    )
    return ApiResponse.success(
        data={
            "id": str(tpl.id),
            "template_key": tpl.template_key,
            "name": tpl.name,
            "category": tpl.category,
            "title_template": tpl.title_template,
            "body_template": tpl.body_template,
            "is_active": tpl.is_active,
            "is_custom": True,
        },
        message="Notification template created successfully.",
    )


@router.get("/delivery-metrics", summary="Get Notification Delivery Metrics")
def get_delivery_metrics(
    current_user: IdentityUser = Depends(require_permission("notification.delivery.view")),
    db: Session = Depends(get_db),
):
    metrics = notification_service.get_delivery_metrics(db=db, school_id=current_user.school_id)
    return ApiResponse.success(data=metrics)


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
