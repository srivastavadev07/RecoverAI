import random


def simulate_recovery(
    amount: float,
    recovery_probability: float,
    action: str,
    seed: int | None = None,
) -> dict:
    """
    Simulate the outcome of a recovery action.

    This is a synthetic evaluation environment.
    No real payment is processed.
    """

    if seed is not None:
        random.seed(seed)

    # Some actions are not considered recovery attempts.
    if action == "SEND_NOTIFICATION":
        return {
            "attempted": False,
            "recovered": False,
            "recovered_amount": 0.0,
            "status": "notification_only",
        }

    # Simulate whether the recovery succeeds.
    recovered = (
        random.random()
        < recovery_probability
    )

    if recovered:
        return {
            "attempted": True,
            "recovered": True,
            "recovered_amount": round(amount, 2),
            "status": "recovered",
        }

    return {
        "attempted": True,
        "recovered": False,
        "recovered_amount": 0.0,
        "status": "failed",
    }