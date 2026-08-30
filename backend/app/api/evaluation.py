from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.customer import Customer
from app.models.payment import Payment

from app.services.risk_engine import (
    calculate_risk_score,
)

from app.services.opportunity_engine import (
    calculate_opportunity_score,
)

from app.services.batch_recovery import (
    evaluate_batch,
)


router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


@router.get("/recovery")
def evaluate_recovery(
    db: Session = Depends(get_db),
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.status == "failed"
        )
        .all()
    )

    opportunities = []

    for payment in payments:

        customer = (
            db.query(Customer)
            .filter(
                Customer.customer_id
                == payment.customer_id
            )
            .first()
        )

        if customer is None:
            continue

        result = calculate_risk_score(
            amount=payment.amount,
            failure_reason=payment.failure_reason,
            retry_count=payment.retry_count,
            customer_failed_payments=(
                customer.failed_payments
            ),
            customer_successful_payments=(
                customer.successful_payments
            ),
            customer_total_spent=(
                customer.total_spent
            ),
        )

        opportunity_score = (
            calculate_opportunity_score(
                expected_recovery=(
                    result.expected_recovery
                ),
                risk_score=result.risk_score,
                retry_count=payment.retry_count,
                customer_total_spent=(
                    customer.total_spent
                ),
            )
        )

        opportunities.append(
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": payment.amount,
                "failure_reason": (
                    payment.failure_reason
                ),
                "payment_method": (
                    payment.payment_method
                ),
                "retry_count": payment.retry_count,
                "risk_score": result.risk_score,
                "recovery_probability": (
                    result.recovery_probability
                ),
                "revenue_at_risk": (
                    result.revenue_at_risk
                ),
                "expected_recovery": (
                    result.expected_recovery
                ),
                "recommended_action": (
                    result.recommended_action
                ),
                "opportunity_score": (
                    opportunity_score
                ),
            }
        )

    return evaluate_batch(
        opportunities
    )