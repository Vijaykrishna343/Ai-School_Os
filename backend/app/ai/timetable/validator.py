from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from app.ai.timetable.solver import (
    TimetableSolverInput,
    TimetableAssignmentOutput,
)


@dataclass
class ValidationReport:
    is_valid: bool
    hard_violations: list[str]
    soft_penalties: dict[str, int]
    summary_stats: dict[str, Any]


class TimetableValidator:
    """
    Independent, deterministic validator for AI-generated timetables.
    Verifies zero hard constraint violations prior to approval/publishing.
    """

    def validate(
        self,
        solver_input: TimetableSolverInput,
        assignments: list[TimetableAssignmentOutput],
    ) -> ValidationReport:
        hard_violations: list[str] = []
        soft_penalties: dict[str, int] = {}

        # Lookup structures
        teacher_unavail_set = {
            (u.teacher_id, u.day_of_week, u.period_slot_id) for u in solver_input.teacher_unavailabilities
        }
        section_unavail_set = {
            (u.section_id, u.day_of_week, u.period_slot_id) for u in solver_input.section_unavailabilities
        }
        classroom_lab_map = {r.id: r.is_lab for r in solver_input.classrooms}

        # Track overlaps
        teacher_slot_map: dict[tuple[str, str, str], list[TimetableAssignmentOutput]] = {}
        section_slot_map: dict[tuple[str, str, str], list[TimetableAssignmentOutput]] = {}
        room_slot_map: dict[tuple[str, str, str], list[TimetableAssignmentOutput]] = {}
        subject_quota_tracker: dict[tuple[str, str], int] = {}

        for a in assignments:
            # 1. Teacher overlap check
            t_key = (a.teacher_id, a.day_of_week, a.period_slot_id)
            teacher_slot_map.setdefault(t_key, []).append(a)

            # 2. Section overlap check
            s_key = (a.section_id, a.day_of_week, a.period_slot_id)
            section_slot_map.setdefault(s_key, []).append(a)

            # 3. Room overlap check
            if a.classroom_id:
                r_key = (a.classroom_id, a.day_of_week, a.period_slot_id)
                room_slot_map.setdefault(r_key, []).append(a)

            # 4. Subject quota tracking
            sq_key = (a.section_id, a.subject_id)
            subject_quota_tracker[sq_key] = subject_quota_tracker.get(sq_key, 0) + 1

            # 5. Teacher unavailability check
            if (a.teacher_id, a.day_of_week, a.period_slot_id) in teacher_unavail_set:
                hard_violations.append(
                    f"Teacher '{a.teacher_id}' assigned to unavailable slot '{a.day_of_week} {a.period_slot_id}'."
                )

            # 6. Section unavailability check
            if (a.section_id, a.day_of_week, a.period_slot_id) in section_unavail_set:
                hard_violations.append(
                    f"Section '{a.section_id}' assigned to unavailable slot '{a.day_of_week} {a.period_slot_id}'."
                )

        # Evaluate Teacher Overlaps
        for (t_id, day, slot_id), entries in teacher_slot_map.items():
            if len(entries) > 1:
                hard_violations.append(
                    f"Teacher '{t_id}' double-booked on {day} slot {slot_id} across {len(entries)} sections."
                )

        # Evaluate Section Overlaps
        for (sec_id, day, slot_id), entries in section_slot_map.items():
            if len(entries) > 1:
                hard_violations.append(
                    f"Section '{sec_id}' double-booked on {day} slot {slot_id} with {len(entries)} subjects."
                )

        # Evaluate Room Overlaps
        for (room_id, day, slot_id), entries in room_slot_map.items():
            if len(entries) > 1:
                hard_violations.append(
                    f"Classroom '{room_id}' double-booked on {day} slot {slot_id} by {len(entries)} sections."
                )

        # Evaluate Subject Quota Violations
        for req in solver_input.curriculum_requirements:
            sq_key = (req.section_id, req.subject_id)
            actual_count = subject_quota_tracker.get(sq_key, 0)
            if actual_count != req.required_weekly_periods:
                hard_violations.append(
                    f"Subject quota mismatch for section '{req.section_id}' subject '{req.subject_id}': "
                    f"Required {req.required_weekly_periods}, got {actual_count}."
                )

        is_valid = len(hard_violations) == 0

        summary_stats = {
            "total_assignments": len(assignments),
            "hard_violations_count": len(hard_violations),
            "teacher_double_bookings": sum(1 for entries in teacher_slot_map.values() if len(entries) > 1),
            "section_double_bookings": sum(1 for entries in section_slot_map.values() if len(entries) > 1),
            "room_double_bookings": sum(1 for entries in room_slot_map.values() if len(entries) > 1),
        }

        return ValidationReport(
            is_valid=is_valid,
            hard_violations=hard_violations,
            soft_penalties=soft_penalties,
            summary_stats=summary_stats,
        )


timetable_validator = TimetableValidator()
