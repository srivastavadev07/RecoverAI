from datetime import datetime
from uuid import uuid4


def retry_payment(
    payment_id: int,
) -> dict:
    """
    Simulate a payment retry.

    This is intentionally a simulation.
    No real payment is processed.
    """

    attempt_id = f"RETRY_{uuid4().hex[:8]}"

    return {
        "success": True,
        "tool": "retry_payment",
        "payment_id": payment_id,
        "attempt_id": attempt_id,
        "status": "retry_scheduled",
        "message": "Payment retry simulated successfully.",
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_payment_link(
    payment_id: int,
    amount: float,
) -> dict:
    """
    Simulate creation of a payment link.

    This does NOT call Razorpay yet.
    """

    link_id = f"plink_{uuid4().hex[:10]}"

    return {
        "success": True,
        "tool": "create_payment_link",
        "payment_id": payment_id,
        "amount": amount,
        "currency": "INR",
        "link_id": link_id,
        "payment_link": (
            f"https://recoverai.demo/pay/{link_id}"
        ),
        "status": "created",
        "timestamp": datetime.utcnow().isoformat(),
    }


def send_notification(
    customer_id: str,
    message: str,
) -> dict:
    """
    Simulate customer notification.
    """

    notification_id = (
        f"NOTIFY_{uuid4().hex[:8]}"
    )

    return {
        "success": True,
        "tool": "send_notification",
        "customer_id": customer_id,
        "notification_id": notification_id,
        "message": message,
        "status": "queued",
        "timestamp": datetime.utcnow().isoformat(),
    }