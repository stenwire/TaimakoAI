from app.services.subscription.base import SubscriptionService
from app.services.subscription.paystack import PaystackSubscriptionService

class SubscriptionServiceFactory:
    _services = {
        "paystack": PaystackSubscriptionService
    }

    @classmethod
    def get_service(cls, provider_name: str = "paystack") -> SubscriptionService:
        service_class = cls._services.get(provider_name.lower())
        if not service_class:
            raise ValueError(f"Subscription Service Provider '{provider_name}' not supported.")
        return service_class()
