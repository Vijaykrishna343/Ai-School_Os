"""
Audit Log Service and Endpoint — Phase 9.7
GET /api/v1/audit-logs  — Admin-only paginated audit trail
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser

router = APIRouter()


def write_audit_log(
    db: Session,
    school_id: UUID,
    user_id: UUID | None,
    user_email: str,
    action: str,
    module: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    status_code: int = 200,
    ip_address: str | None = None,
    details: str | None = None,
    role_name: str | None = None,
) -> None:
    """
    Write an audit log entry. Silently ignores errors to prevent
    audit logging from disrupting primary operations.
    """
    try:
        from app.models.audit_log import AuditLog
        log = AuditLog(
            school_id=school_id,
            user_id=user_id,
            user_email=user_email,
            role_name=role_name,
            action=action,
            module=module,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            status_code=status_code,
            ip_address=ip_address,
            details=details,
        )
        db.add(log)
        db.flush()
    except Exception:
        pass  # Never let audit logging break primary flows


@router.get("", summary="List Audit Logs (Admin Only)")
def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    school_id: UUID | None = Query(default=None),
    user_email: str | None = Query(default=None),
    action: str | None = Query(default=None),
    module: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
) -> JSONResponse:
    from sqlalchemy import select, func
    from app.models.audit_log import AuditLog

    q = select(AuditLog).where(AuditLog.is_deleted.is_(False))
    if current_user.is_super_admin:
        if school_id:
            q = q.where(AuditLog.school_id == school_id)
    else:
        q = q.where(AuditLog.school_id == current_user.school_id)

    if user_email:
        q = q.where(AuditLog.user_email.ilike(f"%{user_email}%"))
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if module:
        q = q.where(AuditLog.module.ilike(f"%{module}%"))
    if date_from:
        q = q.where(AuditLog.created_at >= date_from)
    if date_to:
        q = q.where(AuditLog.created_at <= date_to)

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar_one()
    offset = (page - 1) * page_size
    items = db.execute(q.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)).scalars().all()

    return JSONResponse(content={
        "success": True,
        "data": {
            "items": [
                {
                    "id": str(log.id),
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "user_email": log.user_email,
                    "role_name": log.role_name,
                    "action": log.action,
                    "module": log.module,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "status_code": log.status_code,
                    "ip_address": log.ip_address,
                    "details": log.details,
                }
                for log in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    })
