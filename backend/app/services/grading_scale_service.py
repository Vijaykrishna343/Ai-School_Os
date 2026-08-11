from math import ceil
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.repositories.grading.grade_scale_repository import (
    GradeScaleRepository,
    grade_scale_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.schemas.grading.grade_scale import (
    GradeMatchResponse,
    GradeScaleCreate,
    GradeScaleEntryCreate,
    GradeScaleEntryResponse,
    GradeScaleFilter,
    GradeScaleListResponse,
    GradeScaleResponse,
    GradeScaleUpdate,
)

logger = get_logger(__name__)


class GradeScaleService:
    """
    Business logic service for GradeScale and GradeScaleEntry operations.
    """

    def __init__(
        self,
        repository: GradeScaleRepository = grade_scale_repository,
        school_repo: SchoolRepository = school_repository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repo

    # ------------------------------------------------------------------
    # Domain Validation Helpers
    # ------------------------------------------------------------------

    def validate_entries(
        self,
        entries: list[GradeScaleEntryCreate] | list[GradeScaleEntry],
    ) -> None:
        """
        Validates grade scale entries:
        - Percentage bounds (0 <= min <= max <= 100)
        - Non-negative grade_point
        - Unique grade_code inside the scale
        - No range overlaps between grade bands
        """
        seen_codes: set[str] = set()

        # Convert to uniform objects for evaluation
        entry_items: list[tuple[str, Decimal, Decimal, Decimal]] = []

        for entry in entries:
            code = (
                entry.grade_code.strip().upper()
                if isinstance(entry, (GradeScaleEntryCreate, GradeScaleEntry))
                else str(entry["grade_code"]).strip().upper()
            )
            min_pct = Decimal(str(entry.min_percentage))
            max_pct = Decimal(str(entry.max_percentage))
            gp = Decimal(str(entry.grade_point))

            if min_pct < 0 or min_pct > 100:
                raise ValidationException(
                    f"min_percentage for grade '{code}' must be between 0 and 100."
                )

            if max_pct < 0 or max_pct > 100:
                raise ValidationException(
                    f"max_percentage for grade '{code}' must be between 0 and 100."
                )

            if min_pct > max_pct:
                raise ValidationException(
                    f"min_percentage ({min_pct}) cannot exceed max_percentage ({max_pct}) for grade '{code}'."
                )

            if gp < 0:
                raise ValidationException(
                    f"grade_point for grade '{code}' cannot be negative."
                )

            if code in seen_codes:
                raise ValidationException(
                    f"Duplicate grade_code '{code}' found in grade scale."
                )
            seen_codes.add(code)

            entry_items.append((code, min_pct, max_pct, gp))

        # Check for range overlaps
        n = len(entry_items)
        for i in range(n):
            code_a, min_a, max_a, _ = entry_items[i]
            for j in range(i + 1, n):
                code_b, min_b, max_b, _ = entry_items[j]

                # Overlap occurs if max(min_a, min_b) <= min(max_a, max_b)
                if max(min_a, min_b) <= min(max_a, max_b):
                    raise ValidationException(
                        f"Overlapping grade bands detected between '{code_a}' ({min_a}-{max_a}) and '{code_b}' ({min_b}-{max_b})."
                    )

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------

    def create_grade_scale(
        self,
        db: Session,
        scale_data: GradeScaleCreate,
        current_school_id: UUID | None = None,
    ) -> GradeScale:
        """
        Create a new GradeScale and its associated entries.
        Enforces tenant isolation, name uniqueness, range non-overlap, and single default per school.
        """
        if not current_school_id:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )

        school = self.school_repository.get(db, current_school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(current_school_id))

        if self.repository.exists_by_name(db, current_school_id, scale_data.name):
            raise AlreadyExistsException("GradeScale", scale_data.name)

        self.validate_entries(scale_data.entries)

        if scale_data.is_default:
            self.repository.unset_default_for_school(db, current_school_id)

        scale = GradeScale(
            school_id=current_school_id,
            name=scale_data.name.strip(),
            description=scale_data.description,
            is_default=scale_data.is_default,
        )

        for entry_data in scale_data.entries:
            entry = GradeScaleEntry(
                grade_code=entry_data.grade_code.strip().upper(),
                min_percentage=entry_data.min_percentage,
                max_percentage=entry_data.max_percentage,
                grade_point=entry_data.grade_point,
                description=entry_data.description,
                is_pass=entry_data.is_pass,
            )
            scale.entries.append(entry)

        try:
            created = self.repository.create(db, scale)
            logger.info(
                "GradeScale '%s' created successfully with ID: %s",
                created.name,
                created.id,
            )
            return created
        except IntegrityError as exc:
            db.rollback()
            logger.error("Integrity error creating GradeScale: %s", exc)
            raise AlreadyExistsException(
                "GradeScale", scale_data.name
            ) from exc

    def get_grade_scale(
        self,
        db: Session,
        scale_id: UUID,
        current_school_id: UUID | None = None,
    ) -> GradeScale:
        """
        Retrieve an active GradeScale by ID for the tenant school.
        """
        if not current_school_id:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )

        scale = self.repository.get_by_id_and_school(
            db, scale_id, current_school_id
        )
        if scale is None or scale.is_deleted:
            raise NotFoundException("GradeScale", str(scale_id))

        return scale

    def get_default_grade_scale(
        self,
        db: Session,
        current_school_id: UUID | None = None,
    ) -> GradeScale:
        """
        Retrieve the active default GradeScale for the tenant school.
        """
        if not current_school_id:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )

        scale = self.repository.get_default_by_school(db, current_school_id)
        if scale is None or scale.is_deleted:
            raise NotFoundException(
                "Default GradeScale", str(current_school_id)
            )

        return scale

    def list_grade_scales(
        self,
        db: Session,
        filters: GradeScaleFilter,
        current_school_id: UUID | None = None,
    ) -> GradeScaleListResponse:
        """
        List paginated GradeScales for the tenant school.
        """
        if not current_school_id:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )

        items, total = self.repository.list_by_school(
            db, current_school_id, filters
        )
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return GradeScaleListResponse(
            items=[GradeScaleResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_grade_scale(
        self,
        db: Session,
        scale_id: UUID,
        scale_data: GradeScaleUpdate,
        current_school_id: UUID | None = None,
    ) -> GradeScale:
        """
        Update an existing GradeScale and optional entries.
        """
        scale = self.get_grade_scale(db, scale_id, current_school_id)
        update_dict = scale_data.model_dump(exclude_unset=True)

        if "name" in update_dict and update_dict["name"] is not None:
            new_name = update_dict["name"].strip()
            if new_name != scale.name and self.repository.exists_by_name(
                db, current_school_id, new_name, exclude_id=scale_id
            ):
                raise AlreadyExistsException("GradeScale", new_name)
            scale.name = new_name

        if "description" in update_dict:
            scale.description = update_dict["description"]

        if update_dict.get("is_default") is True:
            if not scale.is_default:
                self.repository.unset_default_for_school(
                    db, current_school_id, exclude_id=scale_id
                )
            scale.is_default = True
        elif update_dict.get("is_default") is False:
            scale.is_default = False

        if "entries" in update_dict and update_dict["entries"] is not None:
            new_entries_data: list[GradeScaleEntryCreate] = update_dict["entries"]
            self.validate_entries(new_entries_data)

            # Soft delete existing entries
            for existing in scale.entries:
                existing.soft_delete()

            scale.entries.clear()

            for entry_data in new_entries_data:
                entry = GradeScaleEntry(
                    grade_scale_id=scale.id,
                    grade_code=entry_data.grade_code.strip().upper(),
                    min_percentage=entry_data.min_percentage,
                    max_percentage=entry_data.max_percentage,
                    grade_point=entry_data.grade_point,
                    description=entry_data.description,
                    is_pass=entry_data.is_pass,
                )
                scale.entries.append(entry)

        try:
            updated = self.repository.update(db, scale)
            logger.info("GradeScale ID: %s updated successfully", scale_id)
            return updated
        except IntegrityError as exc:
            db.rollback()
            logger.error("Integrity error updating GradeScale: %s", exc)
            raise AlreadyExistsException(
                "GradeScale", scale.name
            ) from exc

    def delete_grade_scale(
        self,
        db: Session,
        scale_id: UUID,
        current_school_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a GradeScale and all its associated child entries.
        """
        scale = self.get_grade_scale(db, scale_id, current_school_id)

        for entry in scale.entries:
            if current_user_id:
                entry.deleted_by_user_id = current_user_id
            entry.soft_delete()

        if current_user_id:
            scale.deleted_by_user_id = current_user_id
        self.repository.delete(db, scale)
        logger.info("GradeScale ID: %s soft deleted successfully", scale_id)

    # ------------------------------------------------------------------
    # Grade Calculation / Matching
    # ------------------------------------------------------------------

    def calculate_grade(
        self,
        db: Session,
        percentage: Decimal,
        scale_id: UUID | None = None,
        current_school_id: UUID | None = None,
    ) -> GradeMatchResponse:
        """
        Match a percentage score to a GradeScaleEntry.
        If scale_id is omitted, uses the school's default GradeScale.
        """
        if scale_id is not None:
            scale = self.get_grade_scale(db, scale_id, current_school_id)
        else:
            scale = self.get_default_grade_scale(db, current_school_id)

        matched: GradeScaleEntry | None = None

        for entry in scale.entries:
            if not entry.is_deleted:
                if entry.min_percentage <= percentage <= entry.max_percentage:
                    matched = entry
                    break

        matched_schema = (
            GradeScaleEntryResponse.model_validate(matched)
            if matched is not None
            else None
        )

        return GradeMatchResponse(
            percentage=percentage,
            matched_entry=matched_schema,
        )


grade_scale_service = GradeScaleService(
    repository=grade_scale_repository,
    school_repo=school_repository,
)
