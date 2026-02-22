import hmac
import hashlib
import httpx
from typing import Dict, Any
from app.services.subscription.base import SubscriptionService
from app.core.config import settings

class PaystackSubscriptionService(SubscriptionService):
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        if not self.secret_key:
            print("WARNING: Paystack Secret Key is missing.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_subscription(self, email: str, plan_code: str, callback_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Initialize a transaction with Paystack.
        Note: Paystack init transaction for subscription often just needs 'plan' and 'email'.
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        payload = {
            "email": email,
            "plan": plan_code,
            "callback_url": callback_url,
            "metadata": metadata or {}
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    return data.get("data")
                else:
                    raise Exception(f"Paystack Init Failed: {data.get('message')}")
        except Exception as e:
            print(f"Paystack Init Error: {e}")
            raise e

    def verify_webhook_signature(self, request_headers: Dict[str, str], request_body: bytes) -> bool:
        signature = request_headers.get("x-paystack-signature")
        if not signature:
            return False
        
        calculated_hmac = hmac.new(
            key=self.secret_key.encode('utf-8'),
            msg=request_body,
            digestmod=hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, signature)

    def parse_webhook_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type_raw = payload.get("event")
        data = payload.get("data", {})
        
        standard_event = {
            "event_type": "UNKNOWN",
            "customer_email": data.get("customer", {}).get("email"),
            "customer_code": data.get("customer", {}).get("customer_code"),
            "subscription_code": data.get("subscription_code"), # Might be in data directly or data.subscription?
            "plan_code": data.get("plan", {}).get("plan_code"),
            "amount": data.get("amount"),
            "reference": data.get("reference"),
            "raw_payload": payload
        }

        # Handle variants
        if event_type_raw == "charge.success":
            # Check if it's a subscription renewal/charge
            # "channel": "card" ?
            standard_event["event_type"] = "RENEWAL_SUCCESS"
            # Note: For first payment, it is also charge.success.
            
        elif event_type_raw == "subscription.create":
            standard_event["event_type"] = "SUBSCRIPTION_CREATED"
            standard_event["subscription_code"] = data.get("subscription_code")
            
        elif event_type_raw == "subscription.disable":
            standard_event["event_type"] = "SUBSCRIPTION_CANCELLED"
            
        # Add more mappings as needed
        
        return standard_event
