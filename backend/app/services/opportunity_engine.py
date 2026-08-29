def calculate_opportunity_score(
    expected_recovery: float,
    risk_score: float,
    retry_count: int,
    customer_total_spent: float,
) -> float:
    """
    Calculate a business-oriented opportunity score.

    Higher score = better recovery opportunity.
    """

    # -------------------------------------------------
    # 1. Expected recovery is the strongest signal.
    # -------------------------------------------------

    recovery_component = min(
        expected_recovery / 20000,
        1.0
    ) * 60

    # -------------------------------------------------
    # 2. Risk contributes to urgency.
    # -------------------------------------------------

    risk_component = (
        risk_score / 100
    ) * 20

    # -------------------------------------------------
    # 3. Customer value.
    # -------------------------------------------------

    customer_component = min(
        customer_total_spent / 50000,
        1.0
    ) * 15

    # -------------------------------------------------
    # 4. Penalize repeated retries.
    # -------------------------------------------------

    retry_penalty = min(
        retry_count * 5,
        10
    )

    score = (
        recovery_component
        + risk_component
        + customer_component
        - retry_penalty
    )

    return round(
        max(0, min(score, 100)),
        2
    )


def get_opportunity_priority(
    opportunity_score: float
) -> str:

    if opportunity_score >= 75:
        return "URGENT"

    if opportunity_score >= 50:
        return "HIGH"

    if opportunity_score >= 25:
        return "MEDIUM"

    return "LOW"