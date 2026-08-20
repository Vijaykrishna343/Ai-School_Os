"""
Notification API Endpoint — Phase 9.5/9.6
GET  /api/v1/notifications       — list school notifications (admin)
POST /api/v1/notifications/send  — send a general announcement
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.notification import NotificationChannel, NotificationRecipientType
from app.services.notification_service import notification_service

router = APIRouter()


class AnnouncementRequest(BaseModel):
    title: str
    message: str
    recipient_name: str
    recipient_contact: str
    channel: NotificationChannel = NotificationChannel.IN_APP


@router.get("", summary="List Notifications")
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    channel: NotificationChannel | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
) -> JSONResponse:
    from sqlalchemy import select, func
    from app.models.notification import Notification, NotificationStatus

    q = select(Notification).where(
        Notification.school_id == current_user.school_id,
        Notification.is_deleted.is_(False),
    )
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

    return JSONResponse(content={
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(n.id),
                    "recipient_name": n.recipient_name,
                    "recipient_contact": n.recipient_contact,
                    "channel": n.channel,
                    "template_key": n.template_key,
                    "title": n.title,
                    "body": n.body,
                    "status": n.status,
                    "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    })


@router.post("/send", summary="Send Announcement", status_code=status.HTTP_201_CREATED)
def send_announcement(
    body: AnnouncementRequest,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
) -> JSONResponse:
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

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "success": True,
            "data": {
                "id": str(notification.id),
                "status": notification.status,
                "title": notification.title,
                "channel": notification.channel,
            },
        },
    )


@router.get("/templates", summary="List Notification Templates")
def list_templates(
    current_user: IdentityUser = Depends(require_permission("school.view")),
) -> JSONResponse:
    from app.services.notification_service import NOTIFICATION_TEMPLATES
    return JSONResponse(content={
        "success": True,
        "data": {
            key: {"title": tpl["title"], "body": tpl["body"]}
            for key, tpl in NOTIFICATION_TEMPLATES.items()
        },
    })
