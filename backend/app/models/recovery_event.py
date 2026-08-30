from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.database import Base


class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    action = Column(String, nullable=False)

    amount = Column(Float, nullable=False)

    status = Column(String, nullable=False)

    recovered_amount = Column(
        Float,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )