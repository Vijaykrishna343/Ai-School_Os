from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.schemas.student.progression_preview_schema import (
    ProgressionPreviewRequest,
    ProgressionPreviewResponse,
)
from app.services.student.progression_planner import (
    ProgressionPlanner,
    progression_planner,
)

logger = get_logger(__name__)


class ProgressionPreviewService:
    """
    READ-ONLY Academic Progression Preview Engine.

    Delegates progression plan calculation to the shared ProgressionPlanner domain component
    and formats the paginated preview response for clients.

    STRICT GUARANTEE: Never mutates database entities or roll number sequences.
    """

    def __init__(
        self,
        planner: ProgressionPlanner = progression_planner,
    ) -> None:
        self.planner = planner

    def generate_preview(
        self,
        db: Session,
        source_academic_year_id: UUID,
        request: ProgressionPreviewRequest,
        current_school_id: UUID,
    ) -> ProgressionPreviewResponse:
        """
        Generate progression preview for a school's academic year transition by invoking ProgressionPlanner.
        """
        plan = self.planner.calculate_plan(
            db=db,
            source_academic_year_id=source_academic_year_id,
            target_academic_year_id=request.target_academic_year_id,
            current_school_id=current_school_id,
        )

        page = request.page
        page_size = request.page_size
        total_evaluated = plan.summary.total_students_evaluated
        total_pages = ceil(total_evaluated / page_size) if total_evaluated > 0 else 0
        offset = (page - 1) * page_size
        paged_items = plan.evaluated_items[offset : offset + page_size]

        return ProgressionPreviewResponse(
            execution_plan_hash=plan.execution_plan_hash,
            summary=plan.summary,
            items=paged_items,
            total=total_evaluated,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


progression_preview_service = ProgressionPreviewService()
