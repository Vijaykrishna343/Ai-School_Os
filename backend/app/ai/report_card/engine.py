"""
AI Report Card Remarks Engine for Phase 12.6.
Synthesizes subject marks, attendance, and risk indicators into personalized,
qualitative teacher remarks, principal narrative, and actionable recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SubjectMarkItem:
    subject_name: str
    percentage: float
    grade: str
    is_passed: bool = True


@dataclass
class ReportCardRemarksInput:
    student_name: str
    gender: str = "MALE"  # MALE, FEMALE, OTHER
    percentage: float = 0.0
    overall_grade: str = "N/A"
    is_passed: bool = True
    attendance_percentage: float = 100.0
    subject_marks: List[SubjectMarkItem] = field(default_factory=list)
    risk_level: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL, INSUFFICIENT_DATA
    tone: str = "BALANCED"  # BALANCED, ENCOURAGING, DIRECT, ACADEMIC_FOCUS
    detail_level: str = "DETAILED"  # CONCISE, DETAILED


@dataclass
class ReportCardRemarksOutput:
    teacher_remarks: str
    principal_remarks: str
    action_items: List[str]
    strength_subjects: List[str]
    focus_subjects: List[str]
    token_count: int = 180


class AIReportCardRemarksEngine:
    """
    Qualitative evaluation engine for automated report card remarks synthesis.
    """

    VALID_TONES = {"BALANCED", "ENCOURAGING", "DIRECT", "ACADEMIC_FOCUS"}
    VALID_DETAILS = {"CONCISE", "DETAILED"}

    def generate(self, input_data: ReportCardRemarksInput) -> ReportCardRemarksOutput:
        tone = input_data.tone.upper() if input_data.tone else "BALANCED"
        if tone not in self.VALID_TONES:
            tone = "BALANCED"

        detail_level = input_data.detail_level.upper() if input_data.detail_level else "DETAILED"
        if detail_level not in self.VALID_DETAILS:
            detail_level = "DETAILED"

        student_name = input_data.student_name or "The student"
        pronoun_subject = "She" if input_data.gender.upper() == "FEMALE" else "He"
        pronoun_possessive = "her" if input_data.gender.upper() == "FEMALE" else "his"
        pronoun_object = "her" if input_data.gender.upper() == "FEMALE" else "him"

        # 1. Analyze Subject Strengths & Focus Areas
        strengths: List[str] = []
        focus_areas: List[str] = []

        for sub in input_data.subject_marks:
            if sub.percentage >= 75.0 or sub.grade in {"A+", "A", "O", "E"}:
                strengths.append(sub.subject_name)
            elif sub.percentage < 50.0 or not sub.is_passed or sub.grade in {"F", "D", "E"}:
                focus_areas.append(sub.subject_name)

        # 2. Build Teacher Remarks Narrative
        teacher_remarks_parts: List[str] = []

        # Overall Performance Opening
        if input_data.percentage >= 85.0:
            if tone == "ENCOURAGING":
                teacher_remarks_parts.append(f"{student_name} has achieved outstanding academic success this evaluation period, securing an impressive {input_data.percentage:.1f}% overall aggregate.")
            else:
                teacher_remarks_parts.append(f"{student_name} demonstrated high academic competence with an overall score of {input_data.percentage:.1f}% (Grade: {input_data.overall_grade}).")
        elif input_data.percentage >= 65.0:
            if tone == "ENCOURAGING":
                teacher_remarks_parts.append(f"{student_name} has shown commendable progress and steady dedication across subjects, attaining an overall score of {input_data.percentage:.1f}%.")
            else:
                teacher_remarks_parts.append(f"{student_name} maintained satisfactory academic performance with an overall aggregate of {input_data.percentage:.1f}%.")
        else:
            if tone == "ENCOURAGING":
                teacher_remarks_parts.append(f"{student_name} has shown potential and continues to work towards improving academic results ({input_data.percentage:.1f}% overall).")
            else:
                teacher_remarks_parts.append(f"{student_name}'s overall aggregate stands at {input_data.percentage:.1f}%, indicating a need for target academic remediation.")

        # Subject Strengths Commentary
        if strengths:
            str_list = ", ".join(strengths[:3])
            teacher_remarks_parts.append(f"{pronoun_subject} excels particularly in {str_list}, demonstrating strong comprehension and analytical skills.")

        # Focus Areas Commentary
        if focus_areas:
            foc_list = ", ".join(focus_areas[:3])
            teacher_remarks_parts.append(f"Additional practice and structured revision are recommended in {foc_list} to build foundational confidence.")

        # Attendance & Class Engagement Commentary
        if input_data.attendance_percentage >= 90.0:
            teacher_remarks_parts.append(f"With excellent attendance ({input_data.attendance_percentage:.1f}%), {pronoun_subject.lower()} displays active classroom engagement and regularity.")
        elif input_data.attendance_percentage < 75.0:
            teacher_remarks_parts.append(f"Attendance is currently at {input_data.attendance_percentage:.1f}%, which has impacted continuity; consistent attendance will boost academic performance.")

        teacher_remarks = " ".join(teacher_remarks_parts)

        # 3. Build Principal Remarks Narrative
        principal_remarks_parts: List[str] = []
        if input_data.is_passed and input_data.percentage >= 75.0:
            principal_remarks_parts.append(f"A well-deserved result reflecting diligence and discipline. Keep striving for excellence in the upcoming academic term!")
        elif input_data.is_passed:
            principal_remarks_parts.append(f"Satisfactory progress achieved. With consistent effort and focused goal-setting, {student_name} can achieve higher academic standards.")
        else:
            principal_remarks_parts.append(f"Academic support and remedial guidance are recommended to help {student_name} overcome difficulty and achieve essential learning outcomes.")

        if input_data.risk_level in {"HIGH", "CRITICAL"}:
            principal_remarks_parts.append("Special mentor tracking and parent-teacher collaboration are advised.")

        principal_remarks = " ".join(principal_remarks_parts)

        # 4. Action Items for Parents & Student
        action_items: List[str] = []

        if focus_areas:
            action_items.append(f"Schedule daily 30-minute revision sessions for {', '.join(focus_areas[:2])}.")
        else:
            action_items.append("Maintain consistent daily study routines and explore advanced enrichment exercises.")

        if input_data.attendance_percentage < 85.0:
            action_items.append("Ensure regular daily attendance to prevent missed lesson concepts.")
        else:
            action_items.append("Encourage active participation in co-curricular and subject club activities.")

        action_items.append("Review homework assignments weekly with parents and seek timely teacher guidance.")

        total_chars = len(teacher_remarks) + len(principal_remarks) + sum(len(a) for a in action_items)
        token_count = max(60, total_chars // 4)

        return ReportCardRemarksOutput(
            teacher_remarks=teacher_remarks,
            principal_remarks=principal_remarks,
            action_items=action_items[:3],
            strength_subjects=strengths,
            focus_subjects=focus_areas,
            token_count=token_count,
        )


ai_report_card_remarks_engine = AIReportCardRemarksEngine()
