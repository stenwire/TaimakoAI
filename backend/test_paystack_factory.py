from app.services.subscription.factory import SubscriptionServiceFactory
from app.services.subscription.paystack import PaystackSubscriptionService
import hmac
import hashlib
import json

def test_factory():
    print("Testing Factory...")
    service = SubscriptionServiceFactory.get_service("paystack")
    assert isinstance(service, PaystackSubscriptionService)
    print("✅ Factory returned PaystackService")

def test_webhook_parsing():
    print("Testing Webhook Parsing...")
    service = SubscriptionServiceFactory.get_service("paystack")
    
    # Mock Payload
    payload = {
        "event": "charge.success",
        "data": {
            "amount": 50000,
            "reference": "ref_123",
            "customer": {
                "email": "test@example.com",
                "customer_code": "CUS_123"
            }
        }
    }
    
    event = service.parse_webhook_event(payload)
    assert event["event_type"] == "RENEWAL_SUCCESS"
    assert event["customer_email"] == "test@example.com"
    print("✅ Webhook Parsed Successfully")

def test_signature():
    print("Testing Signature Verification...")
    # Mock Service with known key
    service = PaystackSubscriptionService()
    service.secret_key = "secret"
    
    payload = b'{"test":"data"}'
    signature = hmac.new(b"secret", payload, hashlib.sha512).hexdigest()
    
    headers = {"x-paystack-signature": signature}
    assert service.verify_webhook_signature(headers, payload) is True
    print("✅ Signature Verified")

if __name__ == "__main__":
    try:
        test_factory()
        test_webhook_parsing()
        test_signature()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
