import json

from app.models.audit_log import AuditLog


def record_action(
    db,
    payment_id: int | None,
    action: str,
    status: str,
    reason: str,
    details: dict | None = None,
):

    log = AuditLog(
        payment_id=payment_id,
        action=action,
        status=status,
        reason=reason,
        details=(
            json.dumps(details)
            if details is not None
            else None
        ),
    )

    db.add(log)
    db.commit()

    return log