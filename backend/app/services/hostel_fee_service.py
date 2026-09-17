from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.hostel.hostel_fee import HostelFeeStructure, HostelFeeAllocation
from app.models.fees.fee_structure import FeeStructure, FeeItem
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.fees.fee_payment import FeePayment
from app.models.student.student import Student
from app.models.academic_year.academic_year import AcademicYear
from app.common.enums.fees import (
    FeeCategory,
    FeeStructureStatus,
    StudentFeeAssignmentStatus,
    PaymentMode,
)
from app.services.fee_service import fee_service
from app.schemas.fees.fees import FeePaymentCreate
from app.common.exceptions import (
    BadRequestException,
    NotFoundException,
    ValidationException,
    AlreadyExistsException,
)


class HostelFeeService:
    """
    Service for Hostel Fee Structures and Student Hostel Fee Allocations.
    Strictly integrated with central Fees and Payments ledger.
    Strictly tenant-scoped by school_id.
    """

    def create_fee_structure(
        self,
        db: Session,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        name: str,
        amount: float | Decimal,
        description: str | None = None,
    ) -> HostelFeeStructure:
        # Validate academic year within tenant
        ay = db.execute(
            select(AcademicYear).where(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not ay:
            raise NotFoundException("Academic year not found.")

        dec_amount = Decimal(str(amount))
        if dec_amount <= Decimal("0.00"):
            raise ValidationException("Fee amount must be greater than zero.")

        structure = HostelFeeStructure(
            school_id=school_id,
            academic_year_id=academic_year_id,
            name=name.strip(),
            amount=dec_amount,
            description=description.strip() if description else None,
        )
        db.add(structure)
        db.commit()
        db.refresh(structure)
        return structure

    def get_fee_structures(
        self,
        db: Session,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID | None = None,
    ) -> Sequence[HostelFeeStructure]:
        query = select(HostelFeeStructure).where(
            HostelFeeStructure.school_id == school_id,
            HostelFeeStructure.is_deleted.is_(False),
        )
        if academic_year_id:
            query = query.where(HostelFeeStructure.academic_year_id == academic_year_id)
        return db.execute(query.order_by(HostelFeeStructure.name)).scalars().all()

    def allocate_fee_to_student(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        fee_structure_id: uuid.UUID,
        due_date: date,
    ) -> HostelFeeAllocation:
        # 1. Validate structure within tenant
        structure = db.execute(
            select(HostelFeeStructure).where(
                HostelFeeStructure.id == fee_structure_id,
                HostelFeeStructure.school_id == school_id,
                HostelFeeStructure.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not structure:
            raise NotFoundException("Hostel fee structure not found.")

        # 2. Validate student within tenant & academic year integrity
        student = db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student not found.")

        if getattr(student, "academic_year_id", None) is not None:
            if student.academic_year_id != structure.academic_year_id:
                raise ValidationException("Student academic year does not match hostel fee structure academic year.")

        # 3. Duplicate / Idempotency check on hostel allocation
        existing_alloc = db.execute(
            select(HostelFeeAllocation).where(
                HostelFeeAllocation.school_id == school_id,
                HostelFeeAllocation.student_id == student_id,
                HostelFeeAllocation.fee_structure_id == fee_structure_id,
                HostelFeeAllocation.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing_alloc:
            raise AlreadyExistsException("HostelFeeAllocation", f"Student {student_id} already allocated to fee structure {fee_structure_id}.")

        structure_amount = Decimal(str(structure.amount))

        # 4. Integrate with Central Student Fee Assignment
        assignment = db.execute(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.academic_year_id == structure.academic_year_id,
                StudentFeeAssignment.student_id == student_id,
                StudentFeeAssignment.is_deleted.is_(False),
            ).order_by(StudentFeeAssignment.created_at.asc())
        ).scalars().first()

        item_name = f"Hostel: {structure.name}"

        if assignment:
            # Check if line item already exists on assignment
            item_exists = any(
                item.name == item_name and not item.is_deleted
                for item in assignment.student_fee_items
            )
            if not item_exists:
                new_item = StudentFeeItem(
                    student_fee_assignment_id=assignment.id,
                    fee_item_id=None,
                    category=FeeCategory.OTHER,
                    name=item_name,
                    amount=structure_amount,
                    is_optional=False,
                    is_applicable=True,
                )
                assignment.student_fee_items.append(new_item)
                metrics = fee_service.calculate_metrics(assignment)
                fee_service.update_assignment_status(assignment, metrics)
        else:
            # Create a general fee structure for hostel boarding if none exists
            central_fs = db.execute(
                select(FeeStructure).where(
                    FeeStructure.school_id == school_id,
                    FeeStructure.academic_year_id == structure.academic_year_id,
                    FeeStructure.school_class_id.is_(None),
                    FeeStructure.name == f"Hostel & Boarding - {structure.name}",
                    FeeStructure.is_deleted.is_(False),
                )
            ).scalar_one_or_none()

            if not central_fs:
                central_fs = FeeStructure(
                    school_id=school_id,
                    academic_year_id=structure.academic_year_id,
                    school_class_id=None,
                    name=f"Hostel & Boarding - {structure.name}",
                    description="Hostel boarding and accommodation charges",
                    status=FeeStructureStatus.ACTIVE,
                )
                db.add(central_fs)
                db.flush()

            assignment = StudentFeeAssignment(
                school_id=school_id,
                academic_year_id=structure.academic_year_id,
                student_id=student_id,
                fee_structure_id=central_fs.id,
                due_date=due_date,
                remarks=f"Hostel boarding allocation for {structure.name}",
                status=StudentFeeAssignmentStatus.PENDING,
            )
            new_item = StudentFeeItem(
                fee_item_id=None,
                category=FeeCategory.OTHER,
                name=item_name,
                amount=structure_amount,
                is_optional=False,
                is_applicable=True,
            )
            assignment.student_fee_items.append(new_item)
            db.add(assignment)
            db.flush()
            metrics = fee_service.calculate_metrics(assignment)
            fee_service.update_assignment_status(assignment, metrics)

        # 5. Create Hostel Domain Allocation
        allocation = HostelFeeAllocation(
            school_id=school_id,
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            due_date=due_date,
            amount_due=structure_amount,
            paid_amount=Decimal("0.00"),
            status="UNPAID",
        )
        db.add(allocation)
        db.commit()
        db.refresh(allocation)
        return allocation

    def record_fee_payment(
        self,
        db: Session,
        school_id: uuid.UUID,
        allocation_id: uuid.UUID,
        payment_amount: float | Decimal,
        payment_mode: PaymentMode = PaymentMode.CASH,
        reference_number: str | None = None,
        remarks: str | None = None,
    ) -> HostelFeeAllocation:
        allocation = db.execute(
            select(HostelFeeAllocation).where(
                HostelFeeAllocation.id == allocation_id,
                HostelFeeAllocation.school_id == school_id,
                HostelFeeAllocation.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not allocation:
            raise NotFoundException("Hostel fee allocation not found.")

        dec_payment = Decimal(str(payment_amount))
        if dec_payment <= Decimal("0.00"):
            raise ValidationException("Payment amount must be greater than zero.")

        dec_amount_due = Decimal(str(allocation.amount_due))
        dec_paid = Decimal(str(allocation.paid_amount))
        remaining_due = dec_amount_due - dec_paid
        if dec_payment > remaining_due:
            raise ValidationException(f"Payment amount ({dec_payment}) cannot exceed remaining due balance ({remaining_due}).")

        # Resolve structure to find academic year
        structure = db.execute(
            select(HostelFeeStructure).where(
                HostelFeeStructure.id == allocation.fee_structure_id,
                HostelFeeStructure.school_id == school_id,
            )
        ).scalar_one_or_none()

        if structure:
            # Find central student fee assignment
            assignment = db.execute(
                select(StudentFeeAssignment).where(
                    StudentFeeAssignment.school_id == school_id,
                    StudentFeeAssignment.academic_year_id == structure.academic_year_id,
                    StudentFeeAssignment.student_id == allocation.student_id,
                    StudentFeeAssignment.is_deleted.is_(False),
                )
            ).scalars().first()

            if assignment and assignment.status != StudentFeeAssignmentStatus.CANCELLED:
                payment_data = FeePaymentCreate(
                    student_fee_assignment_id=assignment.id,
                    amount=dec_payment,
                    payment_date=date.today(),
                    payment_mode=payment_mode,
                    reference_number=reference_number or f"HOSTEL-{allocation.id.hex[:8].upper()}",
                    remarks=remarks or f"Hostel fee payment for {structure.name}",
                )
                fee_service.record_payment(
                    db=db,
                    data=payment_data,
                    current_school_id=school_id,
                )

        allocation.paid_amount = dec_paid + dec_payment
        if allocation.paid_amount >= allocation.amount_due:
            allocation.status = "PAID"
        elif allocation.paid_amount > Decimal("0.00"):
            allocation.status = "PARTIAL"

        db.commit()
        db.refresh(allocation)
        return allocation

    def get_student_fee_allocations(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID | None = None,
    ) -> Sequence[HostelFeeAllocation]:
        query = select(HostelFeeAllocation).where(
            HostelFeeAllocation.school_id == school_id,
            HostelFeeAllocation.is_deleted.is_(False),
        )
        if student_id:
            query = query.where(HostelFeeAllocation.student_id == student_id)
        return db.execute(query.order_by(HostelFeeAllocation.due_date.desc())).scalars().all()


hostel_fee_service = HostelFeeService()
