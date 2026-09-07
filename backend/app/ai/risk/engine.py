"""
Deterministic Explainable Student Risk Engine (deterministic-v1) for Phase 12.4.
Calculates student risk 100% from educational signals.

Financial delinquency is EXCLUDED from academic risk calculation.
Missing history results in INSUFFICIENT_DATA status rather than false performance penalties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, List, Dict, Optional, Tuple


@dataclass
class StudentEducationalData:
    student_id: str
    section_id: str
    academic_year_id: str
    
    # Sample counts
    attendance_count: int = 0
    recent_attendance_count: int = 0
    previous_attendance_count: int = 0
    
    attendance_present_count: int = 0
    recent_present_count: int = 0
    previous_present_count: int = 0
    
    exam_results_count: int = 0
    recent_exam_average: Optional[float] = None  # Percentage 0 - 100
    previous_exam_average: Optional[float] = None
    failed_subjects_count: int = 0
    
    total_homework_count: int = 0
    submitted_homework_count: int = 0


@dataclass
class RiskEvaluationOutput:
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL, INSUFFICIENT_DATA
    risk_score: Optional[Decimal]  # 0.00 to 1.00 or None if INSUFFICIENT_DATA
    confidence: Decimal  # 0.00 to 1.00
    scoring_version: str = "deterministic-v1"
    
    attendance_percentage: Optional[Decimal] = None
    attendance_trend_delta: Optional[Decimal] = None
    exam_average_percentage: Optional[Decimal] = None
    exam_trend_delta: Optional[Decimal] = None
    homework_submission_rate: Optional[Decimal] = None
    failed_subjects_count: int = 0
    
    data_sufficiency_status: str = "INSUFFICIENT"  # FULL, PARTIAL, INSUFFICIENT
    sample_counts: Dict[str, int] = field(default_factory=dict)
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    recommended_interventions: List[str] = field(default_factory=list)


class DeterministicRiskEngine:
    """
    Explainable, versioned risk analytics engine.
    
    Weighting Parameters (when FULL data exists):
    - Attendance: 40%
    - Exam Average & Failures: 40%
    - Homework Completion Rate: 20%
    """

    MIN_ATTENDANCE_SAMPLES_PARTIAL = 5
    MIN_ATTENDANCE_SAMPLES_FULL = 14
    MIN_EXAM_SAMPLES_PARTIAL = 1
    MIN_EXAM_SAMPLES_FULL = 3

    def evaluate(self, data: StudentEducationalData) -> RiskEvaluationOutput:
        sample_counts = {
            "attendance_records": data.attendance_count,
            "exam_results": data.exam_results_count,
            "homework_assignments": data.total_homework_count,
        }

        # 1. Determine Data Sufficiency Status
        has_min_attendance = data.attendance_count >= self.MIN_ATTENDANCE_SAMPLES_PARTIAL
        has_min_exams = data.exam_results_count >= self.MIN_EXAM_SAMPLES_PARTIAL
        
        if not has_min_attendance and not has_min_exams:
            return RiskEvaluationOutput(
                risk_level="INSUFFICIENT_DATA",
                risk_score=None,
                confidence=Decimal("0.10"),
                scoring_version="deterministic-v1",
                data_sufficiency_status="INSUFFICIENT",
                sample_counts=sample_counts,
                risk_factors=[{
                    "factor": "DATA_AVAILABILITY",
                    "impact": "NEUTRAL",
                    "value": "INSUFFICIENT_HISTORY",
                    "details": f"Student has insufficient academic history ({data.attendance_count} attendance days, {data.exam_results_count} exam results). Risk score cannot be calculated reliably.",
                }],
                recommended_interventions=["Monitor academic onboarding and allow 2-3 weeks for baseline record generation."],
            )

        sufficiency = "FULL" if (data.attendance_count >= self.MIN_ATTENDANCE_SAMPLES_FULL and data.exam_results_count >= self.MIN_EXAM_SAMPLES_FULL) else "PARTIAL"

        risk_factors: List[Dict[str, Any]] = []
        recommended_interventions: List[str] = []
        
        total_weight = Decimal("0.00")
        weighted_risk_sum = Decimal("0.00")

        # 2. Attendance Factor Analysis
        att_pct_dec: Optional[Decimal] = None
        att_delta_dec: Optional[Decimal] = None

        if data.attendance_count > 0:
            att_pct = (data.attendance_present_count / data.attendance_count) * 100.0
            att_pct_dec = Decimal(str(round(att_pct, 2)))

            # Risk Component for Attendance (100% -> 0.0 risk, 75% -> 0.25 risk, <75% -> steep risk)
            if att_pct >= 90.0:
                att_risk = Decimal("0.00")
            elif att_pct >= 75.0:
                att_risk = Decimal(str(round((90.0 - att_pct) / 60.0, 2)))  # 75% -> 0.25
            else:
                att_risk = Decimal(str(round(0.25 + ((75.0 - att_pct) / 75.0) * 0.75, 2)))  # <75% -> up to 1.0

            # Trend calculation
            if data.recent_attendance_count > 0 and data.previous_attendance_count > 0:
                recent_pct = (data.recent_present_count / data.recent_attendance_count) * 100.0
                prev_pct = (data.previous_present_count / data.previous_attendance_count) * 100.0
                att_delta = recent_pct - prev_pct
                att_delta_dec = Decimal(str(round(att_delta, 2)))

                if att_delta < -10.0:
                    att_risk = min(Decimal("1.00"), att_risk + Decimal("0.15"))
                    risk_factors.append({
                        "factor": "ATTENDANCE_TREND",
                        "impact": "NEGATIVE",
                        "value": f"{att_delta_dec:+}%",
                        "details": "Recent attendance shows a significant declining trend.",
                    })
                    recommended_interventions.append("Initiate counselor follow-up regarding recent attendance decline.")

            att_weight = Decimal("0.40") if has_min_attendance else Decimal("0.20")
            total_weight += att_weight
            weighted_risk_sum += att_risk * att_weight

            if att_pct < 75.0:
                risk_factors.append({
                    "factor": "ATTENDANCE_LEVEL",
                    "impact": "HIGH_NEGATIVE",
                    "value": f"{att_pct_dec}%",
                    "details": "Attendance is below mandatory 75% threshold.",
                })
                recommended_interventions.append("Schedule parent-teacher conference for attendance improvement plan.")
        
        # 3. Exam Factor Analysis
        exam_avg_dec: Optional[Decimal] = None
        exam_delta_dec: Optional[Decimal] = None

        if data.exam_results_count > 0 and data.recent_exam_average is not None:
            exam_avg_dec = Decimal(str(round(data.recent_exam_average, 2)))

            # Exam Risk Component
            if data.recent_exam_average >= 75.0:
                exam_risk = Decimal("0.00")
            elif data.recent_exam_average >= 40.0:
                exam_risk = Decimal(str(round((75.0 - data.recent_exam_average) / 70.0, 2)))
            else:
                exam_risk = Decimal(str(round(0.50 + ((40.0 - data.recent_exam_average) / 40.0) * 0.50, 2)))

            # Failed subjects penalty
            if data.failed_subjects_count > 0:
                fail_penalty = Decimal(str(min(0.40, data.failed_subjects_count * 0.15)))
                exam_risk = min(Decimal("1.00"), exam_risk + fail_penalty)
                risk_factors.append({
                    "factor": "FAILED_SUBJECTS",
                    "impact": "HIGH_NEGATIVE",
                    "value": str(data.failed_subjects_count),
                    "details": f"Student has failing grades in {data.failed_subjects_count} subject(s).",
                })
                recommended_interventions.append("Arrange subject-specific remedial tutoring support.")

            # Exam Trend
            if data.previous_exam_average is not None:
                exam_delta = data.recent_exam_average - data.previous_exam_average
                exam_delta_dec = Decimal(str(round(exam_delta, 2)))

                if exam_delta < -10.0:
                    exam_risk = min(Decimal("1.00"), exam_risk + Decimal("0.15"))
                    risk_factors.append({
                        "factor": "EXAM_TREND",
                        "impact": "NEGATIVE",
                        "value": f"{exam_delta_dec:+}%",
                        "details": "Exam average performance dropped compared to previous assessment period.",
                    })
                elif exam_delta > 10.0:
                    exam_risk = max(Decimal("0.00"), exam_risk - Decimal("0.10"))
                    risk_factors.append({
                        "factor": "EXAM_TREND",
                        "impact": "POSITIVE",
                        "value": f"{exam_delta_dec:+}%",
                        "details": "Academic marks show positive improvement trend.",
                    })

            exam_weight = Decimal("0.40") if has_min_exams else Decimal("0.20")
            total_weight += exam_weight
            weighted_risk_sum += exam_risk * exam_weight

        # 4. Homework Factor Analysis
        hw_rate_dec: Optional[Decimal] = None
        if data.total_homework_count > 0:
            hw_rate = (data.submitted_homework_count / data.total_homework_count) * 100.0
            hw_rate_dec = Decimal(str(round(hw_rate, 2)))

            if hw_rate < 60.0:
                hw_risk = Decimal(str(round((100.0 - hw_rate) / 100.0, 2)))
                hw_weight = Decimal("0.20")
                total_weight += hw_weight
                weighted_risk_sum += hw_risk * hw_weight

                risk_factors.append({
                    "factor": "HOMEWORK_COMPLETION",
                    "impact": "NEGATIVE",
                    "value": f"{hw_rate_dec}%",
                    "details": "Low homework submission completion rate.",
                })
                recommended_interventions.append("Issue homework submission check-in with Class Teacher.")

        # 5. Normalize Risk Score & Clamping
        if total_weight > Decimal("0.00"):
            raw_score = weighted_risk_sum / total_weight
        else:
            raw_score = Decimal("0.00")

        clamped_score = max(Decimal("0.00"), min(Decimal("1.00"), raw_score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)))

        # 6. Map Risk Level
        if clamped_score <= Decimal("0.25"):
            level = "LOW"
        elif clamped_score <= Decimal("0.50"):
            level = "MEDIUM"
        elif clamped_score <= Decimal("0.75"):
            level = "HIGH"
        else:
            level = "CRITICAL"

        # Confidence Calculation
        if sufficiency == "FULL":
            confidence = Decimal("0.95")
        elif sufficiency == "PARTIAL":
            confidence = Decimal("0.70")
        else:
            confidence = Decimal("0.40")

        if not recommended_interventions:
            recommended_interventions.append("Maintain current academic trajectory and monitor periodic assessments.")

        return RiskEvaluationOutput(
            risk_level=level,
            risk_score=clamped_score,
            confidence=confidence,
            scoring_version="deterministic-v1",
            attendance_percentage=att_pct_dec,
            attendance_trend_delta=att_delta_dec,
            exam_average_percentage=exam_avg_dec,
            exam_trend_delta=exam_delta_dec,
            homework_submission_rate=hw_rate_dec,
            failed_subjects_count=data.failed_subjects_count,
            data_sufficiency_status=sufficiency,
            sample_counts=sample_counts,
            risk_factors=risk_factors,
            recommended_interventions=recommended_interventions,
        )


deterministic_risk_engine = DeterministicRiskEngine()
