"""Unit tests for app.core.subscription module.

Tests the SubscriptionTier enum, TIER_LIMITS configuration, and TIER_HIERARCHY ordering.
"""

import pytest

from app.core.subscription import SubscriptionTier, TIER_LIMITS, TIER_HIERARCHY


@pytest.mark.unit
class TestSubscriptionTier:
    """Tests for the SubscriptionTier enum."""

    def test_tier_spark_value(self):
        """SPARK tier should have value 'spark'."""
        assert SubscriptionTier.SPARK.value == "spark"

    def test_tier_flux_value(self):
        """FLUX tier should have value 'flux'."""
        assert SubscriptionTier.FLUX.value == "flux"

    def test_tier_nexus_value(self):
        """NEXUS tier should have value 'nexus'."""
        assert SubscriptionTier.NEXUS.value == "nexus"

    def test_all_tiers_are_strings(self):
        """All tier values should be strings (SubscriptionTier inherits str)."""
        for tier in SubscriptionTier:
            assert isinstance(tier.value, str)

    def test_tier_count(self):
        """There should be exactly 3 subscription tiers."""
        assert len(SubscriptionTier) == 3


@pytest.mark.unit
class TestTierLimits:
    """Tests for the TIER_LIMITS configuration dict."""

    def test_all_tiers_present_in_limits(self):
        """Every SubscriptionTier should have an entry in TIER_LIMITS."""
        for tier in SubscriptionTier:
            assert tier.value in TIER_LIMITS, f"Missing TIER_LIMITS entry for {tier.value}"

    def test_no_extra_tiers_in_limits(self):
        """TIER_LIMITS should not contain keys outside of SubscriptionTier values."""
        tier_values = {t.value for t in SubscriptionTier}
        for key in TIER_LIMITS:
            assert key in tier_values, f"Unexpected tier '{key}' in TIER_LIMITS"

    @pytest.mark.parametrize("required_key", [
        "monthly_credits",
        "max_daily_sessions",
        "max_messages_per_session",
        "max_whitelisted_domains",
        "max_monthly_escalations",
        "description",
    ])
    def test_tier_limits_contains_required_keys(self, required_key):
        """Each tier config must contain all required limit keys."""
        for tier in SubscriptionTier:
            assert required_key in TIER_LIMITS[tier.value], (
                f"Tier '{tier.value}' missing key '{required_key}'"
            )

    def test_spark_monthly_credits(self):
        """Spark tier should have 100 monthly credits."""
        assert TIER_LIMITS["spark"]["monthly_credits"] == 100

    def test_nexus_monthly_credits(self):
        """Nexus tier should have 1000 monthly credits."""
        assert TIER_LIMITS["nexus"]["monthly_credits"] == 1000

    def test_flux_monthly_credits(self):
        """Flux tier should have 10000 monthly credits."""
        assert TIER_LIMITS["flux"]["monthly_credits"] == 10000

    def test_limits_increase_with_tier(self):
        """Higher tiers should have higher monthly_credits than lower tiers."""
        spark = TIER_LIMITS["spark"]["monthly_credits"]
        nexus = TIER_LIMITS["nexus"]["monthly_credits"]
        flux = TIER_LIMITS["flux"]["monthly_credits"]
        assert spark < nexus < flux

    def test_numeric_limits_are_positive_integers(self):
        """All numeric limits should be positive integers."""
        numeric_keys = [
            "monthly_credits",
            "max_daily_sessions",
            "max_messages_per_session",
            "max_whitelisted_domains",
            "max_monthly_escalations",
        ]
        for tier in SubscriptionTier:
            for key in numeric_keys:
                value = TIER_LIMITS[tier.value][key]
                assert isinstance(value, int), f"{tier.value}.{key} is not int"
                assert value > 0, f"{tier.value}.{key} is not positive"

    def test_description_is_nonempty_string(self):
        """Each tier should have a non-empty description string."""
        for tier in SubscriptionTier:
            desc = TIER_LIMITS[tier.value]["description"]
            assert isinstance(desc, str)
            assert len(desc) > 0


@pytest.mark.unit
class TestTierHierarchy:
    """Tests for the TIER_HIERARCHY ordering dict."""

    def test_all_tiers_present_in_hierarchy(self):
        """Every SubscriptionTier should appear in TIER_HIERARCHY."""
        for tier in SubscriptionTier:
            assert tier.value in TIER_HIERARCHY

    def test_hierarchy_values_are_integers(self):
        """Hierarchy values should be integers."""
        for tier, rank in TIER_HIERARCHY.items():
            assert isinstance(rank, int), f"Hierarchy rank for '{tier}' is not int"

    def test_hierarchy_values_are_unique(self):
        """Each tier should have a unique rank."""
        ranks = list(TIER_HIERARCHY.values())
        assert len(ranks) == len(set(ranks))

    def test_spark_is_lowest_tier(self):
        """Spark should have the lowest hierarchy value."""
        assert TIER_HIERARCHY["spark"] == min(TIER_HIERARCHY.values())

    def test_flux_is_highest_tier(self):
        """Flux should have the highest hierarchy value."""
        assert TIER_HIERARCHY["flux"] == max(TIER_HIERARCHY.values())
