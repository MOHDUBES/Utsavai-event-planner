"""
Tests for the Vendor Checklist Engine.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.models.schemas import (
    CityTier,
    DietaryType,
    EventRequest,
    EventType,
    VenueType,
)
from backend.services.vendor_engine import generate_vendor_checklist


def make_vendor_req(
    event_type: EventType = EventType.WEDDING,
    city_tier: CityTier = CityTier.METRO,
    venue_type: VenueType = VenueType.INDOOR,
    dietary: DietaryType = DietaryType.VEG,
    guest_count: int = 150,
) -> EventRequest:
    return EventRequest(
        event_type=event_type,
        event_date=date.today() + timedelta(days=90),
        city="Delhi",
        city_tier=city_tier,
        guest_count=guest_count,
        total_budget_inr=500_000,
        dietary=dietary,
        venue_type=venue_type,
    )


class TestVendorChecklistEngine:
    """Vendor checklist generation tests."""

    def test_wedding_includes_core_and_specific_vendors(self):
        req = make_vendor_req(EventType.WEDDING)
        checklist = generate_vendor_checklist(req)
        categories = {item.category for item in checklist.items}

        assert "Venue" in categories
        assert "Catering" in categories
        assert "Decoration" in categories
        assert "Photography & Videography" in categories
        assert "Invitations & Stationery" in categories
        assert "Pandit / Officiant / Religious Authority" in categories
        assert "Makeup & Grooming" in categories
        assert "Music & Entertainment" in categories
        assert "Transport & Logistics" in categories
        assert checklist.total_categories == len(checklist.items)

    def test_birthday_includes_cake_and_music(self):
        req = make_vendor_req(EventType.BIRTHDAY)
        checklist = generate_vendor_checklist(req)
        categories = {item.category for item in checklist.items}

        assert "Cake & Sweets" in categories
        assert "Music & Entertainment" in categories
        assert "Makeup & Grooming" not in categories

    def test_outdoor_event_includes_permissions_and_noc(self):
        req = make_vendor_req(EventType.BIRTHDAY, venue_type=VenueType.OUTDOOR)
        checklist = generate_vendor_checklist(req)
        categories = {item.category for item in checklist.items}

        assert "Permissions & NOC" in categories

    def test_college_fest_includes_av_and_permissions(self):
        req = make_vendor_req(EventType.COLLEGE_FEST)
        checklist = generate_vendor_checklist(req)
        categories = {item.category for item in checklist.items}

        assert "AV & Stage Equipment" in categories
        assert "Permissions & NOC" in categories

    def test_corporate_event_vendors(self):
        req = make_vendor_req(EventType.CORPORATE)
        checklist = generate_vendor_checklist(req)
        categories = {item.category for item in checklist.items}

        assert "AV & Stage Equipment" in categories
        assert "Transport & Logistics" in categories

    def test_city_tier_multipliers(self):
        req_metro = make_vendor_req(EventType.WEDDING, city_tier=CityTier.METRO)
        req_tier3 = make_vendor_req(EventType.WEDDING, city_tier=CityTier.TIER3)

        checklist_metro = generate_vendor_checklist(req_metro)
        checklist_tier3 = generate_vendor_checklist(req_tier3)

        metro_venue = next(i for i in checklist_metro.items if i.category == "Venue")
        tier3_venue = next(i for i in checklist_tier3.items if i.category == "Venue")

        assert metro_venue.estimated_cost_max_inr > tier3_venue.estimated_cost_max_inr

    @pytest.mark.parametrize(
        "dietary,expected_keyword",
        [
            (DietaryType.JAIN, "onion"),
            (DietaryType.HALAL, "Halal"),
            (DietaryType.VEG, "vegetarian"),
            (DietaryType.NON_VEG, "non-veg"),
            (DietaryType.MIXED, "separate"),
        ],
    )
    def test_dietary_instructions_customized(self, dietary: DietaryType, expected_keyword: str):
        req = make_vendor_req(EventType.WEDDING, dietary=dietary)
        checklist = generate_vendor_checklist(req)
        caterer = next(i for i in checklist.items if i.category == "Catering")

        assert (
            any(
                expected_keyword.lower() in q.lower()
                or expected_keyword.lower() in caterer.notes.lower()
                for q in caterer.questions_to_ask
            )
            or expected_keyword.lower() in caterer.notes.lower()
        )

    def test_vendor_item_fields_populated(self):
        req = make_vendor_req(EventType.WEDDING)
        checklist = generate_vendor_checklist(req)

        for item in checklist.items:
            assert item.category
            assert item.vendor_type
            assert len(item.questions_to_ask) >= 2
            assert item.booking_lead_time_days > 0
            assert item.estimated_cost_min_inr > 0
            assert item.estimated_cost_max_inr >= item.estimated_cost_min_inr
