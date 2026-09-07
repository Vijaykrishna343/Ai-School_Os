from __future__ import annotations

import time
from typing import Any
from dataclasses import dataclass, field
from ortools.sat.python import cp_model

from app.common.logger.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CurriculumRequirementInput:
    section_id: str
    subject_id: str
    teacher_id: str
    required_weekly_periods: int
    school_class_id: str = ""


@dataclass
class TeacherUnavailabilityInput:
    teacher_id: str
    day_of_week: str
    period_slot_id: str


@dataclass
class SectionUnavailabilityInput:
    section_id: str
    day_of_week: str
    period_slot_id: str


@dataclass
class ClassroomInput:
    id: str
    name: str
    is_lab: bool = False


@dataclass
class PeriodSlotInput:
    id: str
    name: str
    display_order: int


@dataclass
class TimetableSolverInput:
    school_id: str
    academic_year_id: str
    days: list[str]
    period_slots: list[PeriodSlotInput]
    classrooms: list[ClassroomInput]
    curriculum_requirements: list[CurriculumRequirementInput]
    teacher_unavailabilities: list[TeacherUnavailabilityInput] = field(default_factory=list)
    section_unavailabilities: list[SectionUnavailabilityInput] = field(default_factory=list)
    timeout_seconds: float = 30.0


@dataclass
class TimetableAssignmentOutput:
    section_id: str
    school_class_id: str
    subject_id: str
    teacher_id: str
    classroom_id: str | None
    period_slot_id: str
    day_of_week: str


@dataclass
class TimetableSolverResult:
    status: str  # FEASIBLE, OPTIMAL, INFEASIBLE, MODEL_INVALID, UNKNOWN
    solver_duration_ms: int
    objective_score: int
    assignments: list[TimetableAssignmentOutput]
    constraint_stats: dict[str, Any]
    error_message: str | None = None


class TimetableCPSATSolver:
    """
    Google OR-Tools CP-SAT Timetable Constraint Solver.
    Constructs an exact integer programming model enforcing hard operational constraints
    and soft quality metrics.
    """

    def solve(self, solver_input: TimetableSolverInput) -> TimetableSolverResult:
        start_time = time.time()
        model = cp_model.CpModel()

        days = solver_input.days
        slots = solver_input.period_slots
        classrooms = solver_input.classrooms
        reqs = solver_input.curriculum_requirements

        if not reqs or not slots or not days:
            return TimetableSolverResult(
                status="MODEL_INVALID",
                solver_duration_ms=int((time.time() - start_time) * 1000),
                objective_score=0,
                assignments=[],
                constraint_stats={"error": "Missing curriculum requirements, slots, or days"},
                error_message="Insufficient data to construct timetable solver model.",
            )

        # Lookup structures
        teacher_unavail_set = {
            (u.teacher_id, u.day_of_week, u.period_slot_id) for u in solver_input.teacher_unavailabilities
        }
        section_unavail_set = {
            (u.section_id, u.day_of_week, u.period_slot_id) for u in solver_input.section_unavailabilities
        }

        # Decision Variables: x[req_idx, room_idx_or_none, slot_idx, day_idx] -> Bool
        x = {}
        vars_by_req = {i: [] for i in range(len(reqs))}
        vars_by_section_slot_day = {}
        vars_by_teacher_slot_day = {}
        vars_by_room_slot_day = {}

        num_variables = 0

        for req_idx, req in enumerate(reqs):
            for day_idx, day in enumerate(days):
                for slot_idx, slot in enumerate(slots):
                    # Check unavailabilities
                    if (req.teacher_id, day, slot.id) in teacher_unavail_set:
                        continue
                    if (req.section_id, day, slot.id) in section_unavail_set:
                        continue

                    # Determine room options
                    room_options = classrooms if classrooms else [None]

                    for r_idx, room in enumerate(room_options):
                        r_id = room.id if room else None

                        var_name = f"x_req{req_idx}_r{r_idx}_s{slot_idx}_d{day_idx}"
                        v = model.NewBoolVar(var_name)
                        num_variables += 1

                        x[(req_idx, r_id, slot_idx, day_idx)] = v
                        vars_by_req[req_idx].append(v)

                        # Group by section slot day
                        sec_key = (req.section_id, slot_idx, day_idx)
                        vars_by_section_slot_day.setdefault(sec_key, []).append(v)

                        # Group by teacher slot day
                        teach_key = (req.teacher_id, slot_idx, day_idx)
                        vars_by_teacher_slot_day.setdefault(teach_key, []).append(v)

                        # Group by room slot day
                        if r_id:
                            room_key = (r_id, slot_idx, day_idx)
                            vars_by_room_slot_day.setdefault(room_key, []).append(v)

        # Constraint 1: Subject Quota (Weekly period count)
        for req_idx, req in enumerate(reqs):
            req_vars = vars_by_req[req_idx]
            if len(req_vars) < req.required_weekly_periods:
                logger.warning("Infeasible requirement: req_idx=%s requires %s periods, available slots=%s",
                               req_idx, req.required_weekly_periods, len(req_vars))
            model.Add(sum(req_vars) == req.required_weekly_periods)

        # Constraint 2: Section Overlap (Max 1 class per section per slot)
        for sec_key, sec_vars in vars_by_section_slot_day.items():
            model.Add(sum(sec_vars) <= 1)

        # Constraint 3: Teacher Overlap (Max 1 class per teacher per slot)
        for teach_key, teach_vars in vars_by_teacher_slot_day.items():
            model.Add(sum(teach_vars) <= 1)

        # Constraint 4: Room Overlap (Max 1 class per room per slot)
        for room_key, room_vars in vars_by_room_slot_day.items():
            model.Add(sum(room_vars) <= 1)

        # Soft Constraints / Objective Penalties
        soft_penalties = []

        # Soft 1: Spread repeated subjects across different days (minimize same subject > 1 on same day)
        for req_idx, req in enumerate(reqs):
            if req.required_weekly_periods <= len(days):
                for day_idx in range(len(days)):
                    day_vars = [
                        v for (r_idx, room) in enumerate(classrooms if classrooms else [None])
                        for slot_idx in range(len(slots))
                        if (v := x.get((req_idx, room.id if room else None, slot_idx, day_idx))) is not None
                    ]
                    if len(day_vars) > 1:
                        # Extra count over 1 on same day
                        same_day_count = model.NewIntVar(0, len(slots), f"same_day_{req_idx}_{day_idx}")
                        model.Add(same_day_count == sum(day_vars))
                        penalty_var = model.NewIntVar(0, len(slots), f"penalty_{req_idx}_{day_idx}")
                        model.Add(penalty_var >= same_day_count - 1)
                        model.Add(penalty_var >= 0)
                        soft_penalties.append(penalty_var * 10)

        if soft_penalties:
            model.Minimize(sum(soft_penalties))

        # Solve model
        cp_solver = cp_model.CpSolver()
        cp_solver.parameters.max_time_in_seconds = solver_input.timeout_seconds
        cp_solver.parameters.num_search_workers = 4

        status_code = cp_solver.Solve(model)
        elapsed_ms = int((time.time() - start_time) * 1000)

        status_str_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        status_str = status_str_map.get(status_code, "UNKNOWN")

        assignments = []
        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for (req_idx, r_id, slot_idx, day_idx), v in x.items():
                if cp_solver.Value(v) == 1:
                    req = reqs[req_idx]
                    slot = slots[slot_idx]
                    day = days[day_idx]
                    assignments.append(
                        TimetableAssignmentOutput(
                            section_id=req.section_id,
                            school_class_id=req.school_class_id,
                            subject_id=req.subject_id,
                            teacher_id=req.teacher_id,
                            classroom_id=r_id,
                            period_slot_id=slot.id,
                            day_of_week=day,
                        )
                    )

        constraint_stats = {
            "num_curriculum_requirements": len(reqs),
            "num_days": len(days),
            "num_slots_per_day": len(slots),
            "num_classrooms": len(classrooms),
            "num_variables": num_variables,
            "num_assignments_generated": len(assignments),
            "solver_status": status_str,
            "solver_wall_time_s": cp_solver.WallTime(),
        }

        return TimetableSolverResult(
            status=status_str,
            solver_duration_ms=elapsed_ms,
            objective_score=int(cp_solver.ObjectiveValue()) if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0,
            assignments=assignments,
            constraint_stats=constraint_stats,
            error_message="No feasible timetable found for the given resource constraints." if status_code == cp_model.INFEASIBLE else None,
        )
