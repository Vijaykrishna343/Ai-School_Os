from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.hostel.hostel_fee import HostelFeeStructure, HostelFeeAllocation
from app.common.exceptions import BadRequestException, NotFoundException


class HostelFeeService:
    """
    Service for Hostel Fee Structures and Student Hostel Fee Allocations.
    Strictly tenant-scoped by school_id.
    """

    def create_fee_structure(
        self,
        db: Session,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        name: str,
        amount: float,
        description: str | None = None,
    ) -> HostelFeeStructure:
        structure = HostelFeeStructure(
            school_id=school_id,
            academic_year_id=academic_year_id,
            name=name,
            amount=amount,
            description=description,
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
        structure = db.execute(
            select(HostelFeeStructure).where(
                HostelFeeStructure.id == fee_structure_id,
                HostelFeeStructure.school_id == school_id,
                HostelFeeStructure.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not structure:
            raise NotFoundException("Hostel fee structure not found.")

        allocation = HostelFeeAllocation(
            school_id=school_id,
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            due_date=due_date,
            amount_due=structure.amount,
            paid_amount=0.0,
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
        payment_amount: float,
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

        allocation.paid_amount += Decimal(str(payment_amount))
        if allocation.paid_amount >= allocation.amount_due:
            allocation.status = "PAID"
        elif allocation.paid_amount > 0:
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
