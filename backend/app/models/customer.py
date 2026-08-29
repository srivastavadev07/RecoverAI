from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        String,
        unique=True,
        index=True
    )

    name = Column(String)

    email = Column(String)

    total_payments = Column(
        Integer,
        default=0
    )

    successful_payments = Column(
        Integer,
        default=0
    )

    failed_payments = Column(
        Integer,
        default=0
    )

    total_spent = Column(
        Float,
        default=0
    )

    last_payment_at = Column(
        DateTime,
        nullable=True
    )