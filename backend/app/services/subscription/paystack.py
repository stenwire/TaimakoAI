import hmac
import hashlib
import httpx
import logging
from typing import Dict, Any, List
from app.services.subscription.base import SubscriptionService
from app.core.config import settings

logger = logging.getLogger(__name__)


class PaystackSubscriptionService(SubscriptionService):
    BASE_URL = "https://api.paystack.co"

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        if not self.secret_key:
            logger.warning("Paystack Secret Key is missing.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def initialize_subscription(self, amount: int, email: str, plan_code: str, callback_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Initialize a transaction with Paystack for subscription creation.
        Paystack auto-creates the subscription on successful payment.
        """
        url = f"{self.BASE_URL}/transaction/initialize"
        payload = {
            "email": email,
            "plan": plan_code,
            "callback_url": callback_url,
            "metadata": metadata or {},
            "amount": amount
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
            logger.error(f"Paystack Init Error: {e}")
            raise e

    def cancel_subscription(self, subscription_code: str, email_token: str) -> bool:
        """
        Disable/cancel a subscription on Paystack.
        Requires the subscription_code and email_token from subscription.create event.
        """
        url = f"{self.BASE_URL}/subscription/disable"
        payload = {
            "code": subscription_code,
            "token": email_token
        }

        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    logger.info(f"Subscription {subscription_code} cancelled successfully")
                    return True
                else:
                    logger.error(f"Paystack cancel failed: {data.get('message')}")
                    return False
        except Exception as e:
            logger.error(f"Paystack Cancel Error: {e}")
            return False

    def fetch_subscription(self, subscription_code: str) -> Dict[str, Any]:
        """
        Fetch details of a subscription, useful for extracting next_payment_date.
        """
        url = f"{self.BASE_URL}/subscription/{subscription_code}"
        
        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    return data.get("data")
        except Exception as e:
            logger.error(f"Paystack Fetch Error: {e}")
            raise e

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """
        Verify a transaction on Paystack by its reference.
        Extracts metadata and standardizes the response similarly to webhooks.
        """
        url = f"{self.BASE_URL}/transaction/verify/{reference}"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    tx_data = data.get("data", {})
                    # Standardize the event structure similar to parse_webhook_event
                    # Wrap tx_data in the same envelope structure as webhook payloads
                    # so _process_renewal_success can extract metadata consistently
                    # via raw_payload["data"]["metadata"]
                    standard_event = {
                        "event_type": "RENEWAL_SUCCESS" if tx_data.get("status") == "success" else "PAYMENT_FAILED",
                        "customer_email": tx_data.get("customer", {}).get("email"),
                        "customer_code": tx_data.get("customer", {}).get("customer_code"),
                        "subscription_code": tx_data.get("metadata", {}).get("subscription_code"),
                        "plan_code": tx_data.get("plan_object", {}).get("plan_code"),
                        "amount": tx_data.get("amount"),
                        "reference": tx_data.get("reference"),
                        "authorization_code": tx_data.get("authorization", {}).get("authorization_code"),
                        "email_token": None,
                        "raw_payload": {"data": tx_data}
                    }
                    print(f"\n\n Result from verifying transaction: {standard_event}\n\n")
                    return standard_event
                else:
                    raise Exception(f"Paystack Verify Failed: {data.get('message')}")
        except Exception as e:
            logger.error(f"Paystack Verify Error: {e}")
            raise e

    def create_subscription(self, customer_code: str, plan_code: str, authorization_code: str, start_date: str = None) -> Dict[str, Any]:
        """
        Create a new subscription using a saved card (authorization).
        Used for plan upgrades without requiring the user to re-enter card details.
        """
        url = f"{self.BASE_URL}/subscription"
        payload = {
            "customer": customer_code,
            "plan": plan_code,
            "authorization": authorization_code
        }
        if start_date:
            payload["start_date"] = start_date

        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    result = data.get("data", {})
                    return {
                        "subscription_code": result.get("subscription_code"),
                        "email_token": result.get("email_token"),
                    }
                else:
                    raise Exception(f"Paystack Create Subscription Failed: {data.get('message')}")
        except Exception as e:
            logger.error(f"Paystack Create Subscription Error: {e}")
            raise e

    def sync_plans(self) -> List[Dict[str, Any]]:
        """
        Fetch all plans from Paystack.
        """
        url = f"{self.BASE_URL}/plan"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                if data.get("status"):
                    plans = []
                    for p in data.get("data", []):
                        plans.append({
                            "plan_code": p.get("plan_code"),
                            "name": p.get("name"),
                            "amount": p.get("amount"),
                            "interval": p.get("interval"),
                            "currency": p.get("currency"),
                        })
                    return plans
                else:
                    raise Exception(f"Paystack Sync Plans Failed: {data.get('message')}")
        except Exception as e:
            logger.error(f"Paystack Sync Plans Error: {e}")
            raise e

    def verify_webhook_signature(self, request_headers: Dict[str, str], request_body: bytes) -> bool:
        signature = request_headers.get("x-paystack-signature")
        logger.info("[PAYSTACK] Verifying webhook signature...")
        logger.info(f"[PAYSTACK] Received signature: {signature[:20] if signature else 'NONE'}...")
        logger.info(f"[PAYSTACK] Secret key present: {bool(self.secret_key)}, length: {len(self.secret_key) if self.secret_key else 0}")

        if not signature:
            logger.warning("[PAYSTACK] ❌ No x-paystack-signature header found")
            return False

        calculated_hmac = hmac.new(
            key=self.secret_key.encode('utf-8'),
            msg=request_body,
            digestmod=hashlib.sha512
        ).hexdigest()

        logger.info(f"[PAYSTACK] Calculated HMAC: {calculated_hmac[:20]}...")
        match = hmac.compare_digest(calculated_hmac, signature)
        logger.info(f"[PAYSTACK] Signature match: {match}")
        return match

    def parse_webhook_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Paystack webhook payload into a standardized event structure.
        Handles: charge.success, subscription.create, subscription.disable,
                invoice.payment_failed, subscription.not_renew.
        """
        event_type_raw = payload.get("event")
        data = payload.get("data", {})
        logger.info(f"[PAYSTACK] Parsing event: {event_type_raw}")
        logger.info(f"[PAYSTACK] Data keys: {list(data.keys())}")

        standard_event = {
            "event_type": "UNKNOWN",
            "customer_email": data.get("customer", {}).get("email"),
            "customer_code": data.get("customer", {}).get("customer_code"),
            "subscription_code": data.get("subscription_code"),
            "plan_code": data.get("plan", {}).get("plan_code"),
            "amount": data.get("amount"),
            "reference": data.get("reference"),
            "authorization_code": None,
            "email_token": None,
            "raw_payload": payload
        }

        if event_type_raw == "charge.success":
            standard_event["event_type"] = "RENEWAL_SUCCESS"
            # Extract authorization_code from the authorization object
            authorization = data.get("authorization", {})
            if authorization:
                standard_event["authorization_code"] = authorization.get("authorization_code")

        elif event_type_raw == "subscription.create":
            standard_event["event_type"] = "SUBSCRIPTION_CREATED"
            standard_event["subscription_code"] = data.get("subscription_code")
            standard_event["email_token"] = data.get("email_token")

        elif event_type_raw == "subscription.disable":
            standard_event["event_type"] = "SUBSCRIPTION_CANCELLED"

        elif event_type_raw == "invoice.payment_failed":
            standard_event["event_type"] = "PAYMENT_FAILED"
            # subscription info may be nested under data.subscription
            sub_data = data.get("subscription", {})
            if sub_data:
                standard_event["subscription_code"] = sub_data.get("subscription_code")

        elif event_type_raw == "subscription.not_renew":
            standard_event["event_type"] = "SUBSCRIPTION_NON_RENEWING"

        return standard_event
