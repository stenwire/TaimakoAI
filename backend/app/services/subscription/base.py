from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

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
            - event_type: "RENEWAL_SUCCESS", "PLAN_CHANGED", "SUBSCRIPTION_CREATED", "SUBSCRIPTION_CANCELLED", "UNKNOWN"
            - customer_email: str
            - customer_code: str (Provider's ID for user)
            - subscription_code: str (Provider's ID for sub)
            - plan_code: str
            - amount: int
            - reference: str
        """
        pass
