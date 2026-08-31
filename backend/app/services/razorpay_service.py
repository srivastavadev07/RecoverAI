import os

import razorpay
from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET"
)


if not RAZORPAY_KEY_ID:
    raise RuntimeError(
        "RAZORPAY_KEY_ID is not configured."
    )


if not RAZORPAY_KEY_SECRET:
    raise RuntimeError(
        "RAZORPAY_KEY_SECRET is not configured."
    )


# =========================================================
# RAZORPAY CLIENT
# =========================================================

client = razorpay.Client(
    auth=(
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET,
    )
)


# =========================================================
# CREATE PAYMENT LINK
# =========================================================

def create_payment_link(
    amount: float,
    customer_id: str,
    payment_id: int,
):
    """
    Create a Razorpay Test Mode Payment Link.

    Amount is converted from INR to paise because
    Razorpay APIs use the smallest currency unit.
    """

    amount_in_paise = int(
        round(amount * 100)
    )


    data = {
        "amount": amount_in_paise,

        "currency": "INR",

        "description": (
            f"RecoverAI recovery for "
            f"payment #{payment_id}"
        ),

        "reference_id": (
            f"RECOVERAI_{payment_id}"
        ),

        "notes": {
            "recoverai_payment_id": str(
                payment_id
            ),

            "customer_id": customer_id,
        },
    }


    payment_link = client.payment_link.create(
        data
    )


    return payment_link