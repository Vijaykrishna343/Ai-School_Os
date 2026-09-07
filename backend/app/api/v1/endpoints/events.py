from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.services.event_service import event_service

router = APIRouter()


class EventCreateSchema(BaseModel):
    title: str
    event_type: str = "HOLIDAY"
    start_datetime: datetime
    end_datetime: datetime
    academic_year_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    all_day: bool = False
    venue: Optional[str] = None
    audience_scope: str = "SCHOOL"
    target_class_id: Optional[uuid.UUID] = None
    target_section_id: Optional[uuid.UUID] = None
    status: str = "DRAFT"


class EventUpdateSchema(BaseModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    description: Optional[str] = None
    all_day: Optional[bool] = None
    venue: Optional[str] = None
    audience_scope: Optional[str] = None
    target_class_id: Optional[uuid.UUID] = None
    target_section_id: Optional[uuid.UUID] = None
    status: Optional[str] = None


@router.post("/", status_code=201)
def create_event(
    payload: EventCreateSchema,
    current_user: IdentityUser = Depends(require_permission("events.create")),
    db: Session = Depends(get_db),
):
    event = event_service.create_event(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        user_email=current_user.email,
        title=payload.title,
        event_type=payload.event_type,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        academic_year_id=payload.academic_year_id,
        description=payload.description,
        all_day=payload.all_day,
        venue=payload.venue,
        audience_scope=payload.audience_scope,
        target_class_id=payload.target_class_id,
        target_section_id=payload.target_section_id,
        status=payload.status,
    )
    return ApiResponse.success(
        message="School event created successfully.",
        data={"id": str(event.id), "title": event.title, "status": event.status},
    )


@router.get("/")
def list_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    audience_scope: Optional[str] = Query(None),
    current_user: IdentityUser = Depends(require_permission("events.view")),
    db: Session = Depends(get_db),
):
    # Staff / Admins can see drafts; Parents / Students only see published
    is_staff = any(r.name in ["Super Admin", "School Admin", "Principal", "Vice Principal", "Teacher", "Class Teacher"] for r in current_user.roles)
    include_drafts = is_staff

    events = event_service.list_events(
        db=db,
        school_id=current_user.school_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        status=status,
        audience_scope=audience_scope,
        include_drafts=include_drafts,
    )

    data = [
        {
            "id": str(e.id),
            "academic_year_id": str(e.academic_year_id) if e.academic_year_id else None,
            "title": e.title,
            "description": e.description,
            "event_type": e.event_type,
            "start_datetime": e.start_datetime.isoformat(),
            "end_datetime": e.end_datetime.isoformat(),
            "all_day": e.all_day,
            "venue": e.venue,
            "audience_scope": e.audience_scope,
            "status": e.status,
        }
        for e in events
    ]
    return ApiResponse.success(data=data)


@router.get("/{event_id}")
def get_event(
    event_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("events.view")),
    db: Session = Depends(get_db),
):
    event = event_service.get_event_by_id(db, current_user.school_id, event_id)
    return ApiResponse.success(
        data={
            "id": str(event.id),
            "academic_year_id": str(event.academic_year_id) if event.academic_year_id else None,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "start_datetime": event.start_datetime.isoformat(),
            "end_datetime": event.end_datetime.isoformat(),
            "all_day": event.all_day,
            "venue": event.venue,
            "audience_scope": event.audience_scope,
            "status": event.status,
        }
    )


@router.put("/{event_id}")
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdateSchema,
    current_user: IdentityUser = Depends(require_permission("events.update")),
    db: Session = Depends(get_db),
):
    event = event_service.update_event(
        db=db,
        school_id=current_user.school_id,
        event_id=event_id,
        user_id=current_user.id,
        user_email=current_user.email,
        data=payload.model_dump(exclude_unset=True),
    )
    return ApiResponse.success(
        message="School event updated successfully.",
        data={"id": str(event.id), "title": event.title, "status": event.status},
    )


@router.put("/{event_id}/publish")
def publish_event(
    event_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("events.publish")),
    db: Session = Depends(get_db),
):
    event = event_service.publish_event(
        db=db,
        school_id=current_user.school_id,
        event_id=event_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.success(
        message="School event published successfully.",
        data={"id": str(event.id), "status": event.status},
    )


@router.put("/{event_id}/cancel")
def cancel_event(
    event_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("events.delete")),
    db: Session = Depends(get_db),
):
    event = event_service.cancel_event(
        db=db,
        school_id=current_user.school_id,
        event_id=event_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.success(
        message="School event cancelled successfully.",
        data={"id": str(event.id), "status": event.status},
    )


@router.delete("/{event_id}")
def delete_event(
    event_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("events.delete")),
    db: Session = Depends(get_db),
):
    event_service.delete_event(
        db=db,
        school_id=current_user.school_id,
        event_id=event_id,
        user_id=current_user.id,
        user_email=current_user.email,
    )
    return ApiResponse.success(message="School event deleted successfully.")
