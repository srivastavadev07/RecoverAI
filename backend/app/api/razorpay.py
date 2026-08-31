from fastapi import APIRouter

from app.services.razorpay_service import (
    create_payment_link,
)


router = APIRouter(
    prefix="/razorpay",
    tags=["Razorpay Test Mode"],
)


@router.post("/payment-link")
def create_test_payment_link(
    amount: float,
    customer_id: str,
    payment_id: int,
):
    try:

        payment_link = create_payment_link(
            amount=amount,
            customer_id=customer_id,
            payment_id=payment_id,
        )


        return {
            "success": True,

            "payment_id": payment_id,

            "customer_id": customer_id,

            "amount": amount,

            "razorpay_payment_link_id": (
                payment_link.get("id")
            ),

            "payment_link": (
                payment_link.get(
                    "short_url"
                )
            ),

            "status": (
                payment_link.get(
                    "status"
                )
            ),
        }


    except Exception as exc:

        return {
            "success": False,
            "error": str(exc),
        }