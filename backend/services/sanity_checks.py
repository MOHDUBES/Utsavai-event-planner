"""
Sanity Check Engine – validates event parameters and flags conflicts.

Checks:
- Weekday vs weekend pricing note
- Monsoon warning for outdoor events
- Festival-date clash note
- Guest-to-budget sanity
- Very large guest counts
"""

from __future__ import annotations

from datetime import date

from backend.constants import FESTIVAL_CLUSTERS
from backend.models.schemas import (
    EventRequest,
    SanityCheck,
    Season,
    VenueType,
)
from backend.services.budget_engine import detect_season


def run_sanity_checks(req: EventRequest, today: date | None = None) -> list[SanityCheck]:
    """
    Run all sanity checks on the event request.

    Args:
        req: Event request to validate.
        today: Override today's date (for testing).

    Returns:
        List of SanityCheck results.
    """
    if today is None:
        today = date.today()

    checks: list[SanityCheck] = []

    checks.append(_check_past_date(req, today))
    checks.append(_check_too_close(req, today))
    checks.append(_check_weekday(req))
    checks.append(_check_monsoon_outdoor(req))
    checks.append(_check_festival_clash(req))
    checks.append(_check_budget_per_head(req))
    checks.append(_check_large_guest_count(req))
    checks.append(_check_guest_venue_capacity(req))

    # Filter out None checks (shouldn't happen but safety)
    return [c for c in checks if c is not None]


def _check_past_date(req: EventRequest, today: date) -> SanityCheck:
    if req.event_date < today:
        return SanityCheck(
            check_name="Event Date",
            status="error",
            message=f"Event date {req.event_date} is in the past.",
            suggestion="Please update the event date to a future date.",
        )
    days_until = (req.event_date - today).days
    return SanityCheck(
        check_name="Event Date",
        status="ok",
        message=f"Event is {days_until} days away ({req.event_date}).",
    )


def _check_too_close(req: EventRequest, today: date) -> SanityCheck:
    days_until = (req.event_date - today).days
    if 0 < days_until < 14:
        return SanityCheck(
            check_name="Booking Lead Time",
            status="warning",
            message=f"Only {days_until} days until the event — very little time to book vendors.",
            suggestion="Focus immediately on venue and caterer. Consider semi-catered options.",
        )
    if 14 <= days_until < 30:
        return SanityCheck(
            check_name="Booking Lead Time",
            status="warning",
            message=f"{days_until} days until event. Some premium vendors may already be booked.",
            suggestion="Contact vendors immediately and have backup options ready.",
        )
    return SanityCheck(
        check_name="Booking Lead Time",
        status="ok",
        message=f"Sufficient lead time ({days_until} days) to book most vendors.",
    )


def _check_weekday(req: EventRequest) -> SanityCheck:
    """Weekday events can be cheaper for venues."""
    day_of_week = req.event_date.weekday()  # 0=Monday, 6=Sunday
    day_name = req.event_date.strftime("%A")
    if day_of_week < 5:  # Monday-Friday
        return SanityCheck(
            check_name="Day of Week",
            status="warning",
            message=f"Event falls on a {day_name} (weekday). "
            "Venues are cheaper but guest attendance may be lower.",
            suggestion="Negotiate a 15–25% weekday discount with venues and caterers.",
        )
    return SanityCheck(
        check_name="Day of Week",
        status="ok",
        message=f"Event falls on {day_name} (weekend) — ideal for guest attendance.",
    )


def _check_monsoon_outdoor(req: EventRequest) -> SanityCheck:
    """Warn about outdoor events during monsoon season."""
    season = detect_season(req.event_date)
    if req.venue_type == VenueType.OUTDOOR and season == Season.OFF:
        month_name = req.event_date.strftime("%B")
        return SanityCheck(
            check_name="Weather Risk",
            status="warning",
            message=f"Outdoor event in {month_name} — monsoon/summer season risk.",
            suggestion="Budget for weatherproof tent/marquee (₹20,000–₹80,000). "
            "Plan a reliable indoor backup option.",
        )
    if req.venue_type == VenueType.OUTDOOR:
        return SanityCheck(
            check_name="Weather Risk",
            status="ok",
            message="Outdoor event in a good season. Still keep a weather contingency plan.",
        )
    return SanityCheck(
        check_name="Weather Risk",
        status="ok",
        message="Indoor venue — no weather risk.",
    )


def _check_festival_clash(req: EventRequest) -> SanityCheck:
    """Check if event date clashes with a major festival."""
    month = req.event_date.month
    day = req.event_date.day

    for f_month, f_start, f_end, festival_name in FESTIVAL_CLUSTERS:
        if month == f_month and f_start <= day <= f_end:
            return SanityCheck(
                check_name="Festival Calendar",
                status="warning",
                message=f"Event date overlaps with {festival_name}. "
                "Venue and vendor availability may be very limited.",
                suggestion=f"Book all vendors immediately. Expect 20–40% higher rates during {festival_name}.",
            )

    return SanityCheck(
        check_name="Festival Calendar",
        status="ok",
        message="No major festival clash detected. Good date choice.",
    )


def _check_budget_per_head(req: EventRequest) -> SanityCheck:
    """Sanity check per-head cost against realistic minimums."""
    from backend.services.budget_engine import (
        CITY_MULTIPLIERS,
        MIN_PER_HEAD_INR,
        SEASON_MULTIPLIERS,
    )

    season = detect_season(req.event_date)
    min_ph = MIN_PER_HEAD_INR.get(req.event_type, 300.0)
    effective_min = min_ph * CITY_MULTIPLIERS[req.city_tier] * SEASON_MULTIPLIERS[season]
    per_head = req.total_budget_inr / req.guest_count

    if per_head < effective_min * 0.7:
        return SanityCheck(
            check_name="Budget Realism",
            status="error",
            message=f"Budget of ₹{per_head:,.0f}/head is well below the realistic minimum "
            f"of ₹{effective_min:,.0f}/head for this event.",
            suggestion=f"Increase total budget to at least ₹{effective_min * req.guest_count:,.0f} "
            f"or reduce guest count.",
        )
    if per_head < effective_min:
        return SanityCheck(
            check_name="Budget Realism",
            status="warning",
            message=f"Budget of ₹{per_head:,.0f}/head is tight (minimum: ₹{effective_min:,.0f}/head).",
            suggestion="Prioritize food and venue; cut on decor and photography.",
        )
    return SanityCheck(
        check_name="Budget Realism",
        status="ok",
        message=f"Budget of ₹{per_head:,.0f}/head is realistic for this event type.",
    )


def _check_large_guest_count(req: EventRequest) -> SanityCheck:
    """Flag very large events that need extra planning."""
    if req.guest_count > 1_000:
        return SanityCheck(
            check_name="Guest Count",
            status="warning",
            message=f"{req.guest_count} guests is a very large event requiring professional event management.",
            suggestion="Hire an Event Management Company (EMC). Budget ₹50,000–₹2,00,000 for professional coordination.",
        )
    if req.guest_count > 500:
        return SanityCheck(
            check_name="Guest Count",
            status="warning",
            message=f"{req.guest_count} guests requires police permission and crowd management planning.",
            suggestion="Get police NOC 30 days before. Plan multiple entry/exit points and first-aid.",
        )
    return SanityCheck(
        check_name="Guest Count",
        status="ok",
        message=f"Guest count ({req.guest_count}) is manageable.",
    )


def _check_guest_venue_capacity(req: EventRequest) -> SanityCheck:
    """Warn if guest count seems high for event budget (venue capacity proxy)."""
    # Approximate minimum venue cost per guest for seated events
    venue_floor_per_guest = {
        "metro": 200,
        "tier2": 120,
        "tier3": 80,
    }.get(req.city_tier.value, 150)

    estimated_min_venue_cost = venue_floor_per_guest * req.guest_count
    total_budget = req.total_budget_inr

    if estimated_min_venue_cost > total_budget * 0.40:
        return SanityCheck(
            check_name="Venue Capacity",
            status="warning",
            message=f"Venue cost alone may exceed 40% of total budget for {req.guest_count} guests.",
            suggestion="Consider a community hall, RWA space, or outdoor lawn to reduce venue cost.",
        )
    return SanityCheck(
        check_name="Venue Capacity",
        status="ok",
        message="Guest count and budget are compatible for venue options in this city.",
    )
