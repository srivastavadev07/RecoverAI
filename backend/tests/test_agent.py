from app.agents.recovery_agent import (
    analyze_opportunity,
)


def main():

    opportunity = {
        "payment_id": 123,
        "customer_id": "CUST_1001",
        "amount": 4999,
        "currency": "INR",
        "failure_reason": "bank_declined",
        "payment_method": "upi",
        "retry_count": 0,
        "risk_score": 73,
        "recovery_probability": 0.7475,
        "revenue_at_risk": 4999,
        "expected_recovery": 3736.75,
        "priority": "MEDIUM",
        "recommended_action": "RETRY_PAYMENT",
        "opportunity_score": 68,
        "opportunity_priority": "HIGH",
    }

    result = analyze_opportunity(
        opportunity
    )

    print("\n===== RECOVERAI AGENT =====")
    print(result)


if __name__ == "__main__":
    main()