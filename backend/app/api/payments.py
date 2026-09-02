from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.payment import Payment
from fastapi import APIRouter, Depends, HTTPException



router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)

@router.get("/{payment_id}")
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "payment_id": payment.id,
        "status": payment.status,
        "recovered": payment.recovered,
        "amount": payment.amount,
        "retry_count": payment.retry_count,
    }

    