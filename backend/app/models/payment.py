from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(String, index=True)

    amount = Column(Float)

    currency = Column(String, default="INR")

    status = Column(String)

    failure_reason = Column(String, nullable=True)

    payment_method = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    retry_count = Column(Integer, default=0)

    recovered = Column(Integer, default=0)