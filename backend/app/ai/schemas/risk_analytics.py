"""
Pydantic schemas for Phase 12.4 Explainable Student Academic Risk & Attendance Analytics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class StudentRiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    student_id: uuid.UUID
    section_id: uuid.UUID
    risk_level: str
    risk_score: Optional[Decimal] = None
    confidence: Decimal
    scoring_version: str
    attendance_percentage: Optional[Decimal] = None
    attendance_trend_delta: Optional[Decimal] = None
    exam_average_percentage: Optional[Decimal] = None
    exam_trend_delta: Optional[Decimal] = None
    homework_submission_rate: Optional[Decimal] = None
    failed_subjects_count: int
    data_sufficiency_status: str
    sample_counts: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    recommended_interventions: List[str]
    assessed_at: datetime


class SectionRiskSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: str
    total_students: int
    risk_distribution: Dict[str, int]


class SchoolRiskSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_id: str
    total_assessed: int
    risk_distribution: Dict[str, int]
