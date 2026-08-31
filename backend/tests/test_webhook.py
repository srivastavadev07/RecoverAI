import hashlib
import hmac
import json
import os

from dotenv import load_dotenv


load_dotenv()


WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET"
)


if not WEBHOOK_SECRET:
    raise RuntimeError(
        "RAZORPAY_WEBHOOK_SECRET is not configured."
    )


payload = {
    "event": "payment_link.paid",
    "payload": {
        "payment_link": {
            "entity": {
                "reference_id": "RECOVERAI_2052",
                "amount_paid": 1999900,
            }
        }
    }
}


body = json.dumps(
    payload,
    separators=(",", ":"),
).encode()


signature = hmac.new(
    WEBHOOK_SECRET.encode(),
    body,
    hashlib.sha256,
).hexdigest()


print(
    "Generated webhook signature:"
)

print(signature)

print("\nWebhook body:")
print(body.decode())