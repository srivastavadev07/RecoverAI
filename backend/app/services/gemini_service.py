import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


MODEL_NAME = "gemini-2.5-flash"


def analyze_recovery_opportunity(
    opportunity: dict,
) -> str:

    prompt = f"""
You are RecoverAI, an AI revenue recovery agent.

Your job is to analyze a failed payment and recommend
the safest and most appropriate recovery action.

IMPORTANT RULES:
- Do not invent payment information.
- Use only the data provided below.
- Do not claim that money was recovered.
- Do not execute any payment action yourself.
- Return a concise business decision.

Payment information:

Payment ID:
{opportunity["payment_id"]}

Customer ID:
{opportunity["customer_id"]}

Amount:
₹{opportunity["amount"]}

Failure reason:
{opportunity["failure_reason"]}

Payment method:
{opportunity["payment_method"]}

Retry count:
{opportunity["retry_count"]}

Risk score:
{opportunity["risk_score"]}

Recovery probability:
{opportunity["recovery_probability"]}

Revenue at risk:
₹{opportunity["revenue_at_risk"]}

Expected recovery:
₹{opportunity["expected_recovery"]}

Opportunity score:
{opportunity["opportunity_score"]}

Opportunity priority:
{opportunity["opportunity_priority"]}

Recommended action from the deterministic engine:
{opportunity["recommended_action"]}

Respond using this format:

Decision: <action>

Reason: <short explanation>

Expected Recovery: ₹<amount>

Confidence: <HIGH/MEDIUM/LOW>
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text