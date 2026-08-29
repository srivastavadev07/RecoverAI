
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.payment import Payment


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.get("/")
def get_payments(
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .limit(20)
        .all()
    )

    return payments