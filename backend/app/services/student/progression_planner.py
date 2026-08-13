"""
Progression Planner Service Component.

Single source of truth for reading and calculating academic progression plans,
student eligibility, promotion decisions, section fallback resolution,
class-level roll number allocation, canonical plan snapshot building, and
SHA-256 execution_plan_hash computation.

STRICT READ-ONLY GUARANTEE:
This domain service NEVER calls db.add(), db.delete(), db.commit(), or db.flush(),
and NEVER mutates any persistent model or database entity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import ceil
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import PromotionDecision, StudentStatus
from app.common.exceptions import NotFoundException, ValidationException
from app.common.logger.logger import get_logger
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.repositories.academic_year import (
    AcademicYearRepository,
    ClassProgressionRuleRepository,
    academic_year_repository,
    class_progression_rule_repository,
)
from app.repositories.school_class import SchoolClassRepository, school_class_repository
from app.repositories.section import SectionRepository, section_repository
from app.repositories.student import StudentRepository, student_repository
from app.schemas.student.progression_preview_schema import (
    ProgressionPreviewSummary,
    StudentProgressionPreviewItem,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class ProgressionPlan:
    """
    Immutable evaluated academic progression plan calculation result.
    Contains evaluation summary, evaluated items, canonical snapshot payload,
    and deterministic SHA-256 execution_plan_hash.
    """

    summary: ProgressionPreviewSummary
    evaluated_items: list[StudentProgressionPreviewItem]
    execution_plan_hash: str
    canonical_payload: dict[str, Any]


class ProgressionPlanner:
    """
    READ-ONLY Academic Progression Planner Component.

    Evaluates student progression rules, eligibility, target class/section resolution,
    class-level roll number allocation, canonical plan snapshots, and SHA-256 plan hash computation.
    """

    def __init__(
        self,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
        class_progression_rule_repo: ClassProgressionRuleRepository = class_progression_rule_repository,
        school_class_repo: SchoolClassRepository = school_class_repository,
        section_repo: SectionRepository = section_repository,
        student_repo: StudentRepository = student_repository,
    ) -> None:
        self.academic_year_repository = academic_year_repo
        self.class_progression_rule_repository = class_progression_rule_repo
        self.school_class_repository = school_class_repo
        self.section_repository = section_repo
        self.student_repository = student_repo

    def calculate_plan(
        self,
        db: Session,
        source_academic_year_id: UUID,
        target_academic_year_id: UUID,
        current_school_id: UUID,
    ) -> ProgressionPlan:
        """
        Calculate prospective academic progression plan for a school transition.

        STRICT READ-ONLY: No database mutations are performed.
        """
        if current_school_id is None:
            raise ValidationException("Authenticated user is not associated with a school.")

        if source_academic_year_id == target_academic_year_id:
            raise ValidationException("Source and target academic years cannot be the same.")

        # 1. Validate Academic Years belong to user's school
        source_ay = self.academic_year_repository.get_by_id_and_school(
            db, source_academic_year_id, current_school_id
        )
        if source_ay is None or source_ay.is_deleted:
            raise NotFoundException("Academic Year", str(source_academic_year_id))

        target_ay = self.academic_year_repository.get_by_id_and_school(
            db, target_academic_year_id, current_school_id
        )
        if target_ay is None or target_ay.is_deleted:
            raise NotFoundException("Academic Year", str(target_academic_year_id))

        # 2. Pre-fetch Active Class Progression Rules for School
        active_rules = self.class_progression_rule_repository.get_all_active_for_school(
            db, current_school_id
        )
        rules_by_source_class: dict[UUID, ClassProgressionRule] = {
            rule.source_class_id: rule for rule in active_rules
        }

        # 3. Pre-fetch Active School Classes for School
        active_classes = self.school_class_repository.get_by_school(db, current_school_id)
        classes_by_id: dict[UUID, SchoolClass] = {
            sc.id: sc for sc in active_classes if not sc.is_deleted
        }

        # 4. Pre-fetch Active Sections for School & Group by Class ID
        sections_stmt = (
            select(Section)
            .where(
                Section.is_deleted.is_(False),
            )
            .order_by(Section.name.asc(), Section.id.asc())
        )
        all_sections = list(db.scalars(sections_stmt))
        sections_by_class_id: dict[UUID, list[Section]] = {}
        for sec in all_sections:
            if sec.school_class_id in classes_by_id:
                sections_by_class_id.setdefault(sec.school_class_id, []).append(sec)

        # 5. Pre-fetch Target Academic Year Occupancy (Existing active students in target AY)
        target_occupancy_stmt = (
            select(
                Student.id,
                Student.school_class_id,
                Student.section_id,
                Student.roll_number,
                Student.updated_at,
            )
            .where(
                Student.school_id == current_school_id,
                Student.academic_year_id == target_academic_year_id,
                Student.is_deleted.is_(False),
                Student.roll_number.isnot(None),
            )
            .order_by(Student.id.asc())
        )
        target_occupancy_rows = list(db.execute(target_occupancy_stmt).all())

        target_occupancy_snapshot: list[dict[str, Any]] = []
        occupied_roll_numbers: dict[UUID, set[str]] = {}
        for row in sorted(target_occupancy_rows, key=lambda r: str(r[0])):
            s_id, class_id, section_id, roll_no, updated_at = row
            target_occupancy_snapshot.append({
                "student_id": str(s_id),
                "school_class_id": str(class_id),
                "section_id": str(section_id),
                "roll_number": str(roll_no),
                "updated_at": updated_at.isoformat() if updated_at else None,
            })
            if class_id and roll_no:
                occupied_roll_numbers.setdefault(class_id, set()).add(str(roll_no))

        # 6. Fetch Active Students in Source Academic Year with eager joins
        students_stmt = (
            select(Student)
            .options(
                joinedload(Student.school_class),
                joinedload(Student.section),
            )
            .where(
                Student.school_id == current_school_id,
                Student.academic_year_id == source_academic_year_id,
                Student.is_deleted.is_(False),
            )
        )
        all_students = list(db.scalars(students_stmt))

        # Sort students deterministically: (Class display_order, Section name, last_name, first_name, id)
        def student_sort_key(s: Student):
            class_order = s.school_class.display_order if s.school_class else 9999
            sec_name = s.section.name if s.section else ""
            l_name = s.last_name or ""
            f_name = s.first_name or ""
            return (class_order, sec_name, l_name, f_name, str(s.id))

        all_students.sort(key=student_sort_key)

        evaluated_items: list[StudentProgressionPreviewItem] = []
        promoted_count = 0
        graduated_count = 0
        retained_count = 0
        blocked_count = 0
        excluded_count = 0
        warning_count = 0

        # 7. Evaluate Each Student in Memory
        for student in all_students:
            warnings: list[str] = []
            c_class_name = student.school_class.name if student.school_class else "Unknown"
            c_sec_name = student.section.name if student.section else "Unknown"

            # Check eligibility status
            if student.status != StudentStatus.ACTIVE:
                excluded_count += 1
                evaluated_items.append(
                    StudentProgressionPreviewItem(
                        student_id=student.id,
                        admission_number=student.admission_number,
                        student_name=f"{student.first_name} {student.last_name}".strip(),
                        current_academic_year_id=source_academic_year_id,
                        current_class_id=student.school_class_id,
                        current_class_name=c_class_name,
                        current_section_id=student.section_id,
                        current_section_name=c_sec_name,
                        current_roll_number=student.roll_number,
                        decision=PromotionDecision.PENDING,
                        target_class_id=None,
                        target_class_name=None,
                        target_section_id=None,
                        target_section_name=None,
                        proposed_roll_number=None,
                        allocation_status="EXCLUDED",
                        reason=f"Student status is '{student.status.value}' (not ACTIVE)",
                        warnings=[],
                    )
                )
                continue

            rule = rules_by_source_class.get(student.school_class_id)
            if rule is None:
                blocked_count += 1
                warning_count += 1
                evaluated_items.append(
                    StudentProgressionPreviewItem(
                        student_id=student.id,
                        admission_number=student.admission_number,
                        student_name=f"{student.first_name} {student.last_name}".strip(),
                        current_academic_year_id=source_academic_year_id,
                        current_class_id=student.school_class_id,
                        current_class_name=c_class_name,
                        current_section_id=student.section_id,
                        current_section_name=c_sec_name,
                        current_roll_number=student.roll_number,
                        decision=PromotionDecision.PENDING,
                        target_class_id=None,
                        target_class_name=None,
                        target_section_id=None,
                        target_section_name=None,
                        proposed_roll_number=None,
                        allocation_status="BLOCKED",
                        reason="No active class progression rule configured for source class",
                        warnings=["Missing progression rule"],
                    )
                )
                continue

            if rule.is_terminal:
                graduated_count += 1
                evaluated_items.append(
                    StudentProgressionPreviewItem(
                        student_id=student.id,
                        admission_number=student.admission_number,
                        student_name=f"{student.first_name} {student.last_name}".strip(),
                        current_academic_year_id=source_academic_year_id,
                        current_class_id=student.school_class_id,
                        current_class_name=c_class_name,
                        current_section_id=student.section_id,
                        current_section_name=c_sec_name,
                        current_roll_number=student.roll_number,
                        decision=PromotionDecision.GRADUATED,
                        target_class_id=None,
                        target_class_name=None,
                        target_section_id=None,
                        target_section_name=None,
                        proposed_roll_number=None,
                        allocation_status="READY",
                        reason="Terminal class progression (Graduation)",
                        warnings=[],
                    )
                )
                continue

            # Non-terminal rule: resolve target class
            target_class = classes_by_id.get(rule.target_class_id) if rule.target_class_id else None
            if target_class is None:
                blocked_count += 1
                warning_count += 1
                evaluated_items.append(
                    StudentProgressionPreviewItem(
                        student_id=student.id,
                        admission_number=student.admission_number,
                        student_name=f"{student.first_name} {student.last_name}".strip(),
                        current_academic_year_id=source_academic_year_id,
                        current_class_id=student.school_class_id,
                        current_class_name=c_class_name,
                        current_section_id=student.section_id,
                        current_section_name=c_sec_name,
                        current_roll_number=student.roll_number,
                        decision=PromotionDecision.PENDING,
                        target_class_id=rule.target_class_id,
                        target_class_name=None,
                        target_section_id=None,
                        target_section_name=None,
                        proposed_roll_number=None,
                        allocation_status="BLOCKED",
                        reason="Configured target class does not exist or was deleted",
                        warnings=["Missing target class"],
                    )
                )
                continue

            # Resolve target section
            target_sections = sections_by_class_id.get(target_class.id, [])
            if not target_sections:
                blocked_count += 1
                warning_count += 1
                evaluated_items.append(
                    StudentProgressionPreviewItem(
                        student_id=student.id,
                        admission_number=student.admission_number,
                        student_name=f"{student.first_name} {student.last_name}".strip(),
                        current_academic_year_id=source_academic_year_id,
                        current_class_id=student.school_class_id,
                        current_class_name=c_class_name,
                        current_section_id=student.section_id,
                        current_section_name=c_sec_name,
                        current_roll_number=student.roll_number,
                        decision=PromotionDecision.PENDING,
                        target_class_id=target_class.id,
                        target_class_name=target_class.name,
                        target_section_id=None,
                        target_section_name=None,
                        proposed_roll_number=None,
                        allocation_status="BLOCKED",
                        reason=f"Target class '{target_class.name}' has no active sections",
                        warnings=["No active section in target class"],
                    )
                )
                continue

            # Section matching logic
            same_name_sec = next(
                (sec for sec in target_sections if sec.name == c_sec_name),
                None,
            )
            if same_name_sec is not None:
                chosen_section = same_name_sec
            else:
                chosen_section = target_sections[0]
                warnings.append(
                    f"Section '{c_sec_name}' not found in target class '{target_class.name}'. Fallback to section '{chosen_section.name}'."
                )
                warning_count += 1

            # In-memory target-occupancy aware roll number allocation (class-level pool)
            occupied_set = occupied_roll_numbers.setdefault(target_class.id, set())

            counter = 1
            while True:
                candidate = f"{counter:03d}"
                if candidate not in occupied_set:
                    proposed_roll = candidate
                    occupied_set.add(proposed_roll)
                    break
                counter += 1

            promoted_count += 1
            evaluated_items.append(
                StudentProgressionPreviewItem(
                    student_id=student.id,
                    admission_number=student.admission_number,
                    student_name=f"{student.first_name} {student.last_name}".strip(),
                    current_academic_year_id=source_academic_year_id,
                    current_class_id=student.school_class_id,
                    current_class_name=c_class_name,
                    current_section_id=student.section_id,
                    current_section_name=c_sec_name,
                    current_roll_number=student.roll_number,
                    decision=PromotionDecision.PROMOTED,
                    target_class_id=target_class.id,
                    target_class_name=target_class.name,
                    target_section_id=chosen_section.id,
                    target_section_name=chosen_section.name,
                    proposed_roll_number=proposed_roll,
                    allocation_status="PROPOSED",
                    reason=f"Promoted to {target_class.name} Section {chosen_section.name}",
                    warnings=warnings,
                )
            )

        total_evaluated = len(all_students)
        summary = ProgressionPreviewSummary(
            source_academic_year_id=source_academic_year_id,
            target_academic_year_id=target_academic_year_id,
            total_students_evaluated=total_evaluated,
            promoted_count=promoted_count,
            graduated_count=graduated_count,
            retained_count=retained_count,
            blocked_count=blocked_count,
            excluded_count=excluded_count,
            warning_count=warning_count,
        )

        # 8. Calculate Canonical Execution Plan Hash (SHA-256)
        rules_snapshot: list[dict[str, Any]] = []
        for rule in sorted(active_rules, key=lambda r: str(r.source_class_id)):
            rules_snapshot.append({
                "rule_id": str(rule.id),
                "source_class_id": str(rule.source_class_id),
                "target_class_id": str(rule.target_class_id) if rule.target_class_id else None,
                "is_terminal": rule.is_terminal,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
            })

        source_students_snapshot: list[dict[str, Any]] = []
        for student in sorted(all_students, key=lambda s: str(s.id)):
            source_students_snapshot.append({
                "student_id": str(student.id),
                "status": student.status.value if hasattr(student.status, "value") else str(student.status),
                "academic_year_id": str(student.academic_year_id),
                "school_class_id": str(student.school_class_id),
                "section_id": str(student.section_id),
                "roll_number": student.roll_number,
                "updated_at": student.updated_at.isoformat() if student.updated_at else None,
            })

        target_structure_snapshot: list[dict[str, Any]] = []
        for sc_id in sorted(classes_by_id.keys(), key=lambda k: str(k)):
            sc = classes_by_id[sc_id]
            sec_list = sections_by_class_id.get(sc_id, [])
            sorted_secs = [
                {"section_id": str(s.id), "section_name": s.name}
                for s in sorted(sec_list, key=lambda s: (s.name, str(s.id)))
            ]
            target_structure_snapshot.append({
                "class_id": str(sc.id),
                "class_name": sc.name,
                "sections": sorted_secs,
            })

        canonical_payload = {
            "school_id": str(current_school_id),
            "source_academic_year_id": str(source_academic_year_id),
            "target_academic_year_id": str(target_academic_year_id),
            "active_progression_rules": rules_snapshot,
            "source_students": source_students_snapshot,
            "active_target_structure": target_structure_snapshot,
            "target_occupancy": target_occupancy_snapshot,
        }

        canonical_json = json.dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
        )
        execution_plan_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return ProgressionPlan(
            summary=summary,
            evaluated_items=evaluated_items,
            execution_plan_hash=execution_plan_hash,
            canonical_payload=canonical_payload,
        )


progression_planner = ProgressionPlanner()
