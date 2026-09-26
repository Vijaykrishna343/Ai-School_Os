from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.identity.models.bootstrap_state import IdentityBootstrapState
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class IdentityBootstrapRepository(BaseRepository[IdentityBootstrapState]):
    """
    Repository for managing persistent platform and tenant bootstrap state.
    """

    def __init__(self) -> None:
        super().__init__(IdentityBootstrapState)

    def get_by_scope(
        self,
        db: Session,
        scope: str = "platform",
    ) -> IdentityBootstrapState | None:
        """
        Retrieve bootstrap state record by scope.
        """
        stmt = select(IdentityBootstrapState).where(
            IdentityBootstrapState.scope == scope,
            IdentityBootstrapState.is_deleted.is_(False),
        )
        return db.scalar(stmt)

    def get_by_scope_for_update(
        self,
        db: Session,
        scope: str = "platform",
    ) -> IdentityBootstrapState | None:
        """
        Retrieve bootstrap state record by scope with a row-level lock (FOR UPDATE).
        Uses populate_existing to ensure the ORM instance reflects the latest committed row.
        """
        stmt = (
            select(IdentityBootstrapState)
            .where(
                IdentityBootstrapState.scope == scope,
                IdentityBootstrapState.is_deleted.is_(False),
            )
            .with_for_update(of=IdentityBootstrapState)
            .execution_options(populate_existing=True)
        )
        return db.scalar(stmt)

    def is_platform_bootstrapped(
        self,
        db: Session,
    ) -> bool:
        """
        Check if the platform bootstrap has been permanently completed.

        Returns True if a persistent platform bootstrap state exists with is_completed=True.
        Returns False otherwise.
        """
        stmt = select(IdentityBootstrapState.is_completed).where(
            IdentityBootstrapState.scope == "platform",
            IdentityBootstrapState.is_deleted.is_(False),
        )
        result = db.scalar(stmt)
        return bool(result)

    def mark_completed_atomic(
        self,
        db: Session,
        completed_by_id: UUID | None = None,
        scope: str = "platform",
    ) -> bool:
        """
        Atomically transition is_completed from False to True.
        Returns True if this operation successfully transitioned the state.
        Returns False if another concurrent transaction already completed setup.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(IdentityBootstrapState)
            .where(
                IdentityBootstrapState.scope == scope,
                IdentityBootstrapState.is_completed.is_(False),
                IdentityBootstrapState.is_deleted.is_(False),
            )
            .values(
                is_completed=True,
                completed_at=now,
                completed_by_id=completed_by_id,
            )
        )
        result = db.execute(stmt)
        if result.rowcount == 0:
            existing = self.get_by_scope(db, scope=scope)
            if existing is None:
                try:
                    new_state = IdentityBootstrapState(
                        scope=scope,
                        is_completed=True,
                        completed_at=now,
                        completed_by_id=completed_by_id,
                    )
                    db.add(new_state)
                    db.flush()
                    return True
                except Exception:
                    return False
            return False

        db.flush()
        logger.info(
            "Persistent bootstrap state atomically marked COMPLETED for scope '%s' by user ID '%s'",
            scope,
            completed_by_id,
        )
        return True

    def mark_completed(
        self,
        db: Session,
        completed_by_id: UUID | None = None,
        scope: str = "platform",
    ) -> IdentityBootstrapState:
        """
        Mark the bootstrap state as permanently completed within the current transaction.
        """
        self.mark_completed_atomic(db, completed_by_id=completed_by_id, scope=scope)
        return self.get_by_scope(db, scope=scope)

    def ensure_initialized(
        self,
        db: Session,
        scope: str = "platform",
    ) -> IdentityBootstrapState:
        """
        Ensure a bootstrap state record exists for the given scope (default is_completed=False).
        """
        state = self.get_by_scope(db, scope=scope)
        if state is None:
            state = IdentityBootstrapState(
                scope=scope,
                is_completed=False,
            )
            db.add(state)
            db.flush()
        return state


identity_bootstrap_repository = IdentityBootstrapRepository()
