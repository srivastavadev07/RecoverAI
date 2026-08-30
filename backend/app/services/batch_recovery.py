from app.services.recovery_simulator import (
    simulate_recovery,
)


def evaluate_batch(opportunities: list[dict]) -> dict:
    """
    Evaluate recovery performance over a batch
    of recovery opportunities.
    """

    total_payments = len(opportunities)

    total_revenue_at_risk = 0.0

    total_expected_recovery = 0.0

    recovery_attempts = 0

    successful_recoveries = 0

    revenue_recovered = 0.0

    blocked_actions = 0

    action_counts = {}

    for index, opportunity in enumerate(
        opportunities
    ):

        total_revenue_at_risk += (
            opportunity["revenue_at_risk"]
        )

        total_expected_recovery += (
            opportunity["expected_recovery"]
        )

        action = opportunity[
            "recommended_action"
        ]

        action_counts[action] = (
            action_counts.get(action, 0) + 1
        )

        # ---------------------------------------------
        # Simulate recovery
        # ---------------------------------------------

        if opportunity["retry_count"] >= 2:

            blocked_actions += 1

            continue

        if (
            opportunity["amount"] > 20000
            and action == "RETRY_PAYMENT"
        ):

            blocked_actions += 1

            continue

        result = simulate_recovery(
            amount=opportunity["amount"],
            recovery_probability=(
                opportunity[
                    "recovery_probability"
                ]
            ),
            action=action,
            seed=index,
        )

        if result["attempted"]:
            recovery_attempts += 1

        if result["recovered"]:

            successful_recoveries += 1

            revenue_recovered += (
                result["recovered_amount"]
            )

    recovery_rate = (
        successful_recoveries
        / recovery_attempts
        if recovery_attempts
        else 0
    )

    return {
        "total_payments": total_payments,
        "revenue_at_risk": round(
            total_revenue_at_risk,
            2,
        ),
        "expected_recovery": round(
            total_expected_recovery,
            2,
        ),
        "recovery_attempts": recovery_attempts,
        "successful_recoveries": (
            successful_recoveries
        ),
        "revenue_recovered": round(
            revenue_recovered,
            2,
        ),
        "recovery_rate": round(
            recovery_rate,
            4,
        ),
        "blocked_actions": blocked_actions,
        "action_counts": action_counts,
    }