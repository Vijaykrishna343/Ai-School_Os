from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.models.event.school_event import SchoolEvent
from app.models.audit_log import AuditLog
from app.common.exceptions import BadRequestException, NotFoundException
from app.services.notification_service import notification_service


class EventService:
    """
    Service layer for School Events and Calendar Management.
    Strictly tenant-isolated by school_id.
    """

    def _log_audit(
        self,
        db: Session,
        school_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
        action: str,
        entity_id: str,
        details: str,
    ) -> None:
        try:
            audit = AuditLog(
                school_id=school_id,
                user_id=user_id,
                user_email=user_email or "system@school.com",
                action=action,
                module="events",
                entity_type="SchoolEvent",
                entity_id=entity_id,
                status_code=200,
                details=details,
            )
            db.add(audit)
        except Exception:
            pass

    def create_event(
        self,
        db: Session,
        school_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
        title: str,
        event_type: str,
        start_datetime: datetime,
        end_datetime: datetime,
        academic_year_id: uuid.UUID | None = None,
        description: str | None = None,
        all_day: bool = False,
        venue: str | None = None,
        audience_scope: str = "SCHOOL",
        target_class_id: uuid.UUID | None = None,
        target_section_id: uuid.UUID | None = None,
        status: str = "DRAFT",
    ) -> SchoolEvent:
        if end_datetime <= start_datetime:
            raise BadRequestException("Event end_datetime must be strictly after start_datetime.")

        event = SchoolEvent(
            school_id=school_id,
            academic_year_id=academic_year_id,
            title=title,
            description=description,
            event_type=event_type,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            all_day=all_day,
            venue=venue,
            organizer_id=user_id,
            audience_scope=audience_scope,
            target_class_id=target_class_id,
            target_section_id=target_section_id,
            status=status,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        self._log_audit(
            db,
            school_id,
            user_id,
            user_email,
            "event.create",
            str(event.id),
            f"Created event '{title}' (type: {event_type}, status: {status}).",
        )
        db.commit()
        return event

    def get_event_by_id(
        self,
        db: Session,
        school_id: uuid.UUID,
        event_id: uuid.UUID,
    ) -> SchoolEvent:
        event = db.execute(
            select(SchoolEvent).where(
                SchoolEvent.id == event_id,
                SchoolEvent.school_id == school_id,
                SchoolEvent.is_deleted.is_(False),
            )
        ).scalar_one_or_none()

        if not event:
            raise NotFoundException("School event not found.")
        return event

    def update_event(
        self,
        db: Session,
        school_id: uuid.UUID,
        event_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
        data: dict,
    ) -> SchoolEvent:
        event = self.get_event_by_id(db, school_id, event_id)

        start = data.get("start_datetime", event.start_datetime)
        end = data.get("end_datetime", event.end_datetime)
        if end <= start:
            raise BadRequestException("Event end_datetime must be strictly after start_datetime.")

        for key, val in data.items():
            if hasattr(event, key) and val is not None:
                setattr(event, key, val)

        db.commit()
        db.refresh(event)

        self._log_audit(
            db,
            school_id,
            user_id,
            user_email,
            "event.update",
            str(event.id),
            f"Updated event '{event.title}'.",
        )
        db.commit()
        return event

    def publish_event(
        self,
        db: Session,
        school_id: uuid.UUID,
        event_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
    ) -> SchoolEvent:
        event = self.get_event_by_id(db, school_id, event_id)
        if event.status == "PUBLISHED":
            return event

        event.status = "PUBLISHED"
        db.commit()
        db.refresh(event)

        self._log_audit(
            db,
            school_id,
            user_id,
            user_email,
            "event.publish",
            str(event.id),
            f"Published event '{event.title}' to audience scope '{event.audience_scope}'.",
        )
        db.commit()

        # Trigger notification queue dispatch
        try:
            notification_service.queue_notification(
                db=db,
                school_id=school_id,
                recipient_type="SCHOOL",
                recipient_id=school_id,
                channel="IN_APP",
                subject=f"School Event Announcement: {event.title}",
                body=f"A new school event '{event.title}' ({event.event_type}) has been scheduled for {event.start_datetime.strftime('%Y-%m-%d %H:%M')}.",
            )
        except Exception:
            pass

        return event

    def cancel_event(
        self,
        db: Session,
        school_id: uuid.UUID,
        event_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
    ) -> SchoolEvent:
        event = self.get_event_by_id(db, school_id, event_id)
        event.status = "CANCELLED"
        db.commit()
        db.refresh(event)

        self._log_audit(
            db,
            school_id,
            user_id,
            user_email,
            "event.cancel",
            str(event.id),
            f"Cancelled event '{event.title}'.",
        )
        db.commit()
        return event

    def delete_event(
        self,
        db: Session,
        school_id: uuid.UUID,
        event_id: uuid.UUID,
        user_id: uuid.UUID | None,
        user_email: str,
    ) -> None:
        event = self.get_event_by_id(db, school_id, event_id)
        event.is_deleted = True
        db.commit()

        self._log_audit(
            db,
            school_id,
            user_id,
            user_email,
            "event.delete",
            str(event_id),
            f"Soft-deleted event '{event.title}'.",
        )
        db.commit()

    def list_events(
        self,
        db: Session,
        school_id: uuid.UUID,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        event_type: str | None = None,
        status: str | None = None,
        audience_scope: str | None = None,
        include_drafts: bool = False,
    ) -> Sequence[SchoolEvent]:
        query = select(SchoolEvent).where(
            SchoolEvent.school_id == school_id,
            SchoolEvent.is_deleted.is_(False),
        )

        if not include_drafts:
            query = query.where(SchoolEvent.status.in_(["PUBLISHED", "COMPLETED", "CANCELLED"]))
        elif status:
            query = query.where(SchoolEvent.status == status)

        if start_date:
            query = query.where(SchoolEvent.end_datetime >= start_date)
        if end_date:
            query = query.where(SchoolEvent.start_datetime <= end_date)
        if event_type:
            query = query.where(SchoolEvent.event_type == event_type)
        if audience_scope:
            query = query.where(SchoolEvent.audience_scope == audience_scope)

        return db.execute(query.order_by(SchoolEvent.start_datetime.asc())).scalars().all()


event_service = EventService()
