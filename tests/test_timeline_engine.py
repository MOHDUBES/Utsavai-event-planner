"""
Tests for the Timeline Generator.

Coverage:
- Backward planning correctness
- Compressed timeline for close dates
- Past date handling
- Outdoor event tasks
- Task priority validation
- Edge cases: same-day, very far future
"""

from __future__ import annotations

from datetime import date, timedelta

from backend.models.schemas import (
    CityTier,
    DietaryType,
    EventRequest,
    EventType,
    VenueType,
)
from backend.services.timeline_engine import generate_timeline


def make_req(
    event_type=EventType.WEDDING, days_ahead=180, venue_type=VenueType.INDOOR, guest_count=100
):
    today = date.today()
    return EventRequest(
        event_type=event_type,
        event_date=today + timedelta(days=days_ahead),
        city="Delhi",
        city_tier=CityTier.METRO,
        guest_count=guest_count,
        total_budget_inr=500_000,
        dietary=DietaryType.VEG,
        venue_type=venue_type,
    )


class TestTimelineGeneration:
    """Core timeline generation tests."""

    def test_wedding_timeline_has_tasks(self):
        """Wedding timeline should generate multiple tasks."""
        req = make_req(EventType.WEDDING, 180)
        tl = generate_timeline(req)
        assert len(tl.tasks) > 10

    def test_days_until_event_correct(self):
        """days_until_event should match event date minus today."""
        req = make_req(days_ahead=90)
        today = date.today()
        tl = generate_timeline(req, today=today)
        assert tl.days_until_event == 90

    def test_tasks_sorted_chronologically(self):
        """Tasks should be in reverse chronological order (largest days_before first)."""
        req = make_req(EventType.WEDDING, 180)
        tl = generate_timeline(req)
        days = [t.days_before for t in tl.tasks]
        assert days == sorted(days, reverse=True)

    def test_all_tasks_have_required_fields(self):
        """Every task must have label, task, category, priority, and status."""
        req = make_req(EventType.BIRTHDAY, 60)
        tl = generate_timeline(req)
        for task in tl.tasks:
            assert task.label, f"Task missing label: {task}"
            assert task.task, f"Task missing description: {task}"
            assert task.category, f"Task missing category: {task}"
            assert task.priority in ("critical", "high", "medium", "low"), (
                f"Invalid priority: {task.priority}"
            )
            assert task.status in ("pending", "done"), f"Invalid status: {task.status}"

    def test_all_event_types_generate_timeline(self):
        """Every event type should generate at least 5 tasks."""
        for event_type in EventType:
            req = make_req(event_type, 120)
            tl = generate_timeline(req)
            assert len(tl.tasks) >= 5, f"Too few tasks for {event_type}"

    def test_wedding_has_day_of_task(self):
        """Wedding should include a Day-of coordination task."""
        req = make_req(EventType.WEDDING, 180)
        tl = generate_timeline(req)
        day_of = [t for t in tl.tasks if t.days_before == 0]
        assert len(day_of) > 0, "No Day-of task found"

    def test_task_priority_values_valid(self):
        """Priority values must be from the allowed set."""
        req = make_req(EventType.WEDDING, 180)
        tl = generate_timeline(req)
        valid_priorities = {"critical", "high", "medium", "low"}
        for task in tl.tasks:
            assert task.priority in valid_priorities


class TestCompressedTimeline:
    """Tests for compressed timeline when event is close."""

    def test_compressed_flag_set_for_close_date(self):
        """Event < 30 days away should set is_compressed = True."""
        req = make_req(days_ahead=15)
        tl = generate_timeline(req)
        assert tl.is_compressed is True

    def test_not_compressed_for_distant_date(self):
        """Event > 30 days away should not be compressed."""
        req = make_req(days_ahead=90)
        tl = generate_timeline(req)
        assert tl.is_compressed is False

    def test_compressed_timeline_has_warnings(self):
        """Compressed timeline should have at least one warning."""
        req = make_req(days_ahead=10)
        tl = generate_timeline(req)
        assert len(tl.warnings) > 0
        assert any("days" in w.lower() or "compressed" in w.lower() for w in tl.warnings)

    def test_compressed_tasks_marked_urgent(self):
        """Overdue tasks in compressed timeline should be marked urgent."""
        req = make_req(days_ahead=7)
        tl = generate_timeline(req)
        urgent_tasks = [t for t in tl.tasks if t.is_urgent]
        assert len(urgent_tasks) > 0


class TestPastDate:
    """Tests for past event dates."""

    def test_past_date_zero_days_until(self):
        """Past date should result in days_until_event = 0."""
        req = EventRequest(
            event_type=EventType.BIRTHDAY,
            event_date=date.today() - timedelta(days=30),
            city="Delhi",
            city_tier=CityTier.METRO,
            guest_count=50,
            total_budget_inr=50_000,
            dietary=DietaryType.VEG,
        )
        tl = generate_timeline(req)
        assert tl.days_until_event == 0

    def test_past_date_generates_warning(self):
        """Past date should produce at least one warning."""
        req = EventRequest(
            event_type=EventType.WEDDING,
            event_date=date.today() - timedelta(days=10),
            city="Delhi",
            city_tier=CityTier.METRO,
            guest_count=100,
            total_budget_inr=500_000,
            dietary=DietaryType.VEG,
        )
        tl = generate_timeline(req)
        assert len(tl.warnings) > 0
        assert any("past" in w.lower() for w in tl.warnings)


class TestOutdoorEvents:
    """Tests for outdoor-specific tasks."""

    def test_outdoor_event_has_permission_task(self):
        """Outdoor events should include a permissions/NOC task."""
        req = make_req(EventType.DIWALI_MELA, 90, VenueType.OUTDOOR)
        tl = generate_timeline(req)
        permission_tasks = [
            t for t in tl.tasks if "permission" in t.task.lower() or "NOC" in t.task
        ]
        assert len(permission_tasks) > 0

    def test_outdoor_event_has_weather_task(self):
        """Outdoor events should have a weather contingency task."""
        req = make_req(EventType.DIWALI_MELA, 90, VenueType.OUTDOOR)
        tl = generate_timeline(req)
        weather_tasks = [
            t for t in tl.tasks if "weather" in t.task.lower() or "tent" in t.task.lower()
        ]
        assert len(weather_tasks) > 0

    def test_indoor_no_permission_task(self):
        """Indoor events should not have outdoor permission tasks."""
        req = make_req(EventType.WEDDING, 180, VenueType.INDOOR)
        tl = generate_timeline(req)
        # Indoor weddings don't need outdoor NOC (pandit booking is fine)
        outdoor_tasks = [t for t in tl.tasks if "NOC" in t.task and "outdoor" in t.task.lower()]
        assert len(outdoor_tasks) == 0


class TestTimelineEdgeCases:
    """Edge case tests."""

    def test_very_large_event(self):
        """5000 guests should still generate a valid timeline."""
        req = make_req(EventType.RWA_EVENT, 180, guest_count=5000)
        tl = generate_timeline(req)
        assert len(tl.tasks) >= 5

    def test_far_future_date(self):
        """Event 2 years out should work fine."""
        req = make_req(days_ahead=730)
        tl = generate_timeline(req)
        assert tl.days_until_event == 730
        assert tl.is_compressed is False

    def test_tomorrow(self):
        """Event tomorrow is extremely compressed."""
        req = make_req(days_ahead=1)
        tl = generate_timeline(req)
        assert tl.is_compressed is True
        assert len(tl.warnings) > 0

    def test_today_date(self):
        """Event today should have 0 days until event."""
        today = date.today()
        req = EventRequest(
            event_type=EventType.BIRTHDAY,
            event_date=today,
            city="Delhi",
            city_tier=CityTier.METRO,
            guest_count=20,
            total_budget_inr=20_000,
            dietary=DietaryType.VEG,
        )
        tl = generate_timeline(req)
        assert tl.days_until_event == 0
