from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.customer import Customer
from app.models.payment import Payment
from app.services.risk_engine import calculate_risk_score
from app.services.opportunity_engine import (
    calculate_opportunity_score,
    get_opportunity_priority,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/recovery-summary")
def recovery_summary(
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .filter(Payment.status == "failed")
        .all()
    )

    total_revenue_at_risk = 0
    total_expected_recovery = 0
    urgent_opportunities = 0

    action_counter = Counter()

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
            customer_failed_payments=customer.failed_payments,
            customer_successful_payments=customer.successful_payments,
            customer_total_spent=customer.total_spent,
        )

        opportunity_score = calculate_opportunity_score(
            expected_recovery=result.expected_recovery,
            risk_score=result.risk_score,
            retry_count=payment.retry_count,
            customer_total_spent=customer.total_spent,
        )

        opportunity_priority = get_opportunity_priority(
            opportunity_score
        )

        total_revenue_at_risk += result.revenue_at_risk
        total_expected_recovery += result.expected_recovery

        if opportunity_priority == "URGENT":
            urgent_opportunities += 1

        action_counter[
            result.recommended_action
        ] += 1

    return {
        "failed_payments": len(payments),
        "revenue_at_risk": round(
            total_revenue_at_risk,
            2,
        ),
        "expected_recovery": round(
            total_expected_recovery,
            2,
        ),
        "urgent_opportunities": urgent_opportunities,
        "recommended_actions": dict(
            action_counter
        ),
    }