from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID
import uuid

from sqlalchemy.orm import Session

from app.common.enums.fees import (
    StudentFeeAssignmentStatus,
)
from app.common.enums.student import StudentStatus
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import (
    FeeDiscount,
    StudentFeeAssignment,
    StudentFeeItem,
)
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.fees.fee_payment_repository import (
    FeePaymentRepository,
    fee_payment_repository,
)
from app.repositories.fees.fee_structure_repository import (
    FeeStructureRepository,
    fee_structure_repository,
)
from app.repositories.fees.student_fee_assignment_repository import (
    StudentFeeAssignmentRepository,
    student_fee_assignment_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.school_class.school_class_repository import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.student.student_repository import (
    StudentRepository,
    student_repository,
)
from app.schemas.fees.fees import (
    FeeDiscountCreate,
    FeeDiscountResponse,
    FeeItemCreate,
    FeeItemResponse,
    FeePaymentCreate,
    FeePaymentListResponse,
    FeePaymentResponse,
    FeeReceiptResponse,
    FeeStructureCreate,
    FeeStructureListResponse,
    FeeStructureResponse,
    FeeStructureUpdate,
    StudentFeeAssignmentCreate,
    StudentFeeAssignmentListResponse,
    StudentFeeAssignmentResponse,
    StudentFeeItemCreate,
    StudentFeeItemResponse,
)

logger = get_logger(__name__)


class FeeService:
    """
    Business logic service for Fees Management operations.
    """

    def __init__(
        self,
        structure_repo: FeeStructureRepository,
        assignment_repo: StudentFeeAssignmentRepository,
        payment_repo: FeePaymentRepository,
        school_repo: SchoolRepository,
        academic_year_repo: AcademicYearRepository,
        class_repo: SchoolClassRepository,
        student_repo: StudentRepository,
    ) -> None:
        self.structure_repo = structure_repo
        self.assignment_repo = assignment_repo
        self.payment_repo = payment_repo
        self.school_repo = school_repo
        self.academic_year_repo = academic_year_repo
        self.class_repo = class_repo
        self.student_repo = student_repo

    # ------------------------------------------------------------------
    # Helper Metrics Calculation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_metrics(assignment: StudentFeeAssignment) -> dict:
        """
        Calculate gross amount, total discounts, net payable, total paid, and outstanding due using Decimal.
        """
        ZERO = Decimal("0.00")
        gross_amount = ZERO
        for item in assignment.student_fee_items:
            if not item.is_deleted and item.is_applicable:
                amt = item.amount if isinstance(item.amount, Decimal) else Decimal(str(item.amount))
                gross_amount += amt

        total_discounts = ZERO
        for d in assignment.discounts:
            if not d.is_deleted:
                amt = d.amount if isinstance(d.amount, Decimal) else Decimal(str(d.amount))
                total_discounts += amt

        net_payable = max(ZERO, gross_amount - total_discounts)

        total_paid = ZERO
        for p in assignment.payments:
            if not p.is_deleted:
                amt = p.amount if isinstance(p.amount, Decimal) else Decimal(str(p.amount))
                total_paid += amt

        outstanding_due = max(ZERO, net_payable - total_paid)

        return {
            "gross_amount": gross_amount,
            "total_discounts": total_discounts,
            "net_payable": net_payable,
            "total_paid": total_paid,
            "outstanding_due": outstanding_due,
        }

    @staticmethod
    def update_assignment_status(
        assignment: StudentFeeAssignment, metrics: dict
    ) -> None:
        """
        Update StudentFeeAssignment status based on financial metrics.
        Preserves CANCELLED status if assignment is already cancelled.
        """
        if assignment.status == StudentFeeAssignmentStatus.CANCELLED:
            return

        net_payable = metrics["net_payable"]
        total_paid = metrics["total_paid"]

        if total_paid >= net_payable and net_payable >= Decimal("0.00"):
            assignment.status = StudentFeeAssignmentStatus.PAID
        elif total_paid > Decimal("0.00"):
            assignment.status = StudentFeeAssignmentStatus.PARTIALLY_PAID
        else:
            assignment.status = StudentFeeAssignmentStatus.PENDING

    def _build_assignment_response(
        self, assignment: StudentFeeAssignment
    ) -> StudentFeeAssignmentResponse:
        metrics = self.calculate_metrics(assignment)

        active_items = [
            StudentFeeItemResponse.model_validate(item)
            for item in assignment.student_fee_items
            if not item.is_deleted
        ]
        active_discounts = [
            FeeDiscountResponse.model_validate(d)
            for d in assignment.discounts
            if not d.is_deleted
        ]

        return StudentFeeAssignmentResponse(
            id=assignment.id,
            school_id=assignment.school_id,
            academic_year_id=assignment.academic_year_id,
            student_id=assignment.student_id,
            fee_structure_id=assignment.fee_structure_id,
            status=assignment.status,
            due_date=assignment.due_date,
            remarks=assignment.remarks,
            gross_amount=metrics["gross_amount"],
            total_discounts=metrics["total_discounts"],
            net_payable=metrics["net_payable"],
            total_paid=metrics["total_paid"],
            outstanding_due=metrics["outstanding_due"],
            student_fee_items=active_items,
            discounts=active_discounts,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
        )

    # ------------------------------------------------------------------
    # Fee Structure Operations
    # ------------------------------------------------------------------

    def create_fee_structure(
        self,
        db: Session,
        data: FeeStructureCreate,
        current_school_id: UUID,
    ) -> FeeStructure:
        school = self.school_repo.get(db, current_school_id)
        if school is None:
            raise NotFoundException("School", str(current_school_id))

        academic_year = self.academic_year_repo.get(db, data.academic_year_id)
        if academic_year is None:
            raise NotFoundException("Academic Year", str(data.academic_year_id))
        if academic_year.school_id != current_school_id:
            raise ValidationException("Academic year must belong to current school.")

        if data.school_class_id is not None:
            school_class = self.class_repo.get(db, data.school_class_id)
            if school_class is None:
                raise NotFoundException("School Class", str(data.school_class_id))
            if school_class.school_id != current_school_id:
                raise ValidationException("School class must belong to current school.")

        if self.structure_repo.exists_by_name(
            db,
            school_id=current_school_id,
            academic_year_id=data.academic_year_id,
            name=data.name,
            school_class_id=data.school_class_id,
        ):
            raise AlreadyExistsException("FeeStructure", data.name)

        structure = FeeStructure(
            school_id=current_school_id,
            academic_year_id=data.academic_year_id,
            school_class_id=data.school_class_id,
            name=data.name,
            description=data.description,
            status=data.status,
        )

        for item_data in data.items:
            item = FeeItem(
                category=item_data.category,
                name=item_data.name,
                amount=item_data.amount,
                is_optional=item_data.is_optional,
                order=item_data.order,
            )
            structure.items.append(item)

        created = self.structure_repo.create(db, structure)
        logger.info("FeeStructure '%s' created with ID: %s", created.name, created.id)
        return created

    def get_fee_structure(
        self,
        db: Session,
        structure_id: UUID,
        current_school_id: UUID,
    ) -> FeeStructure:
        structure = self.structure_repo.get_by_id_and_school(
            db, structure_id, current_school_id
        )
        if structure is None or structure.is_deleted:
            raise NotFoundException("FeeStructure", str(structure_id))
        return structure

    def list_fee_structures(
        self,
        db: Session,
        current_school_id: UUID,
        academic_year_id: UUID | None = None,
        school_class_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> FeeStructureListResponse:
        items, total = self.structure_repo.list_structures(
            db=db,
            school_id=current_school_id,
            academic_year_id=academic_year_id,
            school_class_id=school_class_id,
            status=status,
            search=search,
            page=page,
            page_size=page_size,
        )
        total_pages = ceil(total / page_size) if total > 0 else 0

        response_items = []
        for item in items:
            active_items = [
                FeeItemResponse.model_validate(i) for i in item.items if not i.is_deleted
            ]
            resp = FeeStructureResponse(
                id=item.id,
                school_id=item.school_id,
                academic_year_id=item.academic_year_id,
                school_class_id=item.school_class_id,
                name=item.name,
                description=item.description,
                status=item.status,
                items=active_items,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            response_items.append(resp)

        return FeeStructureListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_fee_structure(
        self,
        db: Session,
        structure_id: UUID,
        data: FeeStructureUpdate,
        current_school_id: UUID,
    ) -> FeeStructure:
        structure = self.get_fee_structure(db, structure_id, current_school_id)
        update_dict = data.model_dump(exclude_unset=True)

        if "name" in update_dict and update_dict["name"] != structure.name:
            if self.structure_repo.exists_by_name(
                db,
                school_id=current_school_id,
                academic_year_id=structure.academic_year_id,
                name=update_dict["name"],
                school_class_id=update_dict.get("school_class_id", structure.school_class_id),
                exclude_id=structure_id,
            ):
                raise AlreadyExistsException("FeeStructure", update_dict["name"])

        if "school_class_id" in update_dict and update_dict["school_class_id"] is not None:
            school_class = self.class_repo.get(db, update_dict["school_class_id"])
            if school_class is None:
                raise NotFoundException("School Class", str(update_dict["school_class_id"]))
            if school_class.school_id != current_school_id:
                raise ValidationException("School class must belong to current school.")

        if "items" in update_dict and update_dict["items"] is not None:
            # Mark existing items soft deleted
            for existing_item in structure.items:
                existing_item.soft_delete()

            for item_data in data.items:
                new_item = FeeItem(
                    fee_structure_id=structure.id,
                    category=item_data.category,
                    name=item_data.name,
                    amount=item_data.amount,
                    is_optional=item_data.is_optional,
                    order=item_data.order,
                )
                structure.items.append(new_item)

        for key in ["name", "description", "school_class_id", "status"]:
            if key in update_dict:
                setattr(structure, key, update_dict[key])

        updated = self.structure_repo.update(db, structure)
        logger.info("FeeStructure ID: %s updated", structure_id)
        return updated

    def delete_fee_structure(
        self,
        db: Session,
        structure_id: UUID,
        current_school_id: UUID,
    ) -> None:
        structure = self.get_fee_structure(db, structure_id, current_school_id)
        for item in structure.items:
            item.soft_delete()
        self.structure_repo.delete(db, structure)
        logger.info("FeeStructure ID: %s soft deleted", structure_id)

    # ------------------------------------------------------------------
    # Student Fee Assignment Operations
    # ------------------------------------------------------------------

    def assign_fee_structure(
        self,
        db: Session,
        data: StudentFeeAssignmentCreate,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        student = self.student_repo.get(db, data.student_id)
        if student is None or student.is_deleted:
            raise NotFoundException("Student", str(data.student_id))
        if student.school_id != current_school_id:
            raise ValidationException("Student must belong to current school.")
        if hasattr(student, "status") and student.status != StudentStatus.ACTIVE:
            raise ValidationException("Student is not active.")

        academic_year = self.academic_year_repo.get(db, data.academic_year_id)
        if academic_year is None or academic_year.is_deleted:
            raise NotFoundException("Academic Year", str(data.academic_year_id))
        if academic_year.school_id != current_school_id:
            raise ValidationException("Academic year must belong to current school.")

        structure = self.get_fee_structure(db, data.fee_structure_id, current_school_id)
        if structure.academic_year_id != data.academic_year_id:
            raise ValidationException("Fee structure academic year mismatch.")

        if structure.school_class_id is not None:
            if getattr(student, "school_class_id", None) != structure.school_class_id:
                raise ValidationException("Student class does not match fee structure class requirement.")


        if self.assignment_repo.exists_active_assignment(
            db,
            school_id=current_school_id,
            academic_year_id=data.academic_year_id,
            student_id=data.student_id,
            fee_structure_id=data.fee_structure_id,
        ):
            raise AlreadyExistsException("StudentFeeAssignment", str(data.student_id))

        assignment = StudentFeeAssignment(
            school_id=current_school_id,
            academic_year_id=data.academic_year_id,
            student_id=data.student_id,
            fee_structure_id=data.fee_structure_id,
            status=StudentFeeAssignmentStatus.PENDING,
            due_date=data.due_date,
            remarks=data.remarks,
        )

        for structure_item in structure.items:
            if not structure_item.is_deleted:
                sf_item = StudentFeeItem(
                    fee_item_id=structure_item.id,
                    category=structure_item.category,
                    name=structure_item.name,
                    amount=structure_item.amount,
                    is_optional=structure_item.is_optional,
                    is_applicable=True,
                )
                assignment.student_fee_items.append(sf_item)

        if getattr(student, "academic_year_id", None) is not None:
            if student.academic_year_id != data.academic_year_id:
                raise ValidationException("Student academic year does not match fee assignment academic year.")

        if data.custom_items:
            valid_structure_item_ids = {item.id for item in structure.items if not item.is_deleted}
            for custom_item in data.custom_items:
                if custom_item.fee_item_id is not None and custom_item.fee_item_id not in valid_structure_item_ids:
                    raise ValidationException("Custom fee item does not belong to the selected fee structure.")
                sf_item = StudentFeeItem(
                    fee_item_id=custom_item.fee_item_id,
                    category=custom_item.category,
                    name=custom_item.name,
                    amount=custom_item.amount,
                    is_optional=custom_item.is_optional,
                    is_applicable=custom_item.is_applicable,
                )
                assignment.student_fee_items.append(sf_item)

        created = self.assignment_repo.create(db, assignment)
        logger.info("Assigned fee structure ID %s to student ID %s", data.fee_structure_id, data.student_id)
        return self._build_assignment_response(created)

    def get_assignment(
        self,
        db: Session,
        assignment_id: UUID,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))
        return self._build_assignment_response(assignment)

    def list_assignments(
        self,
        db: Session,
        current_school_id: UUID,
        academic_year_id: UUID | None = None,
        student_id: UUID | None = None,
        fee_structure_id: UUID | None = None,
        status: StudentFeeAssignmentStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> StudentFeeAssignmentListResponse:
        items, total = self.assignment_repo.list_assignments(
            db=db,
            school_id=current_school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            fee_structure_id=fee_structure_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        total_pages = ceil(total / page_size) if total > 0 else 0

        responses = [self._build_assignment_response(item) for item in items]
        return StudentFeeAssignmentListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def delete_assignment(
        self,
        db: Session,
        assignment_id: UUID,
        current_school_id: UUID,
    ) -> None:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))

        active_payments = [p for p in assignment.payments if not p.is_deleted]
        if active_payments:
            raise ValidationException("Cannot delete student fee assignment with active payment records.")

        for item in assignment.student_fee_items:
            item.soft_delete()
        for discount in assignment.discounts:
            discount.soft_delete()

        self.assignment_repo.delete(db, assignment)
        logger.info("StudentFeeAssignment ID: %s soft deleted", assignment_id)

    # ------------------------------------------------------------------
    # Custom Student Fee Item & Discount Operations
    # ------------------------------------------------------------------

    def add_student_fee_item(
        self,
        db: Session,
        assignment_id: UUID,
        data: StudentFeeItemCreate,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))

        if data.fee_item_id is not None:
            valid_structure_item_ids = {
                item.id for item in assignment.fee_structure.items if not item.is_deleted
            }
            if data.fee_item_id not in valid_structure_item_ids:
                raise ValidationException("fee_item_id does not belong to the assignment's fee structure.")

        item = StudentFeeItem(
            student_fee_assignment_id=assignment.id,
            fee_item_id=data.fee_item_id,
            category=data.category,
            name=data.name,
            amount=data.amount,
            is_optional=data.is_optional,
            is_applicable=data.is_applicable,
        )
        assignment.student_fee_items.append(item)

        metrics = self.calculate_metrics(assignment)
        self.update_assignment_status(assignment, metrics)

        db.commit()
        db.refresh(assignment)

        return self._build_assignment_response(assignment)

    def add_discount(
        self,
        db: Session,
        assignment_id: UUID,
        data: FeeDiscountCreate,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))

        if data.amount <= Decimal("0.00"):
            raise ValidationException("Discount amount must be greater than zero.")

        existing_discount = any(
            d.discount_type == data.discount_type and not d.is_deleted
            for d in assignment.discounts
        )
        if existing_discount:
            raise AlreadyExistsException("FeeDiscount", data.discount_type.value)

        metrics = self.calculate_metrics(assignment)
        new_total_discounts = metrics["total_discounts"] + data.amount
        if new_total_discounts > metrics["gross_amount"]:
            raise ValidationException("Total discount cannot exceed gross payable amount.")

        discount = FeeDiscount(
            student_fee_assignment_id=assignment.id,
            discount_type=data.discount_type,
            name=data.name,
            amount=data.amount,
            remarks=data.remarks,
        )
        assignment.discounts.append(discount)

        metrics = self.calculate_metrics(assignment)
        self.update_assignment_status(assignment, metrics)

        db.commit()
        db.refresh(assignment)

        return self._build_assignment_response(assignment)

    def remove_discount(
        self,
        db: Session,
        assignment_id: UUID,
        discount_id: UUID,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))

        discount = next(
            (d for d in assignment.discounts if d.id == discount_id and not d.is_deleted),
            None,
        )
        if discount is None:
            raise NotFoundException("FeeDiscount", str(discount_id))

        discount.soft_delete()

        metrics = self.calculate_metrics(assignment)
        self.update_assignment_status(assignment, metrics)

        db.commit()
        db.refresh(assignment)

        return self._build_assignment_response(assignment)

    def cancel_assignment(
        self,
        db: Session,
        assignment_id: UUID,
        current_school_id: UUID,
    ) -> StudentFeeAssignmentResponse:
        assignment = self.assignment_repo.get_by_id_and_school(
            db, assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(assignment_id))

        if assignment.status == StudentFeeAssignmentStatus.CANCELLED:
            raise ValidationException("Assignment is already cancelled.")

        active_payments = [p for p in assignment.payments if not p.is_deleted]
        if active_payments:
            raise ValidationException("Cannot cancel fee assignment with active payment records.")

        assignment.status = StudentFeeAssignmentStatus.CANCELLED
        db.commit()
        db.refresh(assignment)

        return self._build_assignment_response(assignment)

    # ------------------------------------------------------------------
    # Payment & Receipt Operations
    # ------------------------------------------------------------------

    def record_payment(
        self,
        db: Session,
        data: FeePaymentCreate,
        current_school_id: UUID,
    ) -> FeePaymentResponse:
        assignment = self.assignment_repo.get_by_id_and_school_for_update(
            db, data.student_fee_assignment_id, current_school_id
        )
        if assignment is None or assignment.is_deleted:
            raise NotFoundException("StudentFeeAssignment", str(data.student_fee_assignment_id))

        if assignment.status == StudentFeeAssignmentStatus.CANCELLED:
            raise ValidationException("Cannot record payment for a cancelled fee assignment.")

        if data.amount <= Decimal("0.00"):
            raise ValidationException("Payment amount must be greater than zero.")

        metrics = self.calculate_metrics(assignment)
        outstanding = metrics["outstanding_due"]

        if data.amount > outstanding:
            raise ValidationException("Payment amount cannot exceed outstanding due balance.")

        receipt_number = self._generate_receipt_number(db, current_school_id)

        payment = FeePayment(
            school_id=current_school_id,
            student_fee_assignment_id=assignment.id,
            receipt_number=receipt_number,
            amount=data.amount,
            payment_date=data.payment_date,
            payment_mode=data.payment_mode,
            reference_number=data.reference_number,
            remarks=data.remarks,
        )
        assignment.payments.append(payment)
        db.flush()
        db.refresh(payment)

        metrics = self.calculate_metrics(assignment)
        self.update_assignment_status(assignment, metrics)

        db.commit()
        db.refresh(payment)

        logger.info(
            "Payment recorded with Receipt '%s' for Assignment ID: %s",
            receipt_number,
            assignment.id,
        )
        return FeePaymentResponse.model_validate(payment)

    def get_payment(
        self,
        db: Session,
        payment_id: UUID,
        current_school_id: UUID,
    ) -> FeePaymentResponse:
        payment = self.payment_repo.get_by_id_and_school(
            db, payment_id, current_school_id
        )
        if payment is None or payment.is_deleted:
            raise NotFoundException("FeePayment", str(payment_id))
        return FeePaymentResponse.model_validate(payment)

    def get_receipt(
        self,
        db: Session,
        payment_id: UUID,
        current_school_id: UUID,
    ) -> FeeReceiptResponse:
        payment = self.payment_repo.get_by_id_and_school(
            db, payment_id, current_school_id
        )
        if payment is None or payment.is_deleted:
            raise NotFoundException("FeePayment", str(payment_id))

        assignment = payment.assignment
        metrics = self.calculate_metrics(assignment)

        return FeeReceiptResponse(
            receipt_number=payment.receipt_number,
            school_id=payment.school_id,
            student_id=assignment.student_id,
            student_fee_assignment_id=assignment.id,
            payment_id=payment.id,
            payment_date=payment.payment_date,
            payment_mode=payment.payment_mode,
            reference_number=payment.reference_number,
            amount=payment.amount,
            gross_amount=metrics["gross_amount"],
            total_discounts=metrics["total_discounts"],
            net_payable=metrics["net_payable"],
            total_paid=metrics["total_paid"],
            outstanding_due=metrics["outstanding_due"],
        )

    def _generate_receipt_number(self, db: Session, school_id: UUID) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        for _ in range(10):
            unique_part = uuid.uuid4().hex[:6].upper()
            receipt_no = f"REC-{date_str}-{unique_part}"
            if not self.payment_repo.exists_receipt_number(db, school_id, receipt_no):
                return receipt_no
        return f"REC-{date_str}-{uuid.uuid4().hex[:10].upper()}"


fee_service = FeeService(
    structure_repo=fee_structure_repository,
    assignment_repo=student_fee_assignment_repository,
    payment_repo=fee_payment_repository,
    school_repo=school_repository,
    academic_year_repo=academic_year_repository,
    class_repo=school_class_repository,
    student_repo=student_repository,
)
