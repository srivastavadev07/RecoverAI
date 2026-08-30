def validate_recovery_action(
    action: str,
    amount: float,
    retry_count: int,
    opportunity_priority: str,
) -> tuple[bool, str]:

    # Never retry a payment more than 2 times
    if action == "RETRY_PAYMENT" and retry_count >= 2:
        return (
            False,
            "Retry limit reached for this payment."
        )

    # Large-value actions require human approval
    if (
        action == "RETRY_PAYMENT"
        and amount > 20000
    ):
        return (
            False,
            "Payment exceeds automatic retry limit. "
            "Merchant approval required."
        )

    # Only meaningful opportunities should be
    # automatically acted upon
    if opportunity_priority == "LOW":
        return (
            False,
            "Low-priority opportunity requires "
            "manual review."
        )

    return True, "Action approved."