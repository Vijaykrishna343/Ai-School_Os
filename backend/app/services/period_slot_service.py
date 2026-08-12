from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.timetable.period_slot import PeriodSlot
from app.repositories.timetable.period_slot_repository import (
    PeriodSlotRepository,
    period_slot_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.schemas.timetable.period_slot import (
    PeriodSlotCreate,
    PeriodSlotFilter,
    PeriodSlotListResponse,
    PeriodSlotResponse,
    PeriodSlotUpdate,
)


class PeriodSlotService:
    """
    Business logic service for PeriodSlot operations.
    """

    def __init__(
        self,
        repository: PeriodSlotRepository = period_slot_repository,
        school_repo: SchoolRepository = school_repository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repo

    def create_period_slot(
        self,
        db: Session,
        slot_data: PeriodSlotCreate,
        current_school_id: UUID | None = None,
    ) -> PeriodSlot:
        """
        Create a new PeriodSlot for a school.
        """
        if current_school_id is not None and slot_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create period slot for another school.")

        school = self.school_repository.get(db, slot_data.school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(slot_data.school_id))

        if self.repository.exists_by_display_order(
            db, slot_data.school_id, slot_data.display_order
        ):
            raise AlreadyExistsException(
                "PeriodSlot display_order", str(slot_data.display_order)
            )

        slot = PeriodSlot(
            school_id=slot_data.school_id,
            name=slot_data.name,
            period_type=slot_data.period_type,
            start_time=slot_data.start_time,
            end_time=slot_data.end_time,
            display_order=slot_data.display_order,
        )

        return self.repository.create(db, slot)

    def get_period_slot(
        self,
        db: Session,
        slot_id: UUID,
        current_school_id: UUID | None = None,
    ) -> PeriodSlot:
        """
        Retrieve a PeriodSlot by ID within the tenant scope.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        slot = self.repository.get_by_id_and_school(db, slot_id, current_school_id)
        if slot is None:
            raise NotFoundException("PeriodSlot", str(slot_id))

        return slot

    def list_period_slots(
        self,
        db: Session,
        filters: PeriodSlotFilter,
        current_school_id: UUID | None = None,
    ) -> PeriodSlotListResponse:
        """
        List paginated PeriodSlots for a tenant school.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        items, total = self.repository.list_by_school(db, current_school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return PeriodSlotListResponse(
            items=[PeriodSlotResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_period_slot(
        self,
        db: Session,
        slot_id: UUID,
        slot_data: PeriodSlotUpdate,
        current_school_id: UUID | None = None,
    ) -> PeriodSlot:
        """
        Update an existing PeriodSlot.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        slot = self.repository.get_by_id_and_school(db, slot_id, current_school_id)
        if slot is None:
            raise NotFoundException("PeriodSlot", str(slot_id))

        if slot_data.name is not None:
            slot.name = slot_data.name

        if slot_data.period_type is not None:
            slot.period_type = slot_data.period_type

        new_start = slot_data.start_time if slot_data.start_time is not None else slot.start_time
        new_end = slot_data.end_time if slot_data.end_time is not None else slot.end_time
        if new_start >= new_end:
            raise ValidationException("start_time must be before end_time.")
        slot.start_time = new_start
        slot.end_time = new_end

        if slot_data.display_order is not None:
            if slot_data.display_order != slot.display_order:
                if self.repository.exists_by_display_order(
                    db, current_school_id, slot_data.display_order, exclude_id=slot_id
                ):
                    raise AlreadyExistsException(
                        "PeriodSlot display_order", str(slot_data.display_order)
                    )
            slot.display_order = slot_data.display_order

        return self.repository.update(db, slot)

    def delete_period_slot(
        self,
        db: Session,
        slot_id: UUID,
        current_school_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a PeriodSlot.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        slot = self.repository.get_by_id_and_school(db, slot_id, current_school_id)
        if slot is None:
            raise NotFoundException("PeriodSlot", str(slot_id))

        self.repository.delete(db, slot)


period_slot_service = PeriodSlotService()
