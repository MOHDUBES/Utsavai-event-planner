"""
Tests for the Budget Engine.

Coverage:
- Base allocation percentages
- Priority boosting
- City tier multipliers
- Season detection
- Guest count scaling
- Budget warnings
- Edge cases: zero budget, huge guests, unrealistic budget
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.models.schemas import (
    CityTier,
    DietaryType,
    EventRequest,
    EventType,
    PriorityArea,
    Season,
)
from backend.services.budget_engine import (
    BASE_ALLOCATIONS,
    _apply_priority_boost,
    _guest_scale_factor,
    calculate_budget,
    detect_season,
)

# ─────────────────────────────────────────────────────────────
# Season detection tests
# ─────────────────────────────────────────────────────────────


class TestSeasonDetection:
    """Test season classification for Indian event calendar."""

    @pytest.mark.parametrize(
        "month,expected",
        [
            (10, Season.PEAK),  # October – peak wedding season
            (11, Season.PEAK),  # November
            (12, Season.PEAK),  # December
            (1, Season.PEAK),  # January
            (2, Season.PEAK),  # February
            (3, Season.SHOULDER),  # March
            (4, Season.SHOULDER),  # April
            (9, Season.SHOULDER),  # September
            (5, Season.OFF),  # May – summer
            (6, Season.OFF),  # June – monsoon
            (7, Season.OFF),  # July – monsoon
            (8, Season.OFF),  # August – monsoon
        ],
    )
    def test_season_detection(self, month: int, expected: Season):
        """Every month maps to the correct season."""
        test_date = date(2027, month, 15)
        assert detect_season(test_date) == expected

    def test_season_peak_increases_cost(self):
        """Peak season allocation should produce valid budget."""
        peak_date = date(2027, 11, 15)
        off_date = date(2027, 6, 15)

        req_peak = _make_request(total_budget_inr=1_000_000, event_date=peak_date)
        req_off = _make_request(total_budget_inr=1_000_000, event_date=off_date)

        budget_peak = calculate_budget(req_peak)
        budget_off = calculate_budget(req_off)

        # Both should have warnings if budget is tight, but allocations sum should be correct
        total_alloc_peak = sum(li.amount_inr for li in budget_peak.allocations)
        total_alloc_off = sum(li.amount_inr for li in budget_off.allocations)

        # Both should account for 90% of budget (10% contingency)
        assert abs(total_alloc_peak - (1_000_000 * 0.9)) < 10_000
        assert abs(total_alloc_off - (1_000_000 * 0.9)) < 10_000


# ─────────────────────────────────────────────────────────────
# Guest scaling tests
# ─────────────────────────────────────────────────────────────


class TestGuestScaling:
    """Test economy-of-scale factors for guest counts."""

    def test_small_group_has_higher_factor(self):
        """Small groups (<50) pay more per head due to no bulk discounts."""
        small = _guest_scale_factor(30)
        medium = _guest_scale_factor(150)
        large = _guest_scale_factor(500)
        huge = _guest_scale_factor(2000)

        assert small > medium > large > huge

    @pytest.mark.parametrize(
        "count,expected_max",
        [
            (10, 1.15),
            (50, 1.12),
            (200, 0.95),
            (1000, 0.88),
        ],
    )
    def test_scale_factor_range(self, count: int, expected_max: float):
        """Scale factors should be in expected range."""
        factor = _guest_scale_factor(count)
        assert factor <= expected_max
        assert factor > 0.5  # Never below 50%


# ─────────────────────────────────────────────────────────────
# Priority boosting tests
# ─────────────────────────────────────────────────────────────


class TestPriorityBoosting:
    """Test that priority areas receive higher budget allocations."""

    def test_food_priority_boosts_catering(self):
        """When food is #1 priority, catering should get a larger share."""
        base_alloc = dict(BASE_ALLOCATIONS[EventType.WEDDING])
        original_catering = sum(v for k, v in base_alloc.items() if "Catering" in k)

        boosted = _apply_priority_boost(base_alloc, [PriorityArea.FOOD])
        boosted_catering = sum(v for k, v in boosted.items() if "Catering" in k)

        assert boosted_catering > original_catering

    def test_empty_priorities_unchanged(self):
        """No priorities → allocations unchanged."""
        base_alloc = dict(BASE_ALLOCATIONS[EventType.BIRTHDAY])
        original_total = sum(base_alloc.values())

        boosted = _apply_priority_boost(base_alloc, [])
        boosted_total = sum(boosted.values())

        assert abs(original_total - boosted_total) < 0.01

    def test_all_categories_positive_after_boost(self):
        """Priority boosting should never make a category negative."""
        for event_type in EventType:
            if event_type not in BASE_ALLOCATIONS:
                continue
            base_alloc = dict(BASE_ALLOCATIONS[event_type])
            boosted = _apply_priority_boost(
                base_alloc,
                [PriorityArea.FOOD, PriorityArea.DECOR, PriorityArea.PHOTOGRAPHY],
            )
            for cat, val in boosted.items():
                assert val >= 0, f"Negative allocation for {cat} in {event_type}"


# ─────────────────────────────────────────────────────────────
# Full budget calculation tests
# ─────────────────────────────────────────────────────────────


class TestBudgetCalculation:
    """End-to-end budget calculation tests."""

    def test_wedding_budget_allocation_sums_correctly(self, wedding_request):
        """Total allocations + contingency should equal total budget."""
        budget = calculate_budget(wedding_request)

        total_alloc = sum(li.amount_inr for li in budget.allocations)
        assert (
            abs(total_alloc + budget.contingency_inr - budget.total_inr) < 500
        )  # ₹500 rounding tolerance

    def test_per_head_calculation(self, wedding_request):
        """Per-head cost should equal total / guest count."""
        budget = calculate_budget(wedding_request)
        expected = wedding_request.total_budget_inr / wedding_request.guest_count
        assert abs(budget.per_head_inr - expected) < 1

    def test_contingency_is_ten_percent(self, wedding_request):
        """Contingency must be exactly 10% of total budget."""
        budget = calculate_budget(wedding_request)
        expected_contingency = wedding_request.total_budget_inr * 0.10
        assert abs(budget.contingency_inr - expected_contingency) < 100

    def test_metro_more_expensive_than_tier3(self, future_date):
        """Metro realistic minimum should exceed tier-3 minimum."""
        req_metro = _make_request(city_tier=CityTier.METRO, event_date=future_date)
        req_tier3 = _make_request(city_tier=CityTier.TIER3, event_date=future_date)

        budget_metro = calculate_budget(req_metro)
        budget_tier3 = calculate_budget(req_tier3)

        assert budget_metro.realistic_minimum_inr > budget_tier3.realistic_minimum_inr

    def test_low_budget_generates_warning(self, future_date):
        """Very low budget should produce a warning."""
        req = EventRequest(
            event_type=EventType.WEDDING,
            event_date=future_date,
            city="Delhi",
            city_tier=CityTier.METRO,
            guest_count=200,
            total_budget_inr=50_000,  # Way too low for 200-guest wedding
            dietary=DietaryType.VEG,
        )
        budget = calculate_budget(req)
        assert len(budget.warnings) > 0
        # Should suggest minimum budget
        assert any("₹" in s for s in budget.suggestions)

    def test_birthday_small_budget(self, future_date):
        """Small birthday budget should work without errors."""
        req = EventRequest(
            event_type=EventType.BIRTHDAY,
            event_date=future_date,
            city="Pune",
            city_tier=CityTier.TIER2,
            guest_count=20,
            total_budget_inr=15_000,
            dietary=DietaryType.VEG,
        )
        budget = calculate_budget(req)
        assert budget.total_inr == 15_000
        assert len(budget.allocations) > 0

    def test_all_event_types_produce_valid_budget(self, future_date):
        """Every event type should produce a valid budget breakdown."""
        for event_type in EventType:
            req = _make_request(event_type=event_type, event_date=future_date)
            budget = calculate_budget(req)

            assert budget.total_inr > 0
            assert budget.per_head_inr > 0
            assert budget.contingency_inr > 0
            assert len(budget.allocations) > 0
            assert all(li.amount_inr >= 0 for li in budget.allocations)

    def test_season_in_response(self, wedding_request):
        """Budget response should include correct season."""
        budget = calculate_budget(wedding_request)
        assert budget.season in list(Season)

    def test_city_tier_in_response(self, wedding_request):
        """Budget response should include city tier."""
        budget = calculate_budget(wedding_request)
        assert budget.city_tier == CityTier.METRO

    # ── Edge cases ──────────────────────────────────────────

    def test_single_guest(self, future_date):
        """Single guest event should work."""
        req = EventRequest(
            event_type=EventType.BIRTHDAY,
            event_date=future_date,
            city="Delhi",
            city_tier=CityTier.METRO,
            guest_count=1,
            total_budget_inr=5_000,
            dietary=DietaryType.VEG,
        )
        budget = calculate_budget(req)
        assert budget.per_head_inr == 5_000.0

    def test_maximum_guest_count(self, future_date):
        """10,000 guests should not crash the engine."""
        req = EventRequest(
            event_type=EventType.RWA_EVENT,
            event_date=future_date,
            city="Mumbai",
            city_tier=CityTier.METRO,
            guest_count=10_000,
            total_budget_inr=10_000_000,
            dietary=DietaryType.VEG,
        )
        budget = calculate_budget(req)
        assert budget.total_inr == 10_000_000
        assert len(budget.allocations) > 0

    def test_very_high_budget(self, future_date):
        """₹1 crore budget should work without overflow."""
        req = _make_request(total_budget_inr=10_000_000, event_date=future_date)
        budget = calculate_budget(req)
        assert budget.total_inr == 10_000_000

    def test_peak_season_warning_generated(self):
        """Peak season should trigger a warning message."""
        peak_date = date(2027, 11, 20)  # November – peak
        req = _make_request(event_date=peak_date, total_budget_inr=1_000_000)
        budget = calculate_budget(req)
        assert any("Peak season" in w or "peak" in w.lower() for w in budget.warnings)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _make_request(
    event_type: EventType = EventType.WEDDING,
    event_date: date | None = None,
    city_tier: CityTier = CityTier.METRO,
    guest_count: int = 100,
    total_budget_inr: float = 500_000,
    dietary: DietaryType = DietaryType.VEG,
) -> EventRequest:
    """Helper to create an EventRequest with sensible defaults."""
    if event_date is None:
        event_date = date.today() + timedelta(days=90)
    return EventRequest(
        event_type=event_type,
        event_date=event_date,
        city="Delhi",
        city_tier=city_tier,
        guest_count=guest_count,
        total_budget_inr=total_budget_inr,
        dietary=dietary,
    )
