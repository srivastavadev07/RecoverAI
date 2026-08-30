from app.agents.recovery_agent import execute_tool


def main():

    retry_result = execute_tool(
        "retry_payment",
        {
            "payment_id": 123,
        },
    )

    print("\nRETRY PAYMENT")
    print(retry_result)

    link_result = execute_tool(
        "create_payment_link",
        {
            "payment_id": 123,
            "amount": 4999,
        },
    )

    print("\nPAYMENT LINK")
    print(link_result)

    notification_result = execute_tool(
        "send_notification",
        {
            "customer_id": "CUST_1001",
            "message": (
                "Your payment needs attention."
            ),
        },
    )

    print("\nNOTIFICATION")
    print(notification_result)


if __name__ == "__main__":
    main()