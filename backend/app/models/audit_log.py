from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_id = Column(
        Integer,
        nullable=True,
    )

    action = Column(String)

    status = Column(String)

    reason = Column(Text)

    details = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )