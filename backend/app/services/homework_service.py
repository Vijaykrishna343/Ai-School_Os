"""
Homework Service — Business logic for Homework & Assignments Module.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.common.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.audit_log import AuditLog
from app.models.homework.homework import Homework, HomeworkStatus
from app.models.homework.homework_submission import HomeworkSubmission, SubmissionStatus
from app.models.parent.parent import Parent
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.schemas.homework.homework import (
    HomeworkCreate,
    HomeworkListResponse,
    HomeworkResponse,
    HomeworkSummaryResponse,
    HomeworkUpdate,
)
from app.schemas.homework.homework_submission import (
    HomeworkSubmissionCreate,
    HomeworkSubmissionGrade,
    HomeworkSubmissionListResponse,
    HomeworkSubmissionResponse,
)
from app.services.notification_service import notification_service

logger = get_logger(__name__)


class HomeworkService:
    def _hydrate_homework_response(self, db: Session, hw: Homework) -> HomeworkResponse:
        teacher = db.get(Teacher, hw.teacher_id)
        school_class = db.get(SchoolClass, hw.school_class_id)
        section = db.get(Section, hw.section_id) if hw.section_id else None
        subject = db.get(Subject, hw.subject_id)

        sub_count = db.scalar(
            select(func.count(HomeworkSubmission.id)).where(
                HomeworkSubmission.school_id == hw.school_id,
                HomeworkSubmission.homework_id == hw.id,
            )
        ) or 0

        teacher_name = f"{teacher.first_name} {teacher.last_name or ''}".strip() if teacher else None
        school_class_name = school_class.name if school_class else None
        section_name = section.name if section else None
        subject_name = getattr(subject, "subject_name", getattr(subject, "name", None)) if subject else None

        res = HomeworkResponse.model_validate(hw)
        res.teacher_name = teacher_name
        res.school_class_name = school_class_name
        res.section_name = section_name
        res.subject_name = subject_name
        res.submission_count = sub_count
        return res

    def _hydrate_submission_response(
        self, db: Session, sub: HomeworkSubmission
    ) -> HomeworkSubmissionResponse:
        student = db.get(Student, sub.student_id)
        homework = db.get(Homework, sub.homework_id)
        subject = db.get(Subject, homework.subject_id) if homework else None

        student_name = f"{student.first_name} {student.last_name or ''}".strip() if student else None
        admission_number = student.admission_number if student else None
        homework_title = homework.title if homework else None
        subject_name = getattr(subject, "subject_name", getattr(subject, "name", None)) if subject else None

        res = HomeworkSubmissionResponse.model_validate(sub)
        res.student_name = student_name
        res.admission_number = admission_number
        res.homework_title = homework_title
        res.subject_name = subject_name
        return res

    def create_homework(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        payload: HomeworkCreate,
    ) -> HomeworkResponse:
        # Resolve Teacher ID
        teacher_id = payload.teacher_id
        if not teacher_id:
            teacher = db.scalar(
                select(Teacher).where(
                    Teacher.school_id == school_id,
                    Teacher.user_id == current_user.id,
                )
            )
            if not teacher:
                # Fallback: query teacher by email
                teacher = db.scalar(
                    select(Teacher).where(
                        Teacher.school_id == school_id,
                        Teacher.email == current_user.email,
                    )
                )
            if not teacher:
                # If still not found, check if teacher exists for school
                teacher = db.scalar(
                    select(Teacher).where(Teacher.school_id == school_id)
                )
            if not teacher:
                raise BadRequestException("Teacher profile required to create homework.")
            teacher_id = teacher.id

        # Validate target class
        sc = db.scalar(
            select(SchoolClass).where(
                SchoolClass.id == payload.school_class_id,
                SchoolClass.school_id == school_id,
            )
        )
        if not sc:
            raise NotFoundException("Target class not found for this school.")

        # Validate section if provided
        if payload.section_id:
            sec = db.scalar(
                select(Section).where(
                    Section.id == payload.section_id,
                    Section.school_class_id == payload.school_class_id,
                )
            )
            if not sec:
                raise BadRequestException("Section does not belong to the selected class.")

        # Validate subject
        sub = db.scalar(
            select(Subject).where(
                Subject.id == payload.subject_id,
                Subject.school_id == school_id,
            )
        )
        if not sub:
            raise NotFoundException("Subject not found for this school.")

        hw = Homework(
            school_id=school_id,
            teacher_id=teacher_id,
            school_class_id=payload.school_class_id,
            section_id=payload.section_id,
            subject_id=payload.subject_id,
            title=payload.title,
            description=payload.description,
            assigned_date=payload.assigned_date or date.today(),
            due_date=payload.due_date,
            status=HomeworkStatus.DRAFT,
        )

        db.add(hw)

        # Audit Log
        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_CREATED",
            module="HOMEWORK",
            entity_type="Homework",
            entity_id=str(hw.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(hw)

        return self._hydrate_homework_response(db, hw)

    def update_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        current_user: IdentityUser,
        payload: HomeworkUpdate,
    ) -> HomeworkResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        if payload.title is not None:
            hw.title = payload.title
        if payload.description is not None:
            hw.description = payload.description
        if payload.due_date is not None:
            hw.due_date = payload.due_date
        if payload.status is not None:
            hw.status = payload.status

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_UPDATED",
            module="HOMEWORK",
            entity_type="Homework",
            entity_id=str(hw.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(hw)

        return self._hydrate_homework_response(db, hw)

    def publish_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        current_user: IdentityUser,
    ) -> HomeworkResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        hw.status = HomeworkStatus.PUBLISHED
        hw.published_at = datetime.now(timezone.utc)

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_PUBLISHED",
            module="HOMEWORK",
            entity_type="Homework",
            entity_id=str(hw.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(hw)

        # Notify Students in class/section
        try:
            stmt = select(Student).where(
                Student.school_id == school_id,
                Student.school_class_id == hw.school_class_id,
            )
            if hw.section_id:
                stmt = stmt.where(Student.section_id == hw.section_id)
            students = db.scalars(stmt).all()

            subject = db.get(Subject, hw.subject_id)
            subject_name = subject.name if subject else "Subject"

            for st in students:
                notification_service.create_in_app_notification(
                    db=db,
                    school_id=school_id,
                    recipient_id=st.id,
                    recipient_type="STUDENT",
                    template_key="general_announcement",
                    variables={
                        "title": f"New Homework: {hw.title}",
                        "message": f"Homework assigned for {subject_name}. Due on {hw.due_date}.",
                    },
                )
        except Exception as e:
            logger.warning(f"Failed to dispatch homework notifications: {e}")

        return self._hydrate_homework_response(db, hw)

    def close_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        current_user: IdentityUser,
    ) -> HomeworkResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        hw.status = HomeworkStatus.CLOSED

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_CLOSED",
            module="HOMEWORK",
            entity_type="Homework",
            entity_id=str(hw.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(hw)

        return self._hydrate_homework_response(db, hw)

    def delete_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        current_user: IdentityUser,
    ) -> None:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_DELETED",
            module="HOMEWORK",
            entity_type="Homework",
            entity_id=str(hw.id),
        )
        db.add(audit)
        db.delete(hw)
        db.commit()

    def get_homework_by_id(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
    ) -> HomeworkResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")
        return self._hydrate_homework_response(db, hw)

    def list_homework(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        page: int = 1,
        page_size: int = 10,
        school_class_id: UUID | None = None,
        section_id: UUID | None = None,
        subject_id: UUID | None = None,
        status: HomeworkStatus | None = None,
        teacher_id: UUID | None = None,
        student_id: UUID | None = None,
    ) -> HomeworkListResponse:
        stmt = select(Homework).where(Homework.school_id == school_id)

        # Role-based filtering
        if user_role == "Student":
            student = None
            if student_id:
                student = db.scalar(
                    select(Student).where(Student.id == student_id, Student.school_id == school_id)
                )
            if not student:
                student = db.scalar(
                    select(Student).where(Student.email == current_user.email, Student.school_id == school_id)
                )
            if student:
                stmt = stmt.where(
                    Homework.school_class_id == student.school_class_id,
                    or_(Homework.section_id == student.section_id, Homework.section_id.is_(None)),
                    Homework.status.in_([HomeworkStatus.PUBLISHED, HomeworkStatus.CLOSED]),
                )
            else:
                stmt = stmt.where(Homework.status.in_([HomeworkStatus.PUBLISHED, HomeworkStatus.CLOSED]))

        elif user_role == "Parent":
            parent = db.scalar(
                select(Parent).where(Parent.email == current_user.email, Parent.school_id == school_id)
            )
            if parent:
                children = db.scalars(
                    select(Student).where(Student.parent_id == parent.id, Student.school_id == school_id)
                ).all()

                if children:
                    conditions = []
                    for ch in children:
                        conditions.append(
                            and_(
                                Homework.school_class_id == ch.school_class_id,
                                or_(Homework.section_id == ch.section_id, Homework.section_id.is_(None)),
                            )
                        )
                    stmt = stmt.where(or_(*conditions), Homework.status.in_([HomeworkStatus.PUBLISHED, HomeworkStatus.CLOSED]))
                else:
                    stmt = stmt.where(Homework.status.in_([HomeworkStatus.PUBLISHED, HomeworkStatus.CLOSED]))
            else:
                stmt = stmt.where(Homework.status.in_([HomeworkStatus.PUBLISHED, HomeworkStatus.CLOSED]))

        # Additional query filters
        if school_class_id:
            stmt = stmt.where(Homework.school_class_id == school_class_id)
        if section_id:
            stmt = stmt.where(Homework.section_id == section_id)
        if subject_id:
            stmt = stmt.where(Homework.subject_id == subject_id)
        if status:
            stmt = stmt.where(Homework.status == status)
        if teacher_id:
            stmt = stmt.where(Homework.teacher_id == teacher_id)

        # Count total
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size)

        # Paginate
        offset = (page - 1) * page_size
        homeworks = db.scalars(
            stmt.order_by(Homework.due_date.desc()).offset(offset).limit(page_size)
        ).all()

        items = [self._hydrate_homework_response(db, hw) for hw in homeworks]

        return HomeworkListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_homework_summary(
        self,
        db: Session,
        school_id: UUID,
        teacher_id: UUID | None = None,
    ) -> HomeworkSummaryResponse:
        base_stmt = select(Homework).where(Homework.school_id == school_id)
        if teacher_id:
            base_stmt = base_stmt.where(Homework.teacher_id == teacher_id)

        total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
        draft = db.scalar(select(func.count()).select_from(base_stmt.where(Homework.status == HomeworkStatus.DRAFT).subquery())) or 0
        published = db.scalar(select(func.count()).select_from(base_stmt.where(Homework.status == HomeworkStatus.PUBLISHED).subquery())) or 0
        closed = db.scalar(select(func.count()).select_from(base_stmt.where(Homework.status == HomeworkStatus.CLOSED).subquery())) or 0

        today = date.today()
        three_days_later = today + timedelta(days=3)
        due_soon = db.scalar(
            select(func.count()).select_from(
                base_stmt.where(
                    Homework.status == HomeworkStatus.PUBLISHED,
                    Homework.due_date >= today,
                    Homework.due_date <= three_days_later,
                ).subquery()
            )
        ) or 0

        return HomeworkSummaryResponse(
            total_homework=total,
            draft_count=draft,
            published_count=published,
            due_soon_count=due_soon,
            closed_count=closed,
        )

    def submit_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        current_user: IdentityUser,
        payload: HomeworkSubmissionCreate,
    ) -> HomeworkSubmissionResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        if hw.status != HomeworkStatus.PUBLISHED:
            raise BadRequestException("Homework is not open for submission.")

        # Find Student record for current user
        student = db.scalar(
            select(Student).where(
                Student.school_id == school_id,
                Student.email == current_user.email,
            )
        )
        if not student:
            # Fallback check student by user_id
            student = db.scalar(
                select(Student).where(
                    Student.school_id == school_id,
                    Student.user_id == current_user.id,
                )
            )
        if not student:
            raise ForbiddenException("Student profile not found for this user account.")

        # Verify student belongs to target class
        if student.school_class_id != hw.school_class_id:
            raise ForbiddenException("Homework was not assigned to your class.")

        # Check existing submission
        existing = db.scalar(
            select(HomeworkSubmission).where(
                HomeworkSubmission.school_id == school_id,
                HomeworkSubmission.homework_id == homework_id,
                HomeworkSubmission.student_id == student.id,
            )
        )

        now = datetime.now(timezone.utc)
        is_late = date.today() > hw.due_date

        if existing:
            existing.content_text = payload.content_text
            existing.submitted_at = now
            existing.status = SubmissionStatus.LATE if is_late else SubmissionStatus.RESUBMITTED
            sub = existing
        else:
            sub = HomeworkSubmission(
                school_id=school_id,
                homework_id=homework_id,
                student_id=student.id,
                submitted_at=now,
                status=SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED,
                content_text=payload.content_text,
            )
            db.add(sub)

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_SUBMITTED",
            module="HOMEWORK",
            entity_type="HomeworkSubmission",
            entity_id=str(sub.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(sub)

        return self._hydrate_submission_response(db, sub)

    def list_submissions_for_homework(
        self,
        db: Session,
        school_id: UUID,
        homework_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> HomeworkSubmissionListResponse:
        hw = db.scalar(
            select(Homework).where(
                Homework.id == homework_id,
                Homework.school_id == school_id,
            )
        )
        if not hw:
            raise NotFoundException("Homework assignment not found.")

        stmt = select(HomeworkSubmission).where(
            HomeworkSubmission.school_id == school_id,
            HomeworkSubmission.homework_id == homework_id,
        )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size)

        offset = (page - 1) * page_size
        subs = db.scalars(
            stmt.order_by(HomeworkSubmission.submitted_at.desc()).offset(offset).limit(page_size)
        ).all()

        items = [self._hydrate_submission_response(db, s) for s in subs]

        return HomeworkSubmissionListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def grade_submission(
        self,
        db: Session,
        school_id: UUID,
        submission_id: UUID,
        current_user: IdentityUser,
        payload: HomeworkSubmissionGrade,
    ) -> HomeworkSubmissionResponse:
        sub = db.scalar(
            select(HomeworkSubmission).where(
                HomeworkSubmission.id == submission_id,
                HomeworkSubmission.school_id == school_id,
            )
        )
        if not sub:
            raise NotFoundException("Homework submission not found.")

        sub.grade = payload.grade
        sub.feedback = payload.feedback
        sub.status = SubmissionStatus.GRADED
        sub.reviewed_at = datetime.now(timezone.utc)
        sub.reviewed_by_id = current_user.id

        audit = AuditLog(
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="HOMEWORK_GRADED",
            module="HOMEWORK",
            entity_type="HomeworkSubmission",
            entity_id=str(sub.id),
        )
        db.add(audit)
        db.commit()
        db.refresh(sub)

        # Notify Student
        try:
            hw = db.get(Homework, sub.homework_id)
            title = hw.title if hw else "Homework"
            notification_service.create_in_app_notification(
                db=db,
                school_id=school_id,
                recipient_id=sub.student_id,
                recipient_type="STUDENT",
                template_key="general_announcement",
                variables={
                    "title": f"Homework Graded: {title}",
                    "message": f"Your submission was graded: {payload.grade}. Feedback: {payload.feedback or 'Good work.'}",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to dispatch grade notification: {e}")

        return self._hydrate_submission_response(db, sub)


homework_service = HomeworkService()
