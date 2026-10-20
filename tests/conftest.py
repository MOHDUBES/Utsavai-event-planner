"""
Shared fixtures for UtsavAI test suite.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.models.schemas import (
    CityTier,
    DietaryType,
    EventRequest,
    EventType,
    PriorityArea,
    VenueType,
)

# ─────────────────────────────────────────────────────────────
# Date fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def future_date() -> date:
    """A date 180 days in the future — plenty of lead time."""
    return date.today() + timedelta(days=180)


@pytest.fixture
def close_date() -> date:
    """A date 15 days in the future — compressed timeline."""
    return date.today() + timedelta(days=15)


@pytest.fixture
def past_date() -> date:
    """A date in the past — should generate warnings."""
    return date.today() - timedelta(days=30)


# ─────────────────────────────────────────────────────────────
# Event request fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def wedding_request(future_date: date) -> EventRequest:
    """Standard wedding request — Delhi, 200 guests, ₹10L."""
    return EventRequest(
        event_type=EventType.WEDDING,
        event_date=future_date,
        city="Delhi",
        city_tier=CityTier.METRO,
        guest_count=200,
        total_budget_inr=1_000_000.0,
        theme="Royal Rajasthani",
        dietary=DietaryType.VEG,
        cultural_customs="North Indian Hindu ceremony",
        religion_culture="Hindu",
        venue_type=VenueType.INDOOR,
        priorities=[PriorityArea.FOOD, PriorityArea.VENUE, PriorityArea.PHOTOGRAPHY],
    )


@pytest.fixture
def birthday_request(future_date: date) -> EventRequest:
    """Kid's birthday — Mumbai, 30 guests, ₹40K."""
    return EventRequest(
        event_type=EventType.BIRTHDAY,
        event_date=future_date,
        city="Mumbai",
        city_tier=CityTier.METRO,
        guest_count=30,
        total_budget_inr=40_000.0,
        theme="Superheroes",
        dietary=DietaryType.VEG,
        venue_type=VenueType.INDOOR,
        priorities=[PriorityArea.DECOR, PriorityArea.ENTERTAINMENT],
    )


@pytest.fixture
def diwali_mela_request(future_date: date) -> EventRequest:
    """Society Diwali Mela — Jaipur, 500 guests, ₹1.5L."""
    return EventRequest(
        event_type=EventType.DIWALI_MELA,
        event_date=future_date,
        city="Jaipur",
        city_tier=CityTier.TIER2,
        guest_count=500,
        total_budget_inr=150_000.0,
        dietary=DietaryType.VEG,
        venue_type=VenueType.OUTDOOR,
        priorities=[PriorityArea.FOOD, PriorityArea.DECOR],
    )


@pytest.fixture
def minimal_request(future_date: date) -> EventRequest:
    """Minimal valid request."""
    return EventRequest(
        event_type=EventType.OTHER,
        event_date=future_date,
        city="Pune",
        city_tier=CityTier.TIER2,
        guest_count=10,
        total_budget_inr=10_000.0,
    )


# ─────────────────────────────────────────────────────────────
# HTTP client fixture
# ─────────────────────────────────────────────────────────────


@pytest.fixture
async def client() -> AsyncClient:
    """Async HTTP client for API endpoint testing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ─────────────────────────────────────────────────────────────
# Valid API payload
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def wedding_payload(future_date: date) -> dict:
    """JSON payload for wedding plan API call."""
    return {
        "event_type": "wedding",
        "event_date": str(future_date),
        "city": "Delhi",
        "city_tier": "metro",
        "guest_count": 200,
        "total_budget_inr": 1_000_000,
        "theme": "Royal Rajasthani",
        "dietary": "veg",
        "cultural_customs": "North Indian Hindu",
        "religion_culture": "Hindu",
        "venue_type": "indoor",
        "priorities": ["food", "venue", "photography"],
    }


def _make_request(
    event_type: EventType = EventType.WEDDING,
    event_date: date | None = None,
    city_tier: CityTier = CityTier.METRO,
    guest_count: int = 100,
    total_budget_inr: float = 500_000,
    dietary: DietaryType = DietaryType.VEG,
    venue_type: VenueType = VenueType.INDOOR,
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
        venue_type=venue_type,
    )
