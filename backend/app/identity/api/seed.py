from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.seeders import seed_identity

router = APIRouter(
    prefix="/identity",
    tags=["Identity Seeding"],
)


class SeedSummaryResponse(BaseModel):
    permissions_created: int = Field(
        ..., description="Number of permissions created"
    )
    permissions_skipped: int = Field(
        ..., description="Number of existing permissions skipped"
    )
    roles_created: int = Field(
        ..., description="Number of system roles created"
    )
    roles_skipped: int = Field(
        ..., description="Number of existing system roles skipped"
    )
    assignments_created: int = Field(
        ..., description="Number of role-permission assignments created"
    )
    assignments_skipped: int = Field(
        ..., description="Number of existing role-permission assignments skipped"
    )


@router.post(
    "/seed",
    response_model=SeedSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Seed Identity Data",
    description=(
        "Seed default permissions, system roles, and role-permission matrix assignments. "
        "Idempotent and safe to execute multiple times."
    ),
    dependencies=[
        Depends(require_permission("permission.create")),
    ],
)
def seed_identity_data(
    db: Session = Depends(get_db),
) -> SeedSummaryResponse:
    """Execute master identity seeder."""
    summary = seed_identity(db)
    db.commit()
    return SeedSummaryResponse(**summary)
