from dataclasses import dataclass


@dataclass
class RiskResult:
    risk_score: float
    recovery_probability: float
    revenue_at_risk: float
    expected_recovery: float
    priority: str
    recommended_action: str


def calculate_risk_score(
    amount: float,
    failure_reason: str | None,
    retry_count: int,
    customer_failed_payments: int,
    customer_successful_payments: int,
    customer_total_spent: float,
) -> RiskResult:

    score = 0.0

    # -------------------------------------------------
    # 1. Transaction amount
    # Higher-value failed payments deserve more attention.
    # -------------------------------------------------
    if amount >= 10000:
        score += 30
    elif amount >= 5000:
        score += 25
    elif amount >= 2000:
        score += 18
    else:
        score += 10

    # -------------------------------------------------
    # 2. Failure reason
    # Some failures are more recoverable than others.
    # -------------------------------------------------
    failure_weights = {
        "insufficient_funds": 20,
        "bank_declined": 18,
        "payment_timeout": 15,
        "technical_error": 12,
        "authentication_failed": 8,
    }

    score += failure_weights.get(
        failure_reason,
        10
    )

    # -------------------------------------------------
    # 3. Retry history
    # Repeated failures increase urgency, but too many
    # retries can indicate that we should stop.
    # -------------------------------------------------
    if retry_count == 0:
        score += 15
    elif retry_count == 1:
        score += 10
    elif retry_count == 2:
        score += 5

    # -------------------------------------------------
    # 4. Customer payment history
    # A customer with successful historical payments
    # is generally more valuable for recovery.
    # -------------------------------------------------
    total_attempts = (
        customer_failed_payments
        + customer_successful_payments
    )

    if total_attempts > 0:

        success_rate = (
            customer_successful_payments
            / total_attempts
        )

        if success_rate >= 0.8:
            score += 15
        elif success_rate >= 0.5:
            score += 10
        else:
            score += 5

    # -------------------------------------------------
    # 5. Customer lifetime value
    # High-value customers deserve additional priority.
    # -------------------------------------------------
    if customer_total_spent >= 50000:
        score += 10
    elif customer_total_spent >= 20000:
        score += 7
    elif customer_total_spent >= 10000:
        score += 5

    # Cap score between 0 and 100.
    score = min(score, 100)

    # -------------------------------------------------
    # Recovery probability
    # Convert risk signals into an estimated probability.
    # -------------------------------------------------

    recovery_probability = min(
        0.95,
        max(
            0.10,
            0.20 + (score / 100) * 0.75
        )
    )

    # -------------------------------------------------
    # Expected recovery
    # -------------------------------------------------

    revenue_at_risk = amount

    expected_recovery = (
        revenue_at_risk
        * recovery_probability
    )

    # -------------------------------------------------
    # Priority
    # -------------------------------------------------

    if score >= 75:
        priority = "HIGH"
    elif score >= 50:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # -------------------------------------------------
    # Recommended action
    # -------------------------------------------------

    if retry_count >= 2:
        recommended_action = "SEND_PAYMENT_LINK"

    elif failure_reason == "insufficient_funds":
        recommended_action = "RETRY_LATER"

    elif failure_reason == "bank_declined":
        recommended_action = "RETRY_PAYMENT"

    elif failure_reason == "payment_timeout":
        recommended_action = "RETRY_PAYMENT"

    elif failure_reason == "technical_error":
        recommended_action = "RETRY_PAYMENT"

    elif failure_reason == "authentication_failed":
        recommended_action = "SEND_PAYMENT_LINK"

    else:
        recommended_action = "SEND_PAYMENT_LINK"

    return RiskResult(
        risk_score=round(score, 2),
        recovery_probability=round(
            recovery_probability,
            4
        ),
        revenue_at_risk=round(
            revenue_at_risk,
            2
        ),
        expected_recovery=round(
            expected_recovery,
            2
        ),
        priority=priority,
        recommended_action=recommended_action,
    )