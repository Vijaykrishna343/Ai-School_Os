from __future__ import annotations

import uuid
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException
from app.models.ai.ai_usage_limit import AIUsageLimit


class AIUsageService:
    """
    Atomic per-school token quota checking and accounting service.
    """

    @classmethod
    def get_or_create_usage_limit(cls, db: Session, school_id: uuid.UUID) -> AIUsageLimit:
        stmt = select(AIUsageLimit).where(AIUsageLimit.school_id == school_id).with_for_update()
        usage_limit = db.scalar(stmt)

        if not usage_limit:
            # Default monthly reset date to first day of next month
            today = date.today()
            first_next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)

            usage_limit = AIUsageLimit(
                id=uuid.uuid4(),
                school_id=school_id,
                monthly_token_quota=1000000,
                used_tokens_current_month=0,
                quota_reset_date=first_next_month,
                is_enabled=True,
            )
            db.add(usage_limit)
            db.commit()
            db.refresh(usage_limit)

        return usage_limit

    @classmethod
    def check_and_reserve_quota(cls, db: Session, school_id: uuid.UUID, estimated_tokens: int = 100) -> AIUsageLimit:
        usage_limit = cls.get_or_create_usage_limit(db, school_id)

        if not usage_limit.is_enabled:
            raise BadRequestException("AI capabilities are currently disabled for this school.")

        # Check for monthly reset
        today = date.today()
        if today >= usage_limit.quota_reset_date:
            usage_limit.used_tokens_current_month = 0
            first_next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            usage_limit.quota_reset_date = first_next_month
            db.commit()

        if usage_limit.used_tokens_current_month + estimated_tokens > usage_limit.monthly_token_quota:
            raise BadRequestException(
                f"Monthly AI token quota exhausted for this school. Quota: {usage_limit.monthly_token_quota}, Used: {usage_limit.used_tokens_current_month}."
            )

        return usage_limit

    @classmethod
    def record_usage(cls, db: Session, school_id: uuid.UUID, actual_tokens: int) -> None:
        stmt = select(AIUsageLimit).where(AIUsageLimit.school_id == school_id).with_for_update()
        usage_limit = db.scalar(stmt)
        if usage_limit:
            usage_limit.used_tokens_current_month += max(0, actual_tokens)
            db.commit()


ai_usage_service = AIUsageService()
