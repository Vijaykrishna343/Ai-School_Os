from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import PromotionDecision


class ProgressionPreviewRequest(BaseModel):
    """
    Request payload for academic year progression preview calculation.
    """

    target_academic_year_id: UUID
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class StudentProgressionPreviewItem(BaseModel):
    """
    Evaluated progression outcome preview for a single student.
    """

    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    admission_number: str
    student_name: str
    current_academic_year_id: UUID
    current_class_id: UUID
    current_class_name: str
    current_section_id: UUID
    current_section_name: str
    current_roll_number: str | None = None
    decision: PromotionDecision
    target_class_id: UUID | None = None
    target_class_name: str | None = None
    target_section_id: UUID | None = None
    target_section_name: str | None = None
    proposed_roll_number: str | None = None
    allocation_status: str
    reason: str
    warnings: list[str] = Field(default_factory=list)


class ProgressionPreviewSummary(BaseModel):
    """
    Summary counts for academic year progression preview calculation.
    """

    model_config = ConfigDict(from_attributes=True)

    source_academic_year_id: UUID
    target_academic_year_id: UUID
    total_students_evaluated: int
    promoted_count: int
    graduated_count: int
    retained_count: int
    blocked_count: int
    excluded_count: int
    warning_count: int


class ProgressionPreviewResponse(BaseModel):
    """
    Paginated response payload for academic progression preview.
    """

    model_config = ConfigDict(from_attributes=True)

    execution_plan_hash: str
    summary: ProgressionPreviewSummary
    items: list[StudentProgressionPreviewItem]
    total: int
    page: int
    page_size: int
    total_pages: int

