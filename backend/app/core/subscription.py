from enum import Enum
from typing import Dict, Any

class SubscriptionTier(str, Enum):
    SPARK = "spark"
    FLUX = "flux"
    NEXUS = "nexus"

TIER_HIERARCHY = {
    SubscriptionTier.SPARK.value: 1,
    SubscriptionTier.NEXUS.value: 2,
    SubscriptionTier.FLUX.value: 3,
}

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    SubscriptionTier.SPARK.value: {
        "monthly_credits": 100,
        "max_daily_sessions": 50,
        "max_messages_per_session": 20,
        "max_whitelisted_domains": 1,
        "max_monthly_escalations": 5,
        "description": "Essential features for small businesses."
    },
    SubscriptionTier.NEXUS.value: {
        "monthly_credits": 1000,
        "max_daily_sessions": 500,
        "max_messages_per_session": 50,
        "max_whitelisted_domains": 5,
        "max_monthly_escalations": 100,
        "description": "Advanced power for growing teams."
    },
    SubscriptionTier.FLUX.value: {
        "monthly_credits": 10000,
        "max_daily_sessions": 5000,
        "max_messages_per_session": 100,
        "max_whitelisted_domains": 10,
        "max_monthly_escalations": 500,
        "description": "Unlimited potential for enterprise scale."
    }
}
