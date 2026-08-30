from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.audit_log import AuditLog


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )

    return logs