"""
Timeline Generator – backward-planned event timeline for UtsavAI.

Generates tasks from T-90 days to Day-of, with:
- Compression when event is < 30 days away
- Priority flags
- Category grouping
- Urgent-task detection when too close
"""

from __future__ import annotations

from datetime import date, timedelta

from backend.models.schemas import (
    EventRequest,
    EventType,
    Timeline,
    TimelineTask,
    VenueType,
)

# ─────────────────────────────────────────────────────────────
# Task template definitions
# ─────────────────────────────────────────────────────────────
# Each entry: (days_before, task_description, category, priority)
# days_before is how many days before the event this should be done BY.

WEDDING_TASKS: list[tuple[int, str, str, str]] = [
    (365, "Set overall wedding budget and consult with families", "Planning", "critical"),
    (270, "Fix wedding date (check auspicious muhurats with pandit)", "Planning", "critical"),
    (240, "Book wedding venue and accommodation", "Venue", "critical"),
    (180, "Finalize caterer and menu tasting", "Catering", "critical"),
    (150, "Book photographer and videographer", "Photography", "critical"),
    (120, "Book decorator / event management company", "Decor", "high"),
    (120, "Send Save-the-Date cards (especially for outstation guests)", "Invitations", "high"),
    (90, "Book pandit/priest; confirm rituals list", "Ceremonial", "critical"),
    (90, "Finalize bridal/groom attire; book makeup artist", "Attire & Makeup", "high"),
    (90, "Book DJ/band/music", "Entertainment", "high"),
    (90, "Arrange transport for bridal party", "Transport", "medium"),
    (75, "Confirm guest list and RSVP deadline", "Guests", "high"),
    (60, "Send formal invitations (printed + WhatsApp)", "Invitations", "high"),
    (60, "Book accommodation for outstation guests", "Logistics", "medium"),
    (45, "Arrange catering staff; confirm dietary needs", "Catering", "high"),
    (45, "Order wedding cake / mithai", "Catering", "medium"),
    (30, "Final venue walkthrough with all vendors", "Venue", "high"),
    (30, "Confirm all bookings with deposit receipts", "Finance", "critical"),
    (21, "Wedding card / invitation final review", "Invitations", "medium"),
    (21, "Arrange dry-run for D-day coordination", "Planning", "medium"),
    (14, "Collect confirmed RSVP headcount; share with caterer", "Guests", "critical"),
    (14, "Final makeup trial and hair trial", "Attire & Makeup", "medium"),
    (7, "Prepare wedding day kit (safety pins, touch-up kit, meds)", "Logistics", "high"),
    (7, "Confirm venue setup schedule with decorator", "Decor", "high"),
    (7, "Brief photographer on must-have shots list", "Photography", "medium"),
    (3, "Settle advance payments to all vendors", "Finance", "critical"),
    (2, "Charge all phones/cameras; prepare day-of logistics bag", "Logistics", "medium"),
    (1, "Final guest count to caterer; confirm timings with all vendors", "Catering", "critical"),
    (
        1,
        "Ensure groom/bride attire, rings, and accessories are ready",
        "Attire & Makeup",
        "critical",
    ),
    (0, "DAY OF: Coordinator to manage vendor arrivals; wedding timeline", "Day-of", "critical"),
]

BIRTHDAY_TASKS: list[tuple[int, str, str, str]] = [
    (60, "Fix date, venue, and guest list", "Planning", "critical"),
    (45, "Book venue / home setup", "Venue", "critical"),
    (45, "Decide theme (character, color, etc.)", "Decor", "high"),
    (30, "Book photographer/videographer", "Photography", "high"),
    (30, "Order / plan custom cake", "Catering", "critical"),
    (21, "Send invitations (WhatsApp/printed)", "Invitations", "high"),
    (21, "Book entertainment (clown, magician, games facilitator)", "Entertainment", "medium"),
    (14, "Plan menu; finalize caterer or home-cook", "Catering", "high"),
    (14, "Order decor supplies (balloons, banners, tableware)", "Decor", "high"),
    (7, "Confirm RSVPs and final headcount", "Guests", "high"),
    (7, "Prepare return gifts / party favors", "Gifts", "medium"),
    (3, "Collect cake and decor supplies", "Logistics", "high"),
    (1, "Set up venue decorations (if not doing on the day)", "Decor", "high"),
    (1, "Confirm caterer arrival time", "Catering", "critical"),
    (0, "DAY OF: Early setup, guest reception, activities coordination", "Day-of", "critical"),
]

DIWALI_MELA_TASKS: list[tuple[int, str, str, str]] = [
    (90, "Form organizing committee and fix budget", "Planning", "critical"),
    (90, "Book venue / ground / common area with RWA/municipality", "Venue", "critical"),
    (75, "Apply for permissions, NOC, fire brigade clearance", "Permissions", "critical"),
    (
        60,
        "Shortlist food stall vendors; fix participation fees or revenue share",
        "Catering",
        "high",
    ),
    (60, "Plan lighting scheme; book electrician / lighting contractor", "Decor", "high"),
    (45, "Book cultural program performers (folk singers, dancers)", "Entertainment", "high"),
    (45, "Arrange sound system and generator", "Logistics", "critical"),
    (30, "Confirm all vendor stalls and layout plan", "Catering", "high"),
    (30, "Design and distribute invitations/banners in the society", "Invitations", "medium"),
    (21, "Follow up on permissions and clearances", "Permissions", "critical"),
    (14, "Final walkthrough of ground layout", "Venue", "high"),
    (7, "Test sound system and lighting", "Logistics", "high"),
    (7, "Confirm security/volunteers roster", "Safety", "high"),
    (3, "Purchase puja samagri and Lakshmi-Ganesh murtis", "Ceremonial", "medium"),
    (1, "Set up stalls, lighting, and decoration", "Decor", "critical"),
    (0, "DAY OF: Puja, program management, stall coordination, cleanup plan", "Day-of", "critical"),
]

COMMUNITY_TASKS: list[tuple[int, str, str, str]] = [
    (90, "Form committee; fix date and venue", "Planning", "critical"),
    (75, "Book venue; apply for permissions if outdoor", "Venue", "critical"),
    (60, "Finalize caterer; plan menu aligned with dietary requirements", "Catering", "high"),
    (60, "Plan entertainment and cultural program", "Entertainment", "high"),
    (45, "Arrange AV equipment and stage", "Logistics", "high"),
    (30, "Distribute invitations; collect RSVPs", "Invitations", "high"),
    (21, "Confirm all vendor bookings", "Finance", "critical"),
    (14, "Final headcount to caterer", "Catering", "critical"),
    (7, "Setup rehearsal and volunteer briefing", "Logistics", "medium"),
    (3, "Venue decorating", "Decor", "high"),
    (1, "Final checks with all vendors", "Finance", "high"),
    (0, "DAY OF: Setup, reception, program coordination", "Day-of", "critical"),
]

GENERIC_TASKS: list[tuple[int, str, str, str]] = [
    (90, "Finalize event concept and guest list", "Planning", "critical"),
    (60, "Book venue", "Venue", "critical"),
    (60, "Finalize caterer", "Catering", "high"),
    (45, "Send invitations", "Invitations", "high"),
    (30, "Confirm all vendor bookings", "Finance", "critical"),
    (14, "Final headcount to caterer", "Catering", "critical"),
    (7, "Setup preparations", "Logistics", "high"),
    (1, "Final vendor confirmations", "Finance", "critical"),
    (0, "DAY OF: Coordination and management", "Day-of", "critical"),
]

# Map event type to task list
EVENT_TASKS: dict[str, list[tuple[int, str, str, str]]] = {
    EventType.WEDDING: WEDDING_TASKS,
    EventType.BIRTHDAY: BIRTHDAY_TASKS,
    EventType.DIWALI_MELA: DIWALI_MELA_TASKS,
    EventType.EID_CELEBRATION: COMMUNITY_TASKS,
    EventType.NAVRATRI: DIWALI_MELA_TASKS,
    EventType.COLLEGE_FEST: COMMUNITY_TASKS,
    EventType.CORPORATE: GENERIC_TASKS,
    EventType.ANNIVERSARY: BIRTHDAY_TASKS,
    EventType.BABY_SHOWER: BIRTHDAY_TASKS,
    EventType.RWA_EVENT: COMMUNITY_TASKS,
    EventType.OTHER: GENERIC_TASKS,
}

# ─────────────────────────────────────────────────────────────
# Timeline generator
# ─────────────────────────────────────────────────────────────


def generate_timeline(req: EventRequest, today: date | None = None) -> Timeline:
    """
    Generate a backward-planned timeline from today to the event date.

    Args:
        req: The event request with event_date and event_type.
        today: Override today's date (for testing).

    Returns:
        Timeline with tasks, warnings, and urgency flags.
    """
    if today is None:
        today = date.today()

    days_until = (req.event_date - today).days
    warnings: list[str] = []
    is_compressed = False

    # Warn on past dates
    if days_until < 0:
        warnings.append(
            f"⚠️ Event date {req.event_date} is in the past ({abs(days_until)} days ago)."
        )
        days_until = 0

    # Compressed timeline warning
    if 0 < days_until < 30:
        is_compressed = True
        warnings.append(
            f"⚠️ Only {days_until} days until the event! Timeline is compressed. "
            "Focus immediately on CRITICAL tasks."
        )
    elif 30 <= days_until < 60:
        warnings.append(f"⚠️ Only {days_until} days until the event. Urgent booking required.")

    # Get base tasks for event type
    raw_tasks = EVENT_TASKS.get(req.event_type, GENERIC_TASKS)

    # Add outdoor-specific warnings
    if req.venue_type == VenueType.OUTDOOR:
        raw_tasks = list(raw_tasks) + [
            (
                45,
                "Apply for outdoor event permission / NOC from local authority",
                "Permissions",
                "critical",
            ),
            (14, "Arrange weather contingency (tent/tarpaulin for monsoon)", "Logistics", "high"),
            (7, "Check weather forecast; have indoor backup plan ready", "Logistics", "medium"),
        ]

    # Filter tasks that are still achievable (i.e., days_before >= days_until would be past)
    # For compressed timelines, include all tasks as urgent
    tasks: list[TimelineTask] = []
    for days_before, task_desc, category, priority in raw_tasks:
        scheduled_at = req.event_date - timedelta(days=days_before)
        is_past = scheduled_at < today

        # For past tasks in a compressed timeline, mark as urgent
        is_urgent = is_compressed and days_before > 0 and is_past

        label = "Day-of" if days_before == 0 else f"T-{days_before}"
        if is_past and not is_compressed:
            label += " (OVERDUE)"
            warnings.append(
                f"⚠️ Overdue: '{task_desc}' was due {(today - scheduled_at).days} days ago."
            )

        tasks.append(
            TimelineTask(
                days_before=days_before,
                label=label,
                task=task_desc,
                category=category,
                priority=priority,
                is_urgent=is_urgent or (days_before <= 3 and days_before >= 0),
                status="pending",
                notes=_get_task_notes(task_desc, req),
            )
        )

    # Limit overdue warnings to top 5
    warnings = warnings[:7]

    # Sort tasks: day-of first-ish? No — sort chronologically (largest days_before first)
    tasks.sort(key=lambda t: t.days_before, reverse=True)

    return Timeline(
        event_date=req.event_date,
        days_until_event=max(0, days_until),
        tasks=tasks,
        warnings=warnings,
        is_compressed=is_compressed,
    )


def _get_task_notes(task: str, req: EventRequest) -> str:
    """Return contextual notes for specific tasks."""
    notes: dict[str, str] = {
        "Book wedding venue": f"For {req.guest_count} guests in {req.city_tier.value} city. "
        "Check parking, AC/heating, and catering kitchen availability.",
        "Finalize caterer": f"Budget approximately ₹{800:.0f}–₹{1_500:.0f}/head. "
        f"Ensure {req.dietary.value} menu options.",
        "Apply for permissions": "Contact local municipal corporation or RWA office. NOC from fire department is mandatory for outdoor events > 200 guests.",
        "Sound system": "Ensure DG set (generator) backup for outdoor events.",
    }
    task_lower = task.lower()
    for key, note in notes.items():
        if key.lower() in task_lower:
            return note
    return ""
