import json

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

from app.agents.guardrails import validate_recovery_action
from app.services.audit_service import record_action
from app.agents.tools.payment_tools import (
    retry_payment,
    create_payment_link,
    send_notification,
)


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


# ---------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------

retry_payment_tool = types.FunctionDeclaration(
    name="retry_payment",
    description=(
        "Schedule a retry attempt for a failed payment."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "payment_id": types.Schema(
                type="INTEGER",
                description="ID of the failed payment."
            )
        },
        required=["payment_id"],
    ),
)


create_payment_link_tool = types.FunctionDeclaration(
    name="create_payment_link",
    description=(
        "Create a payment link for a failed payment."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "payment_id": types.Schema(
                type="INTEGER",
                description="ID of the failed payment."
            ),
            "amount": types.Schema(
                type="NUMBER",
                description="Amount that needs to be recovered."
            ),
        },
        required=[
            "payment_id",
            "amount",
        ],
    ),
)


send_notification_tool = types.FunctionDeclaration(
    name="send_notification",
    description=(
        "Send a recovery notification to a customer."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "customer_id": types.Schema(
                type="STRING",
                description="Customer ID."
            ),
            "message": types.Schema(
                type="STRING",
                description="Notification message."
            ),
        },
        required=[
            "customer_id",
            "message",
        ],
    ),
)


TOOLS = types.Tool(
    function_declarations=[
        retry_payment_tool,
        create_payment_link_tool,
        send_notification_tool,
    ]
)


# ---------------------------------------------------------
# TOOL EXECUTION
# ---------------------------------------------------------

def execute_selected_tool(
    tool_name: str,
    arguments: dict,
    opportunity: dict,
):
    """
    Execute a Gemini-selected tool only after
    deterministic safety validation.
    """

    payment_id = opportunity["payment_id"]
    amount = opportunity["amount"]
    retry_count = opportunity["retry_count"]
    priority = opportunity["opportunity_priority"]

    # Map Gemini's action to our internal action names
    action_map = {
        "retry_payment": "RETRY_PAYMENT",
        "create_payment_link": "SEND_PAYMENT_LINK",
        "send_notification": "SEND_NOTIFICATION",
    }

    action = action_map.get(tool_name)

    if action is None:
        return {
            "success": False,
            "error": "Unknown tool requested.",
        }

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    allowed, reason = validate_recovery_action(
        action=action,
        amount=amount,
        retry_count=retry_count,
        opportunity_priority=priority,
    )

    if not allowed:
        return {
            "success": False,
            "blocked": True,
            "tool": tool_name,
            "reason": reason,
        }

    # -----------------------------------------------------
    # EXECUTE TOOL
    # -----------------------------------------------------

    try:

        if tool_name == "retry_payment":
            return retry_payment(
                payment_id=payment_id
            )

        if tool_name == "create_payment_link":
            return create_payment_link(
                payment_id=payment_id,
                amount=amount,
            )

        if tool_name == "send_notification":
            return send_notification(
                customer_id=opportunity["customer_id"],
                message=arguments["message"],
            )

        return {
            "success": False,
            "error": "Unsupported tool.",
        }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
        }


# ---------------------------------------------------------
# AI DECISION
# ---------------------------------------------------------

def analyze_opportunity(
    opportunity: dict,
    db,
) -> dict:

    prompt = f"""
You are RecoverAI, an AI revenue recovery agent.

Analyze the failed payment below and choose the SINGLE
most appropriate recovery tool.

IMPORTANT RULES:
1. Use only the supplied information.
2. Never claim that money has already been recovered.
3. Prefer retry_payment for an initial recoverable failure.
4. Prefer create_payment_link when retries are exhausted
   or a direct payment request is more appropriate.
5. Use send_notification when communicating with the customer
   is the best first step.
6. Do not attempt multiple tools.
7. Your job is to make ONE action decision.

PAYMENT DATA

Payment ID:
{opportunity["payment_id"]}

Customer ID:
{opportunity["customer_id"]}

Amount:
₹{opportunity["amount"]}

Failure Reason:
{opportunity["failure_reason"]}

Payment Method:
{opportunity["payment_method"]}

Retry Count:
{opportunity["retry_count"]}

Risk Score:
{opportunity["risk_score"]}

Recovery Probability:
{opportunity["recovery_probability"]}

Revenue at Risk:
₹{opportunity["revenue_at_risk"]}

Expected Recovery:
₹{opportunity["expected_recovery"]}

Opportunity Score:
{opportunity["opportunity_score"]}

Opportunity Priority:
{opportunity["opportunity_priority"]}

Deterministic Recommended Action:
{opportunity["recommended_action"]}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[TOOLS],
        ),
    )

    candidate = response.candidates[0]

    tool_call = None

    for part in candidate.content.parts:
        if part.function_call:
            tool_call = part.function_call
            break

    # -----------------------------------------------------
    # Gemini returned a normal text response instead of tool
    # -----------------------------------------------------

    if tool_call is None:
        return {
            "payment_id": opportunity["payment_id"],
            "customer_id": opportunity["customer_id"],
            "decision": "NO_TOOL_SELECTED",
            "ai_response": response.text,
        }

    tool_name = tool_call.name

    arguments = dict(tool_call.args)

    # -----------------------------------------------------
    # Safety validation + execution
    # -----------------------------------------------------

    tool_result = execute_selected_tool(
        tool_name=tool_name,
        arguments=arguments,
        opportunity=opportunity,
    )

    record_action(
    db=db,
    payment_id=opportunity["payment_id"],
    action=tool_name,
    status=(
        "BLOCKED"
        if tool_result.get("blocked")
        else (
            "SUCCESS"
            if tool_result.get("success")
            else "FAILED"
        )
    ),
    reason=tool_result.get(
        "reason",
        "Recovery tool executed."
    ),
    details=tool_result,
)

    return {
    "payment_id": opportunity["payment_id"],
    "customer_id": opportunity["customer_id"],
    "decision": tool_name,
    "arguments": arguments,
    "tool_result": tool_result,
}