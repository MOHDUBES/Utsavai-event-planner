"""
Vendor Checklist Engine – category-wise vendor checklist for UtsavAI.

Provides questions-to-ask, booking lead times, and cost ranges
per vendor category, calibrated by event type and city tier.
"""

from __future__ import annotations

from backend.models.schemas import (
    CityTier,
    EventRequest,
    EventType,
    VendorChecklist,
    VendorItem,
    VenueType,
)

# ─────────────────────────────────────────────────────────────
# City tier cost multipliers for vendor estimates
# ─────────────────────────────────────────────────────────────

VENDOR_CITY_MULT: dict[str, float] = {
    CityTier.METRO: 1.50,
    CityTier.TIER2: 1.20,
    CityTier.TIER3: 1.00,
}

# ─────────────────────────────────────────────────────────────
# Vendor template definitions
# ─────────────────────────────────────────────────────────────


def _venue_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Venue",
        vendor_type="Banquet Hall / Hotel / Farmhouse / Lawn",
        questions_to_ask=[
            "What is the capacity (seated + cocktail)?",
            "Is in-house catering mandatory?",
            "Are there parking facilities?",
            "What is the cancellation/rescheduling policy?",
            "Is a generator/power backup included?",
            "What are the check-in/check-out times for setup?",
            "Are there separate rooms for bridal/family prep?",
            "Is AC/heating available in all halls?",
        ],
        booking_lead_time_days=90,
        estimated_cost_min_inr=round(25_000 * mult, -3),
        estimated_cost_max_inr=round(500_000 * mult, -3),
        notes="Prices vary wildly by location and type. Negotiate a package deal.",
        is_mandatory=True,
    )


def _caterer_vendor(req: EventRequest, mult: float) -> VendorItem:
    dietary_note = {
        "jain": "Ensure no onion/garlic/root vegetables in any preparation.",
        "halal": "All meat must be Halal-certified; request certificate.",
        "veg": "Strictly vegetarian kitchen with no cross-contamination.",
        "non_veg": "Include both veg and non-veg options.",
        "mixed": "Cater for both veg and non-veg guests; separate counters recommended.",
    }.get(req.dietary.value, "")

    return VendorItem(
        category="Catering",
        vendor_type="Catering Company / Home Cook / Hotel Kitchen",
        questions_to_ask=[
            f"Can you cater to {req.dietary.value} requirements?",
            "What is your per-plate rate for the proposed menu?",
            "Do you provide service staff (waiters)?",
            "Are crockery and cutlery included?",
            "Do you have a food license (FSSAI)?",
            "What is your backup plan if a dish runs out?",
            "Can we do a menu tasting before finalizing?",
            "What is your cancellation policy if guest count changes?",
        ],
        booking_lead_time_days=60,
        estimated_cost_min_inr=round(300 * req.guest_count * mult, -2),
        estimated_cost_max_inr=round(1_500 * req.guest_count * mult, -2),
        notes=dietary_note or "Always ask for FSSAI license.",
        is_mandatory=True,
    )


def _decorator_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Decoration",
        vendor_type="Event Decorator / Florist",
        questions_to_ask=[
            "Can you share a portfolio for similar events?",
            "Do you provide fresh flowers or artificial decorations?",
            "What is included in the quoted price (stage, entrance, seating)?",
            "How many hours before the event can you start setup?",
            "Do you handle cleanup/teardown after the event?",
            "Do you have a CAD/3D mockup of the decor layout?",
            "Can you work within a specific color palette?",
        ],
        booking_lead_time_days=45,
        estimated_cost_min_inr=round(15_000 * mult, -3),
        estimated_cost_max_inr=round(300_000 * mult, -3),
        notes="Fresh flowers cost significantly more in peak wedding season (Nov–Jan).",
        is_mandatory=True,
    )


def _photographer_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Photography & Videography",
        vendor_type="Photographer / Videographer",
        questions_to_ask=[
            "How many photographers/videographers are included?",
            "What is the turnaround time for edited photos?",
            "Do you provide a drone/aerial shoot?",
            "Is a highlight reel/wedding film included?",
            "What is your backup plan if you fall ill on event day?",
            "How many hours of coverage are included?",
            "Do you have backup equipment?",
            "What rights do we have over the photos (can we share online)?",
        ],
        booking_lead_time_days=90,
        estimated_cost_min_inr=round(20_000 * mult, -3),
        estimated_cost_max_inr=round(250_000 * mult, -3),
        notes="Book early; good photographers fill up 6+ months in advance.",
        is_mandatory=True,
    )


def _music_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Music & Entertainment",
        vendor_type="DJ / Live Band / Musician / Performer",
        questions_to_ask=[
            "What genres do you specialize in?",
            "Do you bring your own sound system?",
            "How many hours are covered in the quoted price?",
            "Can you accommodate special song requests?",
            "Are you familiar with the venue's noise restrictions?",
            "Do you have public performance licenses (if applicable)?",
            "Can you provide a sample playlist or demo video?",
        ],
        booking_lead_time_days=45,
        estimated_cost_min_inr=round(8_000 * mult, -3),
        estimated_cost_max_inr=round(150_000 * mult, -3),
        notes="Confirm noise ordinance curfew time with venue/local authority.",
        is_mandatory=False,
    )


def _pandit_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Pandit / Officiant / Religious Authority",
        vendor_type="Pandit / Maulvi / Priest / Granthi",
        questions_to_ask=[
            "Are you familiar with our specific regional customs?",
            "What rituals are included in the ceremony?",
            "How long will the ceremony take?",
            "Do you provide puja samagri or should we arrange it?",
            "Are you available for pre-event rituals (haldi, mehendi puja)?",
            "Can you explain the ceremony in both Hindi and English?",
        ],
        booking_lead_time_days=60,
        estimated_cost_min_inr=round(5_000 * mult, -2),
        estimated_cost_max_inr=round(50_000 * mult, -2),
        notes="Many pandits require auspicious muhurat confirmation first.",
        is_mandatory=True,
    )


def _makeup_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Makeup & Grooming",
        vendor_type="Bridal Makeup Artist / Grooming Artist",
        questions_to_ask=[
            "Can we see your bridal portfolio?",
            "Do you offer a trial session before the wedding day?",
            "How long does the bridal look take (plan time accordingly)?",
            "Do you use airbrush or traditional makeup?",
            "Are you available for pre-wedding events (mehendi, sangeet)?",
            "Do you travel to the venue or do we come to your studio?",
            "Is hairstyling included in the package?",
        ],
        booking_lead_time_days=90,
        estimated_cost_min_inr=round(15_000 * mult, -3),
        estimated_cost_max_inr=round(120_000 * mult, -3),
        notes="Best artists book out months in advance for peak season.",
        is_mandatory=True,
    )


def _invitations_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Invitations & Stationery",
        vendor_type="Printing Press / Digital Designer",
        questions_to_ask=[
            "What is the minimum order quantity?",
            "Do you offer digital invitation cards (WhatsApp)?",
            "What is the turnaround time for printing?",
            "Can you personalize each card with guest names?",
            "Do you include envelope and insert cards?",
            "Can you design in both English and Hindi/regional language?",
        ],
        booking_lead_time_days=30,
        estimated_cost_min_inr=round(5_000 * mult, -2),
        estimated_cost_max_inr=round(80_000 * mult, -2),
        notes="Budget digital invites for outstation guests; physical for close family.",
        is_mandatory=True,
    )


def _transport_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Transport & Logistics",
        vendor_type="Travel Agent / Bus Rental / Car Service",
        questions_to_ask=[
            "What vehicle types and capacities are available?",
            "Are fuel costs included in the quote?",
            "Is a driver included and are overnight trips covered?",
            "What is your policy for delays or breakdowns?",
            "Can you provide decorated baraat vehicles?",
        ],
        booking_lead_time_days=30,
        estimated_cost_min_inr=round(5_000 * mult, -2),
        estimated_cost_max_inr=round(100_000 * mult, -2),
        notes="For weddings, book baraat vehicles (horse carriage, classic car) 60+ days early.",
        is_mandatory=False,
    )


def _permissions_vendor(req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Permissions & NOC",
        vendor_type="Municipal Corporation / RWA / Fire Department",
        questions_to_ask=[
            "What permits are required for this type of event?",
            "How many days in advance must applications be submitted?",
            "Is a fire NOC required for the venue capacity?",
            "Are there noise restrictions or curfew timings?",
            "Is a police permission required (> 500 guests)?",
            "Are there crowd management/security requirements?",
        ],
        booking_lead_time_days=45,
        estimated_cost_min_inr=500,
        estimated_cost_max_inr=round(15_000 * mult, -2),
        notes="Start permission applications 6-8 weeks early. Police permission mandatory > 500 guests.",
        is_mandatory=req.venue_type == VenueType.OUTDOOR or req.guest_count > 200,
    )


def _cake_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="Cake & Sweets",
        vendor_type="Bakery / Mithai Shop",
        questions_to_ask=[
            "Can you make an eggless / vegan cake?",
            "Is delivery to the venue included?",
            "What is the lead time for a custom/tiered cake?",
            "Can you match our theme colors?",
            "Do you provide artificial flowers or edible decorations?",
        ],
        booking_lead_time_days=14,
        estimated_cost_min_inr=round(1_500 * mult, -2),
        estimated_cost_max_inr=round(30_000 * mult, -2),
        notes="Order 1kg per 25 guests as a rule of thumb.",
        is_mandatory=False,
    )


def _av_vendor(_req: EventRequest, mult: float) -> VendorItem:
    return VendorItem(
        category="AV & Stage Equipment",
        vendor_type="AV Rental Company / Stage Contractor",
        questions_to_ask=[
            "What PA system size is appropriate for the guest count?",
            "Is LED screen/projector included?",
            "Do you provide a sound engineer on the day?",
            "Is a generator (DG set) included for outdoor events?",
            "What is the setup and teardown time?",
        ],
        booking_lead_time_days=30,
        estimated_cost_min_inr=round(8_000 * mult, -2),
        estimated_cost_max_inr=round(150_000 * mult, -2),
        notes="For outdoor events, always arrange a DG set backup.",
        is_mandatory=True,
    )


# ─────────────────────────────────────────────────────────────
# Main checklist builder
# ─────────────────────────────────────────────────────────────


def _get_event_specific_vendors(req: EventRequest, mult: float) -> list[VendorItem]:
    """Return supplemental vendors based on specific event categories."""
    vendors: list[VendorItem] = []
    if req.event_type in {EventType.WEDDING, EventType.ANNIVERSARY}:
        vendors.extend(
            [
                _pandit_vendor(req, mult),
                _makeup_vendor(req, mult),
                _music_vendor(req, mult),
                _transport_vendor(req, mult),
            ]
        )
    elif req.event_type in {EventType.BIRTHDAY, EventType.BABY_SHOWER}:
        vendors.extend([_music_vendor(req, mult), _cake_vendor(req, mult)])
    elif req.event_type in {
        EventType.DIWALI_MELA,
        EventType.NAVRATRI,
        EventType.RWA_EVENT,
        EventType.EID_CELEBRATION,
    }:
        vendors.extend([_pandit_vendor(req, mult), _music_vendor(req, mult), _av_vendor(req, mult)])
        if req.guest_count > 200:
            vendors.append(_permissions_vendor(req, mult))
    elif req.event_type == EventType.COLLEGE_FEST:
        vendors.extend(
            [_music_vendor(req, mult), _av_vendor(req, mult), _permissions_vendor(req, mult)]
        )
    elif req.event_type == EventType.CORPORATE:
        vendors.extend([_av_vendor(req, mult), _transport_vendor(req, mult)])

    return vendors


def generate_vendor_checklist(req: EventRequest) -> VendorChecklist:
    """
    Build a vendor checklist tailored to the event type, city, and requirements.

    Args:
        req: Event request context.

    Returns:
        VendorChecklist with all relevant vendor categories.
    """
    mult = VENDOR_CITY_MULT[req.city_tier]
    items: list[VendorItem] = [
        _venue_vendor(req, mult),
        _caterer_vendor(req, mult),
        _decorator_vendor(req, mult),
        _photographer_vendor(req, mult),
        _invitations_vendor(req, mult),
    ]
    items.extend(_get_event_specific_vendors(req, mult))

    # Outdoor events always need permissions
    if req.venue_type == VenueType.OUTDOOR and not any(
        v.category == "Permissions & NOC" for v in items
    ):
        items.append(_permissions_vendor(req, mult))

    return VendorChecklist(
        items=items,
        total_categories=len(items),
    )
