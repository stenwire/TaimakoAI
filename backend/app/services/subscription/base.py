from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class SubscriptionService(ABC):
    """
    Abstract Base Class for Subscription Services (e.g., Paystack, Stripe).
    """

    @abstractmethod
    def initialize_subscription(self, email: str, plan_code: str, callback_url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Initialize a subscription transaction.
        Returns:
            Dict containing 'authorization_url', 'reference', etc.
        """
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_code: str, email_token: str) -> bool:
        """
        Cancel/disable an active subscription.
        Returns:
            True if successfully cancelled, False otherwise.
        """
        pass

    @abstractmethod
    def create_subscription(self, customer_code: str, plan_code: str, authorization_code: str) -> Dict[str, Any]:
        """
        Create a new subscription on an existing customer's saved card.
        Used for plan upgrades with card-on-file.
        Returns:
            Dict containing 'subscription_code', 'email_token', etc.
        """
        pass

    @abstractmethod
    def sync_plans(self) -> List[Dict[str, Any]]:
        """
        Fetch all plans from the payment provider.
        Returns:
            List of plan dicts with keys: plan_code, name, amount, interval, currency.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(self, request_headers: Dict[str, str], request_body: bytes) -> bool:
        """
        Verify that the webhook request is genuinely from the provider.
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the webhook payload into a standardized event structure.
        Expected Standard Keys:
            - event_type: "RENEWAL_SUCCESS", "SUBSCRIPTION_CREATED", "SUBSCRIPTION_CANCELLED",
                        "PAYMENT_FAILED", "SUBSCRIPTION_NON_RENEWING", "UNKNOWN"
            - customer_email: str
            - customer_code: str (Provider's ID for user)
            - subscription_code: str (Provider's ID for sub)
            - plan_code: str
            - amount: int
            - reference: str
            - authorization_code: str (card token, from charge.success)
            - email_token: str (subscription token, from subscription.create)
        """
        pass
