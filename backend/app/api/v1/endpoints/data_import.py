"""
Data Import Endpoint — Phase 9.1
POST /api/v1/import/{entity_type}
"""
from fastapi import APIRouter, Depends, File, UploadFile, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.services.import_service import import_data, ENTITY_SCHEMAS

router = APIRouter()

ENTITY_PERMISSION = {
    "students": "student.create",
    "teachers": "teacher.create",
    "parents": "parent.create",
}


@router.post(
    "/{entity_type}",
    summary="Bulk Import School Data",
    status_code=status.HTTP_200_OK,
)
def bulk_import(
    entity_type: str = Path(..., description="Entity to import: students | teachers | parents"),
    file: UploadFile = File(..., description="CSV or XLSX file"),
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Bulk import school data from a CSV or XLSX file.

    Supports entity types: students, teachers, parents.

    Returns an import summary with per-row error details.
    """
    if entity_type not in ENTITY_SCHEMAS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Unsupported entity type '{entity_type}'. Valid: {list(ENTITY_SCHEMAS)}"},
        )

    # Dynamic permission enforcement per entity_type (Fixes RBAC-001)
    required_perm = ENTITY_PERMISSION.get(entity_type)
    if not required_perm:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"No permission mapping for entity type '{entity_type}'."},
        )

    # Enforce permission dynamically
    require_permission(required_perm)(current_user=current_user, db=db)

    content = file.file.read()
    filename = file.filename or "upload.csv"

    result = import_data(
        db=db,
        entity_type=entity_type,
        file_content=content,
        filename=filename,
        school_id=current_user.school_id,
    )

    # Commit if there were inserts
    if result.inserted_rows > 0:
        db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "data": result.to_dict(),
        },
    )


@router.get(
    "/schema/{entity_type}",
    summary="Get Import Schema",
    status_code=status.HTTP_200_OK,
)
def get_import_schema(
    entity_type: str = Path(...),
    current_user: IdentityUser = Depends(require_permission("student.view")),
) -> JSONResponse:
    """
    Returns the expected CSV column schema for the given entity type.
    """
    if entity_type not in ENTITY_SCHEMAS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Unknown entity type: {entity_type}"},
        )
    schema = ENTITY_SCHEMAS[entity_type]
    return JSONResponse(content={
        "entity_type": entity_type,
        "required_columns": sorted(schema["required"]),
        "optional_columns": sorted(schema["optional"]),
        "description": schema["description"],
    })
