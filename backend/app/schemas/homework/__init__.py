"""
Homework and HomeworkSubmission Pydantic schemas.
"""
from app.schemas.homework.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkResponse,
    HomeworkListResponse,
    HomeworkSummaryResponse,
)
from app.schemas.homework.homework_submission import (
    HomeworkSubmissionCreate,
    HomeworkSubmissionGrade,
    HomeworkSubmissionResponse,
    HomeworkSubmissionListResponse,
)

__all__ = [
    "HomeworkCreate",
    "HomeworkUpdate",
    "HomeworkResponse",
    "HomeworkListResponse",
    "HomeworkSummaryResponse",
    "HomeworkSubmissionCreate",
    "HomeworkSubmissionGrade",
    "HomeworkSubmissionResponse",
    "HomeworkSubmissionListResponse",
]
