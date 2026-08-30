from app.agents.guardrails import (
    validate_recovery_action,
)


def main():

    allowed = validate_recovery_action(
        action="RETRY_PAYMENT",
        amount=4999,
        retry_count=0,
        opportunity_priority="HIGH",
    )

    print("Normal payment:")
    print(allowed)

    blocked_retry = validate_recovery_action(
        action="RETRY_PAYMENT",
        amount=4999,
        retry_count=2,
        opportunity_priority="HIGH",
    )

    print("\nRetry limit:")
    print(blocked_retry)

    blocked_amount = validate_recovery_action(
        action="RETRY_PAYMENT",
        amount=25000,
        retry_count=0,
        opportunity_priority="HIGH",
    )

    print("\nHigh-value payment:")
    print(blocked_amount)


if __name__ == "__main__":
    main()