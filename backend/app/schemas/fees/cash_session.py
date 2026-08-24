from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CashSessionOpenRequest(BaseModel):
    opening_balance: Decimal = Field(default=Decimal("0.00"), ge=0)
    session_date: date | None = None


class CashSessionCloseRequest(BaseModel):
    actual_counted_cash: Decimal = Field(..., ge=0)
    notes: str | None = Field(default=None, max_length=500)


class CashSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    opened_by_user_id: UUID
    closed_by_user_id: UUID | None = None
    session_date: date
    status: str
    opening_balance: Decimal
    expected_cash_collected: Decimal
    expected_non_cash_collected: Decimal
    expected_total_cash: Decimal
    actual_counted_cash: Decimal | None = None
    variance: Decimal | None = None
    notes: str | None = None
    opened_at: datetime
    closed_at: datetime | None = None
