import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.agents.guardrails import validate_recovery_action
from app.agents.tools.payment_tools import (
    retry_payment,
    create_payment_link,
    send_notification,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)

MODEL_NAME = "gemini-2.5-flash"


# =========================================================
# FUNCTION DECLARATIONS
# =========================================================

retry_payment_tool = types.FunctionDeclaration(
    name="retry_payment",
    description=(
        "Schedule exactly one retry attempt for a failed payment."
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
        "Create a payment link for a failed payment "
        "so the customer can complete the payment manually."
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
        "Send a recovery notification to the customer "
        "about the failed payment."
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
                description="Message to send to the customer."
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


# =========================================================
# TOOL EXECUTION
# =========================================================

def execute_selected_tool(
    tool_name: str,
    arguments: dict,
    opportunity: dict,
) -> dict:
    """
    Execute a recovery tool only after passing
    deterministic RecoverAI guardrails.

    IMPORTANT:
    This function is called by our backend, not by Gemini.
    """

    payment_id = opportunity["payment_id"]
    amount = opportunity["amount"]
    retry_count = opportunity["retry_count"]
    priority = opportunity["opportunity_priority"]

    # -----------------------------------------------------
    # Map Gemini tool name -> internal action
    # -----------------------------------------------------

    action_map = {
        "retry_payment": "RETRY_PAYMENT",
        "create_payment_link": "SEND_PAYMENT_LINK",
        "send_notification": "SEND_NOTIFICATION",
    }

    action = action_map.get(tool_name)

    if action is None:
        return {
            "success": False,
            "blocked": True,
            "error": f"Unknown recovery tool: {tool_name}",
        }

    # -----------------------------------------------------
    # SAFETY / GUARDRAIL CHECK
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
    # EXECUTE THE APPROVED TOOL
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

            message = arguments.get(
                "message",
                (
                    "Your payment requires attention. "
                    "Please complete your payment."
                ),
            )

            return send_notification(
                customer_id=opportunity["customer_id"],
                message=message,
            )

        return {
            "success": False,
            "error": "Unsupported recovery tool.",
        }

    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
        }


# =========================================================
# AI ANALYSIS ONLY
# =========================================================

def analyze_opportunity(
    opportunity: dict,
) -> dict:
    """
    Ask Gemini to select ONE recovery action.

    IMPORTANT:
    This function ONLY asks Gemini for a decision.
    It does NOT execute the recovery tool.
    """

    prompt = f"""
You are RecoverAI, an AI revenue recovery decision engine.

Your task is to select exactly ONE recovery function
from the available functions.

YOU MUST RETURN A FUNCTION CALL.

Do NOT return normal text.
Do NOT write:
"Recovery Action: retry_payment"
Do NOT explain the answer in plain text.

Use exactly ONE of these functions:

- retry_payment
- create_payment_link
- send_notification

Decision rules:

1. Use retry_payment when the payment appears
   recoverable and retry_count is below 2.

2. Use create_payment_link when repeated retry attempts
   are no longer appropriate.

3. Use send_notification when customer communication
   should happen before another recovery action.

4. Use only the supplied payment information.

5. Do not claim that money has been recovered.

PAYMENT INFORMATION
-------------------

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

    # -----------------------------------------------------
    # Force Gemini to return a function call
    # -----------------------------------------------------

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[TOOLS],

            tool_config=types.ToolConfig(
                function_calling_config=(
                    types.FunctionCallingConfig(
                        mode="ANY",
                        allowed_function_names=[
                            "retry_payment",
                            "create_payment_link",
                            "send_notification",
                        ],
                    )
                )
            ),

            # IMPORTANT:
            # Our application executes the function.
            # The SDK must NOT execute it automatically.
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        ),
    )

    # -----------------------------------------------------
    # Safely inspect the function calls
    # -----------------------------------------------------

    function_calls = response.function_calls

    if not function_calls:

        return {
            "payment_id": opportunity["payment_id"],
            "customer_id": opportunity["customer_id"],
            "decision": "NO_TOOL_SELECTED",
            "ai_response": response.text,
            "status": "FAILED_TO_SELECT_TOOL",
        }

    # We asked for exactly one function.
    tool_call = function_calls[0]

    return {
        "payment_id": opportunity["payment_id"],
        "customer_id": opportunity["customer_id"],
        "decision": tool_call.name,
        "arguments": dict(tool_call.args),
        "status": "AWAITING_APPROVAL",
    }