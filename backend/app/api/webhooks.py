import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.payment import Payment
from app.models.recovery_event import RecoveryEvent
from app.services.webhook_service import (
    verify_razorpay_signature,
)


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(
        default=None
    ),
    x_razorpay_event_id: str | None = Header(
        default=None
    ),
):
    # =====================================================
    # 1. Read RAW body
    # =====================================================

    body = await request.body()

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Empty webhook body.",
        )


    # =====================================================
    # 2. Check signature exists
    # =====================================================

    if not x_razorpay_signature:

        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay webhook signature.",
        )


    # =====================================================
    # 3. Verify signature
    # =====================================================

    if not verify_razorpay_signature(
        body=body,
        signature=x_razorpay_signature,
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature.",
        )


    # =====================================================
    # 4. Parse JSON only AFTER verification
    # =====================================================

    try:

        payload = json.loads(
            body.decode("utf-8")
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        )


    # =====================================================
    # 5. Event type
    # =====================================================

    event_name = payload.get("event")


    # =====================================================
    # 6. We only process payment_link.paid
    # =====================================================

    if event_name != "payment_link.paid":

        return {
            "success": True,
            "status": "event_ignored",
            "event": event_name,
        }


    # =====================================================
    # 7. Prevent duplicate event processing
    # =====================================================

    if x_razorpay_event_id:

        existing_event = (
            db.query(RecoveryEvent)
            .filter(
                RecoveryEvent.external_event_id
                == x_razorpay_event_id
            )
            .first()
        )

        if existing_event:

            return {
                "success": True,
                "status": "duplicate_ignored",
                "event_id": x_razorpay_event_id,
            }


    # =====================================================
    # 8. Extract payment link entity
    # =====================================================

    payment_link_entity = (
        payload
        .get("payload", {})
        .get("payment_link", {})
        .get("entity", {})
    )


    reference_id = (
        payment_link_entity.get(
            "reference_id"
        )
    )


    amount_paid = (
        payment_link_entity.get(
            "amount_paid",
            0,
        )
    )


    # =====================================================
    # 9. Validate RecoverAI reference
    # =====================================================

    if not reference_id:

        raise HTTPException(
            status_code=400,
            detail="Missing payment link reference_id.",
        )


    if not reference_id.startswith(
        "RECOVERAI_"
    ):

        return {
            "success": True,
            "status": "reference_ignored",
        }


    # =====================================================
    # 10. Extract RecoverAI payment ID
    # =====================================================

    try:

        payment_id = int(
            reference_id.removeprefix(
                "RECOVERAI_"
            )
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid RecoverAI payment "
                "reference_id."
            ),
        )


    # =====================================================
    # 11. Find payment
    # =====================================================

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )


    if payment is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Payment #{payment_id} "
                "was not found."
            ),
        )


    # =====================================================
    # 12. Idempotent payment recovery check
    # =====================================================

    if payment.recovered == 1:

        return {
            "success": True,
            "status": "already_recovered",
            "payment_id": payment.id,
        }


    # =====================================================
    # 13. Convert amount from paise to INR
    # =====================================================

    recovered_amount = (
        float(amount_paid) / 100
    )


    # =====================================================
    # 14. Mark payment recovered
    # =====================================================

    payment.status = "recovered"
    payment.recovered = 1


    # =====================================================
    # 15. Create RecoveryEvent
    # =====================================================

    recovery_event = RecoveryEvent(
        payment_id=payment.id,
        action="razorpay_payment_link",
        amount=payment.amount,
        status="RECOVERED",
        recovered_amount=recovered_amount,
        external_event_id=(
            x_razorpay_event_id
        ),
    )

    db.add(recovery_event)


    # =====================================================
    # 16. Save
    # =====================================================

    db.commit()


    # =====================================================
    # 17. Response
    # =====================================================

    return {
        "success": True,
        "status": "payment_recovered",
        "payment_id": payment.id,
        "recovered_amount": recovered_amount,
        "event": event_name,
        "event_id": x_razorpay_event_id,
    }