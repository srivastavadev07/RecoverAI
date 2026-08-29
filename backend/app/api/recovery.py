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
    prefix="/recovery",
    tags=["Revenue Recovery"],
)


@router.get("/opportunities")
def get_recovery_opportunities(
    db: Session = Depends(get_db),
):
    payments = (
        db.query(Payment)
        .filter(Payment.status == "failed")
        .all()
    )

    opportunities = []

    for payment in payments:

        customer = (
            db.query(Customer)
            .filter(
                Customer.customer_id == payment.customer_id
            )
            .first()
        )

        if customer is None:
            continue

        # Calculate risk for this payment
        result = calculate_risk_score(
            amount=payment.amount,
            failure_reason=payment.failure_reason,
            retry_count=payment.retry_count,
            customer_failed_payments=customer.failed_payments,
            customer_successful_payments=customer.successful_payments,
            customer_total_spent=customer.total_spent,
        )

        # Calculate business opportunity score
        opportunity_score = calculate_opportunity_score(
            expected_recovery=result.expected_recovery,
            risk_score=result.risk_score,
            retry_count=payment.retry_count,
            customer_total_spent=customer.total_spent,
        )

        # Determine opportunity priority
        opportunity_priority = get_opportunity_priority(
            opportunity_score
        )

        opportunities.append(
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "failure_reason": payment.failure_reason,
                "payment_method": payment.payment_method,
                "retry_count": payment.retry_count,

                # Risk information
                "risk_score": result.risk_score,
                "recovery_probability": result.recovery_probability,
                "revenue_at_risk": result.revenue_at_risk,
                "expected_recovery": result.expected_recovery,

                # Recommended action
                "priority": result.priority,
                "recommended_action": result.recommended_action,

                # Opportunity information
                "opportunity_score": opportunity_score,
                "opportunity_priority": opportunity_priority,
            }
        )

    # Highest opportunity score first
    opportunities.sort(
        key=lambda x: x["opportunity_score"],
        reverse=True,
    )

    return {
        "total_opportunities": len(opportunities),
        "opportunities": opportunities,
    }