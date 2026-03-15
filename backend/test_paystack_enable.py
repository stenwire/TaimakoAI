import asyncio
from app.services.subscription.paystack import PaystackSubscriptionService

srv = PaystackSubscriptionService()

async def test():
    # It might be hard to test without valid customer and plan codes. Let's see if we can get a failure using mock data.
    try:
        srv.create_subscription("CUS_mock", "PLN_mock", "AUTH_mock", "2024-05-19T00:00:00.000Z")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
