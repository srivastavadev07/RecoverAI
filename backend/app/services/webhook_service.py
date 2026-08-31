import hashlib
import hmac
import os

from dotenv import load_dotenv


load_dotenv()


RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET"
)


def verify_razorpay_signature(
    body: bytes,
    signature: str,
) -> bool:
    """
    Verify the Razorpay webhook signature.

    Razorpay signs the raw webhook request body using
    HMAC-SHA256.
    """

    if not RAZORPAY_WEBHOOK_SECRET:
        raise RuntimeError(
            "RAZORPAY_WEBHOOK_SECRET is not configured."
        )

    expected_signature = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )