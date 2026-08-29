from app.services.risk_engine import calculate_risk_score


result = calculate_risk_score(
    amount=4999,
    failure_reason="bank_declined",
    retry_count=0,
    customer_failed_payments=1,
    customer_successful_payments=5,
    customer_total_spent=32000,
)

print("Risk Score:", result.risk_score)
print("Recovery Probability:", result.recovery_probability)
print("Revenue at Risk:", result.revenue_at_risk)
print("Expected Recovery:", result.expected_recovery)
print("Priority:", result.priority)
print("Recommended Action:", result.recommended_action)