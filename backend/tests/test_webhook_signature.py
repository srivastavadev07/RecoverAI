import hashlib
import hmac
import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET"
)

if not WEBHOOK_SECRET:
    raise RuntimeError(
        "RAZORPAY_WEBHOOK_SECRET is not configured."
    )


# Replace these with a REAL failed payment
# from /recovery/opportunities
PAYMENT_ID = 1155
AMOUNT = 19999


payload = {
    "event": "payment_link.paid",
    "payload": {
        "payment_link": {
            "entity": {
                "reference_id": (
                    f"RECOVERAI_{PAYMENT_ID}"
                ),
                "amount_paid": int(
                    AMOUNT * 100
                ),
            }
        }
    }
}


body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")


signature = hmac.new(
    WEBHOOK_SECRET.encode("utf-8"),
    body,
    hashlib.sha256,
).hexdigest()


response = requests.post(
    "http://127.0.0.1:8000/webhooks/razorpay",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
        "X-Razorpay-Event-Id": (
            "recoverai_test_event_001"
        ),
    },
)


print("STATUS CODE:")
print(response.status_code)

print("\nRESPONSE:")
print(response.text)