from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClassProgressionRuleBase(BaseModel):
    """
    Shared base fields for ClassProgressionRule.
    """

    source_class_id: UUID
    target_class_id: UUID | None = None
    is_terminal: bool = False
    description: str | None = Field(default=None, max_length=255)


class ClassProgressionRuleCreate(ClassProgressionRuleBase):
    """
    Request body for creating a ClassProgressionRule.
    """

    @model_validator(mode="after")
    def validate_terminal_target_consistency(self) -> "ClassProgressionRuleCreate":
        if self.is_terminal:
            if self.target_class_id is not None:
                raise ValueError("Terminal progression rules must not specify a target class.")
        else:
            if self.target_class_id is None:
                raise ValueError("Non-terminal progression rules must specify a target class.")

        if self.target_class_id and self.source_class_id == self.target_class_id:
            raise ValueError("Source class and target class cannot be the same.")

        return self


class ClassProgressionRuleUpdate(BaseModel):
    """
    Request body for updating a ClassProgressionRule.
    """

    target_class_id: UUID | None = None
    is_terminal: bool | None = None
    description: str | None = Field(default=None, max_length=255)


class ClassProgressionRuleResponse(BaseModel):
    """
    API response representation for ClassProgressionRule.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    source_class_id: UUID
    target_class_id: UUID | None = None
    is_terminal: bool
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class ClassProgressionRuleFilter(BaseModel):
    """
    Query filter parameters for listing ClassProgressionRules.
    """

    source_class_id: UUID | None = None
    target_class_id: UUID | None = None
    is_terminal: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ClassProgressionRuleListResponse(BaseModel):
    """
    Paginated API response for ClassProgressionRules.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[ClassProgressionRuleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
