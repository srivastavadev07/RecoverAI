import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import random
from datetime import datetime, timedelta

from app.database.database import Base, SessionLocal, engine
from app.models.customer import Customer
from app.models.payment import Payment


CUSTOMER_COUNT = 1000
PAYMENTS_PER_CUSTOMER = 3


NAMES = [
    "Aarav Sharma",
    "Vihaan Singh",
    "Aditya Verma",
    "Arjun Gupta",
    "Riya Sharma",
    "Ananya Singh",
    "Karan Mehta",
    "Priya Kapoor",
    "Rahul Mishra",
    "Sneha Patel",
]


PAYMENT_METHODS = [
    "upi",
    "card",
    "netbanking",
    "wallet",
]


FAILURE_REASONS = [
    "insufficient_funds",
    "bank_declined",
    "payment_timeout",
    "technical_error",
    "authentication_failed",
]


def generate_data():

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Generating customers and payments...")

        for i in range(CUSTOMER_COUNT):

            customer_id = f"CUST_{1000 + i}"

            customer = Customer(
                customer_id=customer_id,
                name=random.choice(NAMES),
                email=f"user{i}@example.com",
                total_payments=0,
                successful_payments=0,
                failed_payments=0,
                total_spent=0,
            )

            db.add(customer)

            total_payments = 0
            successful_payments = 0
            failed_payments = 0
            total_spent = 0
            last_payment_at = None

            for _ in range(PAYMENTS_PER_CUSTOMER):

                amount = random.choice([
                    299,
                    499,
                    999,
                    1299,
                    2499,
                    4999,
                    9999,
                    19999,
                ])

                status = random.choices(
                    ["success", "failed"],
                    weights=[75, 25],
                    k=1
                )[0]

                failure_reason = None

                if status == "failed":
                    failure_reason = random.choice(
                        FAILURE_REASONS
                    )
                    failed_payments += 1

                else:
                    successful_payments += 1
                    total_spent += amount

                total_payments += 1

                payment_date = (
                    datetime.utcnow()
                    - timedelta(
                        days=random.randint(0, 90)
                    )
                )

                if (
                    last_payment_at is None
                    or payment_date > last_payment_at
                ):
                    last_payment_at = payment_date

                payment = Payment(
                    customer_id=customer_id,
                    amount=amount,
                    currency="INR",
                    status=status,
                    failure_reason=failure_reason,
                    payment_method=random.choice(
                        PAYMENT_METHODS
                    ),
                    created_at=payment_date,
                    retry_count=random.randint(0, 2),
                    recovered=0,
                )

                db.add(payment)

            customer.total_payments = total_payments
            customer.successful_payments = successful_payments
            customer.failed_payments = failed_payments
            customer.total_spent = total_spent
            customer.last_payment_at = last_payment_at

        db.commit()

        print("✅ Data generated successfully!")
        print(f"Customers created: {CUSTOMER_COUNT}")
        print(
            f"Payments created: "
            f"{CUSTOMER_COUNT * PAYMENTS_PER_CUSTOMER}"
        )

    except Exception as e:
        db.rollback()
        print("❌ Error while generating data:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    generate_data()