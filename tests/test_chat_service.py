"""
Unit tests for backend.services.chat_service pure helper functions and intent parsers.
"""

from __future__ import annotations

from datetime import date

from backend.constants import (
    BASE_ALLOCATIONS,
    CITY_MULTIPLIERS,
    FESTIVAL_CLUSTERS,
    MIN_PER_HEAD_INR,
    SEASON_MULTIPLIERS,
)
from backend.exceptions import (
    AIProviderError,
    ChatServiceError,
    PlanningEngineException,
    UtsavAIException,
)
from backend.models.schemas import BudgetLineItem, CityTier, EventType, Season
from backend.services.chat_service import (
    build_cost_cut_tips,
    calculate_area_cut,
    parse_cost_reduction_params,
    parse_reschedule_delta,
)


class TestChatServicePureHelpers:
    """Test pure functions extracted for chat intent parsing."""

    def test_parse_cost_reduction_decor_percentage(self):
        res = parse_cost_reduction_params("Can you cut decor cost by 20%?")
        assert res is not None
        area, pct = res
        assert area == "decor"
        assert pct == 20

    def test_parse_cost_reduction_catering_custom_pct(self):
        res = parse_cost_reduction_params("Reduce catering budget by 35% please")
        assert res is not None
        area, pct = res
        assert area == "catering"
        assert pct == 35

    def test_parse_cost_reduction_photography_default_pct(self):
        res = parse_cost_reduction_params("Can we reduce photography costs?")
        assert res is not None
        area, pct = res
        assert area == "photography"
        assert pct == 20

    def test_parse_cost_reduction_unrelated_message(self):
        res = parse_cost_reduction_params("What is the weather like tomorrow?")
        assert res is None

    def test_calculate_area_cut(self):
        allocations = [
            BudgetLineItem(
                category="Decor & Florals",
                amount_inr=100_000.0,
                percentage=10.0,
                min_amount_inr=50_000.0,
            ),
            BudgetLineItem(
                category="Venue",
                amount_inr=200_000.0,
                percentage=20.0,
                min_amount_inr=100_000.0,
            ),
        ]
        updated, savings, old_tot, new_tot = calculate_area_cut(
            allocations=allocations,
            category_kw="decor",
            reduction_pct=20,
            total_budget=1_000_000.0,
        )
        assert savings == 20_000.0
        assert old_tot == 100_000.0
        assert new_tot == 80_000.0
        assert len(updated) == 2
        decor_item = next(i for i in updated if "decor" in i.category.lower())
        assert decor_item.amount_inr == 80_000.0

    def test_build_cost_cut_tips_decor(self):
        tips = build_cost_cut_tips("decor")
        assert len(tips) > 0
        joined = " ".join(tips).lower()
        assert "flowers" in joined or "lights" in joined or "props" in joined

    def test_build_cost_cut_tips_catering(self):
        tips = build_cost_cut_tips("catering")
        assert len(tips) > 0
        joined = " ".join(tips).lower()
        assert "buffet" in joined or "stations" in joined or "ingredients" in joined

    def test_build_cost_cut_tips_unmatched(self):
        tips = build_cost_cut_tips("unknown_area")
        assert tips == []

    def test_parse_reschedule_delta_weeks(self):
        today = date(2027, 2, 14)
        delta_2_weeks = parse_reschedule_delta(today, "Please reschedule 2 weeks later")
        assert delta_2_weeks == 14

    def test_parse_reschedule_delta_single_week(self):
        today = date(2027, 2, 14)
        delta_1_week = parse_reschedule_delta(today, "Postpone by 1 week")
        assert delta_1_week == 7

    def test_parse_reschedule_delta_months(self):
        today = date(2027, 2, 14)
        delta_1_month = parse_reschedule_delta(today, "Push the wedding by 1 month")
        assert delta_1_month == 30

        delta_2_months = parse_reschedule_delta(today, "Delay event by 2 months")
        assert delta_2_months == 60

    def test_parse_reschedule_delta_days(self):
        today = date(2027, 2, 14)
        delta_10_days = parse_reschedule_delta(today, "Move event 10 days later")
        assert delta_10_days == 10

    def test_parse_reschedule_delta_default(self):
        today = date(2027, 2, 14)
        delta_default = parse_reschedule_delta(today, "Can we postpone this?")
        assert delta_default == 14


class TestDomainConstantsAndExceptions:
    """Verify integrity of extracted domain constants and custom exceptions."""

    def test_custom_exception_hierarchy(self):
        err = ChatServiceError("Chat failed")
        assert isinstance(err, UtsavAIException)
        assert str(err) == "Chat failed"

        ai_err = AIProviderError("LLM failed")
        assert isinstance(ai_err, UtsavAIException)

        plan_err = PlanningEngineException("Engine failed")
        assert isinstance(plan_err, UtsavAIException)

    def test_base_allocations_defined(self):
        assert EventType.WEDDING in BASE_ALLOCATIONS
        assert EventType.BIRTHDAY in BASE_ALLOCATIONS
        assert "Catering" in BASE_ALLOCATIONS[EventType.WEDDING]

    def test_multipliers_integrity(self):
        assert CITY_MULTIPLIERS[CityTier.METRO] > CITY_MULTIPLIERS[CityTier.TIER3]
        assert SEASON_MULTIPLIERS[Season.PEAK] > SEASON_MULTIPLIERS[Season.OFF]
        assert MIN_PER_HEAD_INR[EventType.WEDDING] > 0
        assert len(FESTIVAL_CLUSTERS) > 0
