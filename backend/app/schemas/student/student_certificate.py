from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.student.student_certificate import CertificateType


class StudentCertificateCreateTC(BaseModel):
    reason_for_leaving: str = Field(..., min_length=2, max_length=500)
    conduct: str = Field(default="Good", max_length=100)
    issued_date: date = Field(default_factory=date.today)
    update_student_status: bool = Field(default=True)


class StudentCertificateCreateBonafide(BaseModel):
    purpose: str = Field(..., min_length=2, max_length=255)
    conduct: str = Field(default="Good", max_length=100)
    issued_date: date = Field(default_factory=date.today)


class StudentCertificateResponse(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: str | None = None
    admission_number: str | None = None
    roll_number: str | None = None
    school_class_name: str | None = None
    section_name: str | None = None
    parent_name: str | None = None
    certificate_type: CertificateType
    certificate_number: str
    issued_date: date
    purpose: str | None = None
    reason_for_leaving: str | None = None
    conduct: str | None = None
    issued_by_name: str | None = None

    model_config = {"from_attributes": True}


class StudentCertificateListResponse(BaseModel):
    items: list[StudentCertificateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
