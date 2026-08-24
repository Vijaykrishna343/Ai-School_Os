from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.fees import PaymentMode
from app.common.exceptions import NotFoundException, ValidationException
from app.common.logger.logger import get_logger
from app.models.fees.cash_session import CashSession
from app.models.fees.fee_payment import FeePayment
from app.schemas.fees.cash_session import (
    CashSessionCloseRequest,
    CashSessionOpenRequest,
    CashSessionResponse,
)

logger = get_logger(__name__)


class CashSessionService:
    def open_session(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        data: CashSessionOpenRequest,
    ) -> CashSessionResponse:
        existing_open = db.scalar(
            select(CashSession).where(
                CashSession.school_id == school_id,
                CashSession.opened_by_user_id == user_id,
                CashSession.status == "OPEN",
                CashSession.is_deleted.is_(False),
            )
        )
        if existing_open:
            raise ValidationException("An active cash drawer session is already open.")

        s_date = data.session_date or date.today()
        session = CashSession(
            school_id=school_id,
            opened_by_user_id=user_id,
            session_date=s_date,
            status="OPEN",
            opening_balance=data.opening_balance,
            expected_cash_collected=Decimal("0.00"),
            expected_non_cash_collected=Decimal("0.00"),
            opened_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return self._format_response(db, session)

    def get_active_session(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
    ) -> CashSessionResponse:
        session = db.scalar(
            select(CashSession).where(
                CashSession.school_id == school_id,
                CashSession.opened_by_user_id == user_id,
                CashSession.status == "OPEN",
                CashSession.is_deleted.is_(False),
            )
        )
        if not session:
            raise NotFoundException("Active Cash Drawer Session", str(user_id))

        return self._format_response(db, session)

    def close_session(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        session_id: UUID,
        data: CashSessionCloseRequest,
    ) -> CashSessionResponse:
        session = db.scalar(
            select(CashSession).where(
                CashSession.id == session_id,
                CashSession.school_id == school_id,
                CashSession.is_deleted.is_(False),
            )
        )
        if not session:
            raise NotFoundException("Cash Session", str(session_id))

        if session.status != "OPEN":
            raise ValidationException("Cannot close cash session because it is already closed.")

        cash_sum, non_cash_sum = self._calculate_payment_totals(db, school_id, session.session_date)

        session.expected_cash_collected = cash_sum
        session.expected_non_cash_collected = non_cash_sum
        session.actual_counted_cash = data.actual_counted_cash

        expected_total = session.opening_balance + cash_sum
        session.variance = data.actual_counted_cash - expected_total

        if data.notes is not None:
            session.notes = data.notes

        session.status = "CLOSED"
        session.closed_by_user_id = user_id
        session.closed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(session)
        return self._format_response(db, session)

    def _calculate_payment_totals(
        self,
        db: Session,
        school_id: UUID,
        session_date: date,
    ) -> tuple[Decimal, Decimal]:
        cash_query = select(func.coalesce(func.sum(FeePayment.amount), Decimal("0.00"))).where(
            FeePayment.school_id == school_id,
            FeePayment.payment_date == session_date,
            FeePayment.payment_mode == PaymentMode.CASH,
            FeePayment.is_deleted.is_(False),
        )
        cash_sum = Decimal(str(db.scalar(cash_query) or "0.00"))

        non_cash_query = select(func.coalesce(func.sum(FeePayment.amount), Decimal("0.00"))).where(
            FeePayment.school_id == school_id,
            FeePayment.payment_date == session_date,
            FeePayment.payment_mode != PaymentMode.CASH,
            FeePayment.is_deleted.is_(False),
        )
        non_cash_sum = Decimal(str(db.scalar(non_cash_query) or "0.00"))

        return cash_sum, non_cash_sum

    def _format_response(self, db: Session, session: CashSession) -> CashSessionResponse:
        cash_sum, non_cash_sum = self._calculate_payment_totals(db, session.school_id, session.session_date)
        expected_total = session.opening_balance + cash_sum

        variance = session.variance
        if session.status == "OPEN":
            variance = None

        actual_cash = session.actual_counted_cash if session.status == "CLOSED" else None

        return CashSessionResponse(
            id=session.id,
            school_id=session.school_id,
            opened_by_user_id=session.opened_by_user_id,
            closed_by_user_id=session.closed_by_user_id,
            session_date=session.session_date,
            status=session.status,
            opening_balance=session.opening_balance,
            expected_cash_collected=cash_sum,
            expected_non_cash_collected=non_cash_sum,
            expected_total_cash=expected_total,
            actual_counted_cash=actual_cash,
            variance=variance,
            notes=session.notes,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
        )


cash_session_service = CashSessionService()
