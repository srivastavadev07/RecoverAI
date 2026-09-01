from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_event import RecoveryEvent

from app.services.risk_engine import (
    calculate_risk_score,
)

from app.services.opportunity_engine import (
    calculate_opportunity_score,
    get_opportunity_priority,
)

from app.agents.recovery_agent import (
    analyze_opportunity,
    execute_selected_tool,
)

from app.agents.guardrails import (
    validate_recovery_action,
)

from app.services.audit_service import (
    record_action,
)

from app.services.razorpay_service import (
    create_payment_link as create_razorpay_payment_link,
)


router = APIRouter(
    prefix="/recovery",
    tags=["Revenue Recovery"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class RecoveryExecutionRequest(BaseModel):
    action: Literal[
        "retry_payment",
        "create_payment_link",
        "send_notification",
    ]


# =========================================================
# GET ALL RECOVERY OPPORTUNITIES
# =========================================================

@router.get("/opportunities")
def get_recovery_opportunities(
    db: Session = Depends(get_db),
):
    """
    Return all failed payments ranked by
    Recovery Opportunity Score.
    """

    payments = (
        db.query(Payment)
        .filter(
            Payment.status == "failed"
        )
        .all()
    )

    opportunities = []

    for payment in payments:

        # -------------------------------------------------
        # Find customer
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Calculate risk
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Calculate opportunity score
        # -------------------------------------------------

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

        opportunity_priority = (
            get_opportunity_priority(
                opportunity_score
            )
        )

        # -------------------------------------------------
        # Build opportunity
        # -------------------------------------------------

        opportunities.append(
            {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "failure_reason": (
                    payment.failure_reason
                ),
                "payment_method": (
                    payment.payment_method
                ),
                "retry_count": payment.retry_count,

                # Risk information
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

                # Deterministic recommendation
                "priority": result.priority,
                "recommended_action": (
                    result.recommended_action
                ),

                # Opportunity information
                "opportunity_score": (
                    opportunity_score
                ),
                "opportunity_priority": (
                    opportunity_priority
                ),
            }
        )

    # -----------------------------------------------------
    # Sort highest opportunity first
    # -----------------------------------------------------

    opportunities.sort(
        key=lambda x: x["opportunity_score"],
        reverse=True,
    )

    return {
        "total_opportunities": len(
            opportunities
        ),
        "opportunities": opportunities,
    }


# =========================================================
# AI ANALYSIS
# =========================================================

@router.get("/analyze/{payment_id}")
def analyze_payment(
    payment_id: int,
    db: Session = Depends(get_db),
):
    """
    Ask Gemini to recommend a recovery action.

    IMPORTANT:
    This endpoint ONLY analyzes.
    It does NOT execute any recovery action.
    """

    # -----------------------------------------------------
    # Find payment
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if payment is None:
        return {
            "success": False,
            "error": "Payment not found",
        }

    # -----------------------------------------------------
    # Make sure payment is failed
    # -----------------------------------------------------

    if payment.status != "failed":
        return {
            "success": False,
            "error": (
                "Only failed payments can be "
                "analyzed for recovery."
            ),
        }

    # -----------------------------------------------------
    # Find customer
    # -----------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_id
            == payment.customer_id
        )
        .first()
    )

    if customer is None:
        return {
            "success": False,
            "error": "Customer not found",
        }

    # -----------------------------------------------------
    # Calculate risk
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Calculate opportunity score
    # -----------------------------------------------------

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

    opportunity_priority = (
        get_opportunity_priority(
            opportunity_score
        )
    )

    # -----------------------------------------------------
    # Build trusted opportunity object
    # -----------------------------------------------------

    opportunity = {
        "payment_id": payment.id,
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "currency": payment.currency,
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

        "priority": result.priority,

        "recommended_action": (
            result.recommended_action
        ),

        "opportunity_score": (
            opportunity_score
        ),

        "opportunity_priority": (
            opportunity_priority
        ),
    }

    # -----------------------------------------------------
    # AI DECISION ONLY
    # -----------------------------------------------------

    return analyze_opportunity(
        opportunity
    )


# =========================================================
# EXECUTE RECOVERY ACTION
# =========================================================

@router.post("/execute/{payment_id}")
def execute_recovery(
    payment_id: int,
    request: RecoveryExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a merchant-approved recovery action.

    Flow:

    Payment
        ↓
    Recalculate risk
        ↓
    Validate action
        ↓
    Guardrails
        ↓
    Recovery tool / Razorpay
        ↓
    Persist recovery event
        ↓
    Audit log
    """

    # -----------------------------------------------------
    # Find payment
    # -----------------------------------------------------

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if payment is None:
        return {
            "success": False,
            "error": "Payment not found",
        }

    # -----------------------------------------------------
    # Only failed payments can enter recovery
    # -----------------------------------------------------

    if payment.status != "failed":
        return {
            "success": False,
            "error": (
                "Only failed payments can "
                "enter recovery."
            ),
        }

    # -----------------------------------------------------
    # Prevent duplicate recovery after payment is recovered
    # -----------------------------------------------------

    if payment.recovered == 1:
        return {
            "success": False,
            "error": (
                "This payment has already "
                "been recovered."
            ),
        }

    # -----------------------------------------------------
    # Find customer
    # -----------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(
            Customer.customer_id
            == payment.customer_id
        )
        .first()
    )

    if customer is None:
        return {
            "success": False,
            "error": "Customer not found",
        }

    # =====================================================
    # RECALCULATE RISK
    # =====================================================

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

    # =====================================================
    # CALCULATE OPPORTUNITY SCORE
    # =====================================================

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

    opportunity_priority = (
        get_opportunity_priority(
            opportunity_score
        )
    )

    # =====================================================
    # TRUSTED OPPORTUNITY OBJECT
    # =====================================================

    opportunity = {
        "payment_id": payment.id,
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "currency": payment.currency,
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

        "priority": result.priority,

        "recommended_action": (
            result.recommended_action
        ),

        "opportunity_score": (
            opportunity_score
        ),

        "opportunity_priority": (
            opportunity_priority
        ),
    }

    # =====================================================
    # BUILD TOOL ARGUMENTS
    # =====================================================

    if request.action == "retry_payment":

        arguments = {
            "payment_id": payment.id,
        }

    elif request.action == "create_payment_link":

        arguments = {
            "payment_id": payment.id,
            "amount": payment.amount,
        }

    else:

        arguments = {
            "customer_id": payment.customer_id,
            "message": (
                "Your payment requires attention. "
                "Please complete your payment to "
                "avoid interruption of service."
            ),
        }

    # =====================================================
    # EXECUTE RECOVERY ACTION
    # =====================================================

    # -----------------------------------------------------
    # RAZORPAY PAYMENT LINK
    # -----------------------------------------------------

    if request.action == "create_payment_link":

        # -------------------------------------------------
        # Guardrail FIRST
        # -------------------------------------------------

        allowed, reason = validate_recovery_action(
            action="SEND_PAYMENT_LINK",
            amount=payment.amount,
            retry_count=payment.retry_count,
            opportunity_priority=(
                opportunity_priority
            ),
        )

        if not allowed:

            tool_result = {
                "success": False,
                "blocked": True,
                "tool": "create_payment_link",
                "reason": reason,
            }

        else:

            try:

                # -----------------------------------------
                # Create actual Razorpay Test Mode link
                # -----------------------------------------

                razorpay_result = (
                    create_razorpay_payment_link(
                        amount=payment.amount,
                        customer_id=(
                            payment.customer_id
                        ),
                        payment_id=payment.id,
                    )
                )

                tool_result = {
                    "success": True,
                    "tool": "create_payment_link",
                    "provider": "razorpay",
                    "payment_id": payment.id,

                    "razorpay_payment_link_id": (
                        razorpay_result.get("id")
                    ),

                    "payment_link": (
                        razorpay_result.get(
                            "short_url"
                        )
                    ),

                    "status": (
                        razorpay_result.get(
                            "status"
                        )
                    ),
                }

            except Exception as exc:

                tool_result = {
                    "success": False,
                    "tool": "create_payment_link",
                    "provider": "razorpay",
                    "error": str(exc),
                }

    # -----------------------------------------------------
    # OTHER RECOVERY TOOLS
    # -----------------------------------------------------

    else:

        tool_result = execute_selected_tool(
            tool_name=request.action,
            arguments=arguments,
            opportunity=opportunity,
        )

    # =====================================================
    # DETERMINE EXECUTION STATUS
    # =====================================================

    if tool_result.get("blocked"):

        audit_status = "BLOCKED"

    elif tool_result.get("success"):

        audit_status = "SUCCESS"

    else:

        audit_status = "FAILED"

    # =====================================================
    # DETERMINE WHETHER MONEY WAS ACTUALLY RECOVERED
    # =====================================================

    # IMPORTANT:
    #
    # Creating a payment link is NOT a recovery.
    #
    # The money is considered recovered only when the
    # Razorpay webhook confirms payment_link.paid.
    #
    # Therefore this must stay False here unless a tool
    # explicitly says:
    #
    #     "recovered": True

    payment_recovered = (
        tool_result.get(
            "recovered",
            False,
        )
        is True
    )

    recovered_amount = 0.0

    if payment_recovered:

        recovered_amount = payment.amount

        payment.recovered = 1
        payment.status = "recovered"

    # =====================================================
    # UPDATE RETRY COUNT
    # =====================================================

    if (
        request.action == "retry_payment"
        and tool_result.get("success")
    ):

        payment.retry_count += 1

    # =====================================================
    # DETERMINE RECOVERY EVENT STATUS
    # =====================================================

    if payment_recovered:

        recovery_event_status = "RECOVERED"

    elif tool_result.get("blocked"):

        recovery_event_status = "BLOCKED"

    elif tool_result.get("success"):

        recovery_event_status = "ACTION_EXECUTED"

    else:

        recovery_event_status = "FAILED"

    # =====================================================
    # CREATE PERSISTENT RECOVERY EVENT
    # =====================================================

    recovery_event = RecoveryEvent(
        payment_id=payment.id,
        action=request.action,
        amount=payment.amount,
        status=recovery_event_status,
        recovered_amount=recovered_amount,
    )

    db.add(recovery_event)

    # =====================================================
    # SAVE DATABASE CHANGES
    # =====================================================

    db.commit()

    # =====================================================
    # RECORD AUDIT EVENT
    # =====================================================

    record_action(
        db=db,
        payment_id=payment.id,
        action=request.action,
        status=audit_status,
        reason=tool_result.get(
            "reason",
            (
                "Recovery action executed."
                if tool_result.get("success")
                else "Recovery action failed."
            ),
        ),
        details=tool_result,
    )

    # =====================================================
    # RETURN RESULT
    # =====================================================

    return {
        "success": tool_result.get(
            "success",
            False,
        ),

        "payment_id": payment.id,

        "action": request.action,

        "tool_result": tool_result,

        "audit_status": audit_status,

        "recovery_status": (
            recovery_event_status
        ),

        "recovered": payment_recovered,

        "recovered_amount": recovered_amount,

        "retry_count": payment.retry_count,
    }