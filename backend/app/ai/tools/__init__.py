from app.ai.tools.registry import AIToolRegistry, ToolDefinition, ai_tool_registry
from app.ai.tools.school_tools import get_school_summary
from app.ai.tools.domain_tools import (
    get_academic_risk_summary,
    get_attendance_analytics,
    get_fee_delinquency_summary,
    get_exam_performance_summary,
    get_homework_completion_summary,
    get_timetable_schedule_summary,
    get_staff_leave_summary,
)

__all__ = [
    "AIToolRegistry",
    "ToolDefinition",
    "ai_tool_registry",
    "get_school_summary",
    "get_academic_risk_summary",
    "get_attendance_analytics",
    "get_fee_delinquency_summary",
    "get_exam_performance_summary",
    "get_homework_completion_summary",
    "get_timetable_schedule_summary",
    "get_staff_leave_summary",
]
