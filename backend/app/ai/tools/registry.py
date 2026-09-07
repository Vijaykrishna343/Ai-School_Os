from __future__ import annotations

import uuid
from typing import Any, Callable
from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException, ForbiddenException
from app.identity.models.user import IdentityUser
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


class ToolDefinition:

    def __init__(
        self,
        name: str,
        description: str,
        required_permission: str,
        handler: Callable[..., dict[str, Any]],
        parameters_schema: dict[str, Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.required_permission = required_permission
        self.handler = handler
        self.parameters_schema = parameters_schema or {}


class AIToolRegistry:
    """
    Whitelisted AI Tool Registry.
    Enforces typed handlers, explicit permissions, and tenant boundary constraints.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register_tool(self, tool_def: ToolDefinition) -> None:
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_permission": t.required_permission,
                "parameters": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    def _has_permission(self, current_user: IdentityUser, required_permission: str) -> bool:
        if not current_user:
            return False
        if getattr(current_user, "is_super_admin", False):
            return True

        user_permissions: set[str] = getattr(current_user, "permissions", set())
        if not user_permissions and hasattr(current_user, "roles") and current_user.roles:
            user_permissions = set()
            for role in current_user.roles:
                if getattr(role, "is_deleted", False):
                    continue
                for perm in getattr(role, "permissions", []):
                    if not getattr(perm, "is_deleted", False):
                        user_permissions.add(perm.name)

        if "*" in user_permissions or required_permission in user_permissions:
            return True

        if "." in required_permission:
            module_name = required_permission.split(".", 1)[0]
            if f"{module_name}.*" in user_permissions:
                return True

        return False

    def list_tools_for_user(self, current_user: IdentityUser) -> list[dict[str, Any]]:
        """
        Returns only the tools that the specified user is authorized to execute.
        """
        permitted_tools = []
        for t in self._tools.values():
            if self._has_permission(current_user, t.required_permission):
                permitted_tools.append({
                    "name": t.name,
                    "description": t.description,
                    "required_permission": t.required_permission,
                    "parameters": t.parameters_schema,
                })
        return permitted_tools

    def execute_tool(
        self,
        tool_name: str,
        db: Session,
        current_user: IdentityUser,
        tool_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tool = self.get_tool(tool_name)
        if not tool:
            raise BadRequestException(f"Requested AI tool '{tool_name}' is not registered or supported.")

        if not current_user or not current_user.school_id:
            raise ForbiddenException("Tenant context required to execute AI tools.")

        if not self._has_permission(current_user, tool.required_permission):
            raise ForbiddenException(f"Missing required permission '{tool.required_permission}' for tool '{tool_name}'.")

        args = tool_args or {}
        return tool.handler(
            db=db,
            school_id=current_user.school_id,
            current_user_school_id=current_user.school_id,
            **args,
        )


# Global tool registry instance
ai_tool_registry = AIToolRegistry()

# Register 0: Baseline School Profile Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_school_summary",
        description="Retrieve basic school profile summary for the current tenant",
        required_permission="school.view",
        handler=get_school_summary,
        parameters_schema={"type": "object", "properties": {}},
    )
)

# Register 1: Academic Risk Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_academic_risk_summary",
        description="Retrieve academic risk score breakdown and flagged student counts for the current tenant",
        required_permission="ai.risk.view",
        handler=get_academic_risk_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "class_id": {"type": "string", "description": "Optional UUID string for filtering by specific school class"},
                "risk_level": {"type": "string", "description": "Optional risk level filter (HIGH, MODERATE, LOW, INSUFFICIENT_DATA)"},
            },
        },
    )
)

# Register 2: Attendance Analytics Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_attendance_analytics",
        description="Retrieve overall student attendance percentages and present/absent/late counts over a lookback window",
        required_permission="attendance.view",
        handler=get_attendance_analytics,
        parameters_schema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback window in days (default: 30, range: 1-90)"},
                "class_id": {"type": "string", "description": "Optional UUID string for filtering by specific school class"},
            },
        },
    )
)

# Register 3: Fee Delinquency Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_fee_delinquency_summary",
        description="Retrieve fee assignment counts, paid vs pending stats, and overdue payment summaries",
        required_permission="fee.view",
        handler=get_fee_delinquency_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional fee status filter (PENDING, PARTIALLY_PAID, PAID, CANCELLED)"},
                "days_overdue": {"type": "integer", "description": "Optional minimum days past due date"},
            },
        },
    )
)

# Register 4: Exam Performance Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_exam_performance_summary",
        description="Retrieve examination marks summary, term pass/fail counts, and subject score distributions",
        required_permission="report_card.view",
        handler=get_exam_performance_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "academic_term_id": {"type": "string", "description": "Optional UUID string for filtering by academic term"},
                "class_id": {"type": "string", "description": "Optional UUID string for filtering by specific school class"},
            },
        },
    )
)

# Register 5: Homework Completion Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_homework_completion_summary",
        description="Retrieve homework assignment creation volume, submission counts, and completion rates over a lookback window",
        required_permission="homework.view",
        handler=get_homework_completion_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback window in days (default: 30, range: 1-90)"},
                "class_id": {"type": "string", "description": "Optional UUID string for filtering by specific school class"},
            },
        },
    )
)

# Register 6: Timetable Schedule Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_timetable_schedule_summary",
        description="Retrieve active class timetable period entry counts, unique scheduled teachers, and daily schedule totals",
        required_permission="timetable.view",
        handler=get_timetable_schedule_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "day_of_week": {"type": "string", "description": "Optional day of week filter (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY)"},
                "teacher_id": {"type": "string", "description": "Optional UUID string for filtering by specific teacher"},
            },
        },
    )
)

# Register 7: Staff Leave Summary Tool
ai_tool_registry.register_tool(
    ToolDefinition(
        name="get_staff_leave_summary",
        description="Retrieve staff leave request totals, approved/pending/rejected counts, approved leave days, and staff currently on leave",
        required_permission="staff_leave.report.view",
        handler=get_staff_leave_summary,
        parameters_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional leave status filter (PENDING, APPROVED, REJECTED, CANCELLED)"},
                "days": {"type": "integer", "description": "Lookback window in days (default: 30, range: 1-90)"},
            },
        },
    )
)
