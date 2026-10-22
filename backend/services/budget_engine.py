"""
Budget Engine – deterministic, rule-based budget allocation for UtsavAI.
"""

from __future__ import annotations

from datetime import date

from backend.constants import (
    BASE_ALLOCATIONS,
    CITY_MULTIPLIERS,
    MIN_PER_HEAD_INR,
    PRIORITY_CATEGORY_MAP,
    SEASON_MULTIPLIERS,
)
from backend.models.schemas import (
    BudgetBreakdown,
    BudgetLineItem,
    EventRequest,
    EventType,
    PriorityArea,
    Season,
)

CONTINGENCY_PERCENTAGE = 10.0
DISTRIBUTABLE_PERCENTAGE = 90.0


def detect_season(event_date: date) -> Season:
    """Detect season based on month: Peak (Oct-Feb), Shoulder (Mar-Apr, Sep), Off (May-Aug)."""
    month = event_date.month
    if month in (10, 11, 12, 1, 2):
        return Season.PEAK
    if month in (3, 4, 9):
        return Season.SHOULDER
    return Season.OFF


def _guest_scale_factor(guest_count: int) -> float:
    """Return economy-of-scale factor for catering/venue."""
    if guest_count <= 50:
        return 1.10
    if guest_count <= 150:
        return 1.00
    if guest_count <= 300:
        return 0.95
    if guest_count <= 600:
        return 0.90
    return 0.85


def _calculate_effective_min(req: EventRequest, season: Season) -> float:
    """Compute realistic minimum budget based on city tier, season, and guest scaling."""
    city_mult = CITY_MULTIPLIERS[req.city_tier]
    season_mult = SEASON_MULTIPLIERS[season]
    guest_scale = _guest_scale_factor(req.guest_count)
    base_min = MIN_PER_HEAD_INR.get(req.event_type, 300.0)
    effective_min_per_head = base_min * city_mult * season_mult * guest_scale
    return effective_min_per_head * req.guest_count * (1 + CONTINGENCY_PERCENTAGE / 100)


def _build_line_items(
    normalized_alloc: dict[str, float],
    total_budget_inr: float,
    spendable_inr: float,
    req: EventRequest,
) -> list[BudgetLineItem]:
    """Construct BudgetLineItem models for each normalized allocation category."""
    line_items: list[BudgetLineItem] = []
    for category, pct in normalized_alloc.items():
        amount = (pct / 100) * total_budget_inr
        min_amount = (pct / 100) * spendable_inr * 0.6
        line_items.append(
            BudgetLineItem(
                category=category,
                percentage=round(pct, 1),
                amount_inr=round(amount, -1),
                min_amount_inr=round(min_amount, -1),
                notes=_get_category_notes(category, req),
            )
        )
    line_items.sort(key=lambda x: x.amount_inr, reverse=True)
    return line_items


def calculate_budget(req: EventRequest) -> BudgetBreakdown:
    """Deterministically compute the full budget breakdown."""
    season = detect_season(req.event_date)
    base_alloc = dict(BASE_ALLOCATIONS.get(req.event_type, BASE_ALLOCATIONS[EventType.OTHER]))
    base_alloc = _apply_priority_boost(base_alloc, req.priorities)

    total_pct = sum(base_alloc.values())
    normalized_alloc = {
        k: (v / total_pct) * DISTRIBUTABLE_PERCENTAGE for k, v in base_alloc.items()
    }
    realistic_min = _calculate_effective_min(req, season)

    contingency_inr = req.total_budget_inr * (CONTINGENCY_PERCENTAGE / 100)
    spendable_inr = req.total_budget_inr - contingency_inr

    line_items = _build_line_items(normalized_alloc, req.total_budget_inr, spendable_inr, req)
    per_head = req.total_budget_inr / req.guest_count
    warnings, suggestions = _generate_warnings(req, per_head, realistic_min, season, line_items)

    return BudgetBreakdown(
        total_inr=req.total_budget_inr,
        per_head_inr=round(per_head, 0),
        contingency_inr=round(contingency_inr, -1),
        allocations=line_items,
        warnings=warnings,
        suggestions=suggestions,
        season=season,
        city_tier=req.city_tier,
        realistic_minimum_inr=round(realistic_min, -2),
    )


def _apply_priority_boost(
    alloc: dict[str, float],
    priorities: list[PriorityArea],
) -> dict[str, float]:
    """Boost the top-3 priority categories by 20/10/5% points respectively."""
    if not priorities:
        return alloc

    boost_amounts = [20.0, 10.0, 5.0]
    result = dict(alloc)

    for idx, priority in enumerate(priorities[:3]):
        boost = boost_amounts[idx]
        mapped = PRIORITY_CATEGORY_MAP.get(priority, [])
        target_keys = [k for k in result if any(m in k for m in mapped)]
        if not target_keys:
            continue

        per_key_boost = boost / len(target_keys)
        total_boost = per_key_boost * len(target_keys)
        for key in target_keys:
            result[key] += per_key_boost

        non_priority = [k for k in result if k not in target_keys]
        if non_priority:
            total_non = sum(result[k] for k in non_priority)
            if total_non > 0:
                reduction_factor = total_boost / total_non
                for key in non_priority:
                    result[key] = max(1.0, result[key] * (1 - reduction_factor))

    return result


def _get_category_notes(category: str, req: EventRequest) -> str:
    """Return context-sensitive notes for a budget category."""
    base_min = MIN_PER_HEAD_INR.get(req.event_type, 300.0)
    notes_map: dict[str, str] = {
        "Catering": f"Based on ₹{base_min:.0f}–₹{base_min * 2:.0f}/head. Negotiate bulk discounts.",
        "Catering & Biryani": "Halal catering; get quotes from 3+ vendors.",
        "Venue": "Book 60-90 days early; check for advance payment requirements.",
        "Venue / Ground": "Verify open-air permits and noise regulations.",
        "Photography & Video": "Includes candid + traditional + highlight reel.",
        "Decor & Florals": "Fresh flowers cost 40% more in peak season.",
        "Decor & Lighting": "LED lighting can cut costs by 30% vs traditional.",
        "Permissions & NOC": "Allow 4-6 weeks for municipal/RWA permissions.",
        "Music & Entertainment": "Check noise ordinance curfew times.",
        "Garba Music & DJ": "Confirm sound system capability for open-air venue.",
    }
    for key, note in notes_map.items():
        if key.lower() in category.lower():
            return note
    return ""


def _check_budget_shortfall(
    req: EventRequest, realistic_minimum: float, warnings: list[str], suggestions: list[str]
) -> None:
    """Check whether budget is below market minimum and append guidance."""
    if req.total_budget_inr < realistic_minimum:
        shortfall = realistic_minimum - req.total_budget_inr
        warnings.append(
            f"⚠️ Your budget (₹{req.total_budget_inr:,.0f}) is ₹{shortfall:,.0f} below the "
            f"realistic minimum (₹{realistic_minimum:,.0f}) for this event type, guest count, "
            f"city tier, and season."
        )
        suggestions.append(f"💡 Increase your budget to at least ₹{realistic_minimum:,.0f}")
        suggestions.append(
            f"💡 Or reduce guest count to {int(req.total_budget_inr / (realistic_minimum / req.guest_count))} guests"
        )


def _check_season_weather(req: EventRequest, season: Season, warnings: list[str]) -> None:
    """Check season-specific premium and outdoor monsoon warnings."""
    if season == Season.PEAK:
        warnings.append(
            "⚠️ Peak season (Oct–Feb): venue and catering vendors charge 15–25% premium. "
            "Book early and negotiate fixed rates."
        )
    if req.venue_type == "outdoor" and season == Season.OFF:
        warnings.append(
            "⚠️ Monsoon season (May–Aug) for outdoor events: arrange weather contingency (tent/marquee)."
        )


def _generate_warnings(
    req: EventRequest,
    per_head: float,
    realistic_minimum: float,
    season: Season,
    line_items: list[BudgetLineItem],
) -> tuple[list[str], list[str]]:
    """Generate budget warnings and actionable suggestions."""
    warnings: list[str] = []
    suggestions: list[str] = []

    _check_budget_shortfall(req, realistic_minimum, warnings, suggestions)
    _check_season_weather(req, season, warnings)

    misc_items = [li for li in line_items if "Misc" in li.category]
    if misc_items and misc_items[0].amount_inr < 5_000:
        warnings.append(
            "⚠️ Miscellaneous fund is very low (< ₹5,000). Unexpected expenses are common."
        )

    if per_head > 5_000 and req.event_type != EventType.WEDDING:
        suggestions.append(
            "💡 Consider a buffet format instead of plated meals to reduce catering cost by 20–30%."
        )

    return warnings, suggestions
