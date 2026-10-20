"""
Budget Engine – deterministic, rule-based budget allocation for UtsavAI.

Algorithm:
1. Start with base percentages per event type.
2. Apply city-tier multiplier (metro costs 30-50% more than tier-3).
3. Apply season multiplier (peak Oct-Feb is 20% dearer).
4. Shift allocation percentages toward user-specified priorities.
5. Scale to actual total budget, reserve 10% contingency.
6. Compute per-head cost and warn if unrealistic.
7. Suggest minimum viable budget if too low.
"""

from __future__ import annotations

from datetime import date

from backend.models.schemas import (
    BudgetBreakdown,
    BudgetLineItem,
    CityTier,
    EventRequest,
    EventType,
    PriorityArea,
    Season,
)

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

# Base allocation percentages by event type (sum to ~90%; 10% reserved for contingency)
# Keys are budget category names.
BASE_ALLOCATIONS: dict[str, dict[str, float]] = {
    EventType.WEDDING: {
        "Venue": 25.0,
        "Catering": 30.0,
        "Decor & Florals": 12.0,
        "Photography & Video": 10.0,
        "Music & Entertainment": 4.0,
        "Bridal/Groom Makeup & Attire": 5.0,
        "Invitations & Stationery": 2.0,
        "Pandit / Officiant": 2.0,
        "Transport & Logistics": 3.0,
        "Gifts & Return Favours": 3.0,
        "Miscellaneous": 4.0,
    },
    EventType.BIRTHDAY: {
        "Venue": 20.0,
        "Catering": 30.0,
        "Decor & Balloons": 18.0,
        "Photography": 8.0,
        "Entertainment & Games": 10.0,
        "Cake": 7.0,
        "Invitations & Return Gifts": 4.0,
        "Miscellaneous": 3.0,
    },
    EventType.DIWALI_MELA: {
        "Venue / Ground": 15.0,
        "Food Stalls & Catering": 30.0,
        "Lighting & Decor": 20.0,
        "Entertainment & Cultural Programs": 12.0,
        "Puja & Ceremonial": 5.0,
        "Permissions & NOC": 5.0,
        "Invitations & Promotions": 4.0,
        "Cleanup & Logistics": 5.0,
        "Miscellaneous": 4.0,
    },
    EventType.EID_CELEBRATION: {
        "Venue": 20.0,
        "Catering & Biryani": 35.0,
        "Decor": 12.0,
        "Photography": 8.0,
        "Entertainment": 8.0,
        "Invitations": 3.0,
        "Transport": 5.0,
        "Miscellaneous": 9.0,
    },
    EventType.NAVRATRI: {
        "Venue / Pandal": 20.0,
        "Catering (Satvik/Fasting food)": 25.0,
        "Decor & Lighting": 18.0,
        "Garba Music & DJ": 15.0,
        "Puja & Ceremonial": 7.0,
        "Permissions & NOC": 5.0,
        "Invitations": 3.0,
        "Miscellaneous": 7.0,
    },
    EventType.COLLEGE_FEST: {
        "Venue & Stage": 20.0,
        "Catering & Stalls": 20.0,
        "Decor & Branding": 12.0,
        "Performers & Artists": 20.0,
        "AV & Equipment": 10.0,
        "Invitations & Promotions": 8.0,
        "Security & Logistics": 5.0,
        "Miscellaneous": 5.0,
    },
    EventType.CORPORATE: {
        "Venue": 25.0,
        "Catering": 25.0,
        "AV & Technology": 12.0,
        "Decor & Branding": 10.0,
        "Photography & Video": 8.0,
        "Transport": 5.0,
        "Gifting": 8.0,
        "Miscellaneous": 7.0,
    },
    EventType.ANNIVERSARY: {
        "Venue": 22.0,
        "Catering": 30.0,
        "Decor": 15.0,
        "Photography": 12.0,
        "Entertainment": 8.0,
        "Cake & Flowers": 6.0,
        "Miscellaneous": 7.0,
    },
    EventType.BABY_SHOWER: {
        "Venue": 20.0,
        "Catering": 30.0,
        "Decor & Themes": 20.0,
        "Photography": 10.0,
        "Games & Activities": 8.0,
        "Return Gifts": 7.0,
        "Miscellaneous": 5.0,
    },
    EventType.RWA_EVENT: {
        "Venue / Community Hall": 15.0,
        "Catering": 30.0,
        "Decor & Lighting": 18.0,
        "Entertainment": 12.0,
        "Permissions & NOC": 7.0,
        "Sound & AV": 8.0,
        "Miscellaneous": 10.0,
    },
    EventType.OTHER: {
        "Venue": 25.0,
        "Catering": 30.0,
        "Decor": 15.0,
        "Entertainment": 10.0,
        "Miscellaneous": 20.0,
    },
}

# Minimum cost per head by event type (INR) – Indian market benchmarks
MIN_PER_HEAD_INR: dict[str, float] = {
    EventType.WEDDING: 1_500.0,
    EventType.BIRTHDAY: 300.0,
    EventType.DIWALI_MELA: 150.0,
    EventType.EID_CELEBRATION: 600.0,
    EventType.NAVRATRI: 150.0,
    EventType.COLLEGE_FEST: 200.0,
    EventType.CORPORATE: 800.0,
    EventType.ANNIVERSARY: 600.0,
    EventType.BABY_SHOWER: 400.0,
    EventType.RWA_EVENT: 150.0,
    EventType.OTHER: 300.0,
}

# City tier cost multipliers (relative to tier-3 base)
CITY_MULTIPLIERS: dict[str, float] = {
    CityTier.METRO: 1.45,
    CityTier.TIER2: 1.20,
    CityTier.TIER3: 1.00,
}

# Season multipliers (peak Oct-Feb in India)
SEASON_MULTIPLIERS: dict[str, float] = {
    Season.PEAK: 1.20,
    Season.SHOULDER: 1.05,
    Season.OFF: 0.90,
}

# Priority area → budget category mapping
PRIORITY_CATEGORY_MAP: dict[str, list[str]] = {
    PriorityArea.FOOD: [
        "Catering",
        "Catering & Biryani",
        "Food Stalls & Catering",
        "Catering (Satvik/Fasting food)",
        "Catering & Stalls",
    ],
    PriorityArea.DECOR: [
        "Decor & Florals",
        "Decor & Balloons",
        "Decor",
        "Lighting & Decor",
        "Decor & Lighting",
        "Decor & Themes",
        "Decor & Branding",
    ],
    PriorityArea.PHOTOGRAPHY: ["Photography & Video", "Photography"],
    PriorityArea.MUSIC: [
        "Music & Entertainment",
        "Garba Music & DJ",
        "Entertainment",
        "Entertainment & Games",
        "Entertainment & Cultural Programs",
        "Performers & Artists",
        "AV & Equipment",
    ],
    PriorityArea.VENUE: [
        "Venue",
        "Venue / Ground",
        "Venue / Pandal",
        "Venue & Stage",
        "Venue / Community Hall",
    ],
    PriorityArea.ENTERTAINMENT: [
        "Entertainment",
        "Entertainment & Games",
        "Entertainment & Cultural Programs",
        "Performers & Artists",
    ],
    PriorityArea.INVITATIONS: [
        "Invitations & Stationery",
        "Invitations & Return Gifts",
        "Invitations & Promotions",
        "Invitations",
    ],
    PriorityArea.TRANSPORT: ["Transport & Logistics", "Transport"],
}


# Large-event guest scaling: per-head cost goes down slightly for very large events
def _guest_scale_factor(guest_count: int) -> float:
    """Return economy-of-scale factor for catering/venue."""
    if guest_count <= 50:
        return 1.10
    elif guest_count <= 150:
        return 1.00
    elif guest_count <= 500:
        return 0.92
    elif guest_count <= 1_000:
        return 0.85
    else:
        return 0.78


# ─────────────────────────────────────────────────────────────
# Season detection
# ─────────────────────────────────────────────────────────────


def detect_season(event_date: date) -> Season:
    """
    Classify the event month into an Indian wedding/festive season.

    Peak   : Oct, Nov, Dec, Jan, Feb  (wedding + festival season)
    Shoulder: Mar, Apr, Sep
    Off    : May, Jun, Jul, Aug       (summer / monsoon)
    """
    month = event_date.month
    if month in {10, 11, 12, 1, 2}:
        return Season.PEAK
    elif month in {3, 4, 9}:
        return Season.SHOULDER
    else:
        return Season.OFF


# ─────────────────────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────────────────────


def calculate_budget(req: EventRequest) -> BudgetBreakdown:
    """
    Deterministically compute the full budget breakdown.

    Steps:
    1. Detect season.
    2. Fetch base allocation percentages for event type.
    3. Boost priority categories by reallocating from lower-priority ones.
    4. Apply guest-count scale factor.
    5. Compute realistic minimum budget.
    6. Reserve 10% contingency; distribute remaining 90% per allocations.
    7. Generate warnings and suggestions.
    """
    season = detect_season(req.event_date)
    base_alloc = dict(BASE_ALLOCATIONS.get(req.event_type, BASE_ALLOCATIONS[EventType.OTHER]))

    # Step 1: Priority boosting
    base_alloc = _apply_priority_boost(base_alloc, req.priorities)

    # Step 2: Contingency reservation – remaining 90% goes to categories
    contingency_pct = 10.0
    distributable_pct = 90.0

    # Normalize allocations to sum to distributable_pct
    total_pct = sum(base_alloc.values())
    normalized_alloc = {k: (v / total_pct) * distributable_pct for k, v in base_alloc.items()}

    # Step 3: Compute effective per-head minimum (with city + season multipliers)
    city_mult = CITY_MULTIPLIERS[req.city_tier]
    season_mult = SEASON_MULTIPLIERS[season]
    guest_scale = _guest_scale_factor(req.guest_count)

    base_min_per_head = MIN_PER_HEAD_INR.get(req.event_type, 300.0)
    effective_min_per_head = base_min_per_head * city_mult * season_mult * guest_scale
    realistic_minimum = effective_min_per_head * req.guest_count * (1 + contingency_pct / 100)

    # Step 4: Distribute budget
    contingency_inr = req.total_budget_inr * (contingency_pct / 100)
    spendable_inr = req.total_budget_inr - contingency_inr

    # Minimum amounts per category (city + season adjusted)
    min_amounts = _compute_min_amounts(req, city_mult, season_mult, normalized_alloc, spendable_inr)

    # Build line items
    line_items: list[BudgetLineItem] = []
    for category, pct in normalized_alloc.items():
        amount = (pct / 100) * req.total_budget_inr
        line_items.append(
            BudgetLineItem(
                category=category,
                percentage=round(pct, 1),
                amount_inr=round(amount, -1),  # Round to nearest ₹10
                min_amount_inr=round(min_amounts.get(category, amount * 0.6), -1),
                notes=_get_category_notes(category, req),
            )
        )

    # Sort by amount descending for readability
    line_items.sort(key=lambda x: x.amount_inr, reverse=True)

    per_head = req.total_budget_inr / req.guest_count
    warnings, suggestions = _generate_warnings(req, per_head, realistic_minimum, season, line_items)

    return BudgetBreakdown(
        total_inr=req.total_budget_inr,
        per_head_inr=round(per_head, 0),
        contingency_inr=round(contingency_inr, -1),
        allocations=line_items,
        warnings=warnings,
        suggestions=suggestions,
        season=season,
        city_tier=req.city_tier,
        realistic_minimum_inr=round(realistic_minimum, -2),
    )


def _apply_priority_boost(
    alloc: dict[str, float],
    priorities: list[PriorityArea],
) -> dict[str, float]:
    """
    Boost the top-3 priority categories by 20/10/5% points respectively,
    balanced by reducing lower-priority categories proportionally.
    """
    if not priorities:
        return alloc

    boost_amounts = [20.0, 10.0, 5.0]  # % points to boost for top-3 priorities
    alloc = dict(alloc)

    for idx, priority in enumerate(priorities[:3]):
        boost = boost_amounts[idx]
        mapped = PRIORITY_CATEGORY_MAP.get(priority, [])
        target_keys = [k for k in alloc if any(m in k for m in mapped)]
        if not target_keys:
            continue

        per_key_boost = boost / len(target_keys)
        total_boost = per_key_boost * len(target_keys)

        # Add boost to priority categories
        for key in target_keys:
            alloc[key] += per_key_boost

        # Reduce non-priority categories proportionally
        non_priority = [k for k in alloc if k not in target_keys]
        if non_priority:
            total_non = sum(alloc[k] for k in non_priority)
            if total_non > 0:
                reduction_factor = total_boost / total_non
                for key in non_priority:
                    alloc[key] = max(1.0, alloc[key] * (1 - reduction_factor))

    return alloc


def _compute_min_amounts(
    req: EventRequest,
    city_mult: float,
    season_mult: float,
    normalized_alloc: dict[str, float],
    spendable_inr: float,
) -> dict[str, float]:
    """Compute minimum viable amount per category based on market rates."""
    # Use 60% of allocated amount as minimum (you can always spend less on decor etc.)
    return {k: (pct / 100) * spendable_inr * 0.6 for k, pct in normalized_alloc.items()}


def _get_category_notes(category: str, req: EventRequest) -> str:
    """Return context-sensitive notes for a budget category."""
    notes_map: dict[str, str] = {
        "Catering": f"Based on ₹{MIN_PER_HEAD_INR.get(req.event_type, 300):.0f}–₹{MIN_PER_HEAD_INR.get(req.event_type, 300) * 2:.0f}/head. Negotiate bulk discounts.",
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
    # Partial match lookup
    for key, note in notes_map.items():
        if key.lower() in category.lower():
            return note
    return ""


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

    # Warning: budget below realistic minimum
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

    # Warning: peak season premium
    if season == Season.PEAK:
        warnings.append(
            "⚠️ Peak season (Oct–Feb): venue and catering vendors charge 15–25% premium. "
            "Book early and negotiate fixed rates."
        )

    # Warning: off-season outdoor
    if req.venue_type == "outdoor" and season == Season.OFF:
        warnings.append(
            "⚠️ Monsoon season (May–Aug) for outdoor events: arrange weather contingency (tent/marquee)."
        )

    # Warning: Miscellaneous is very low
    misc_items = [li for li in line_items if "Misc" in li.category]
    if misc_items and misc_items[0].amount_inr < 5_000:
        warnings.append(
            "⚠️ Miscellaneous fund is very low (< ₹5,000). Unexpected expenses are common."
        )

    # Suggestion: reduce per-head catering cost
    if per_head > 5_000 and req.event_type != EventType.WEDDING:
        suggestions.append(
            "💡 Consider a buffet format instead of plated meals to reduce catering cost by 20–30%."
        )

    return warnings, suggestions
