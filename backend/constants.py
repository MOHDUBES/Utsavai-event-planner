"""
Centralized domain constants, multipliers, benchmarks, and mapping tables for UtsavAI.
"""

from __future__ import annotations

from backend.models.schemas import CityTier, EventType, PriorityArea, Season

# ─────────────────────────────────────────────────────────────
# Budget Allocation Percentages (sum to ~90%; 10% contingency)
# ─────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────
# Cost Benchmarks & Multipliers
# ─────────────────────────────────────────────────────────────

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

CITY_MULTIPLIERS: dict[str, float] = {
    CityTier.METRO: 1.45,
    CityTier.TIER2: 1.20,
    CityTier.TIER3: 1.00,
}

SEASON_MULTIPLIERS: dict[str, float] = {
    Season.PEAK: 1.20,
    Season.SHOULDER: 1.05,
    Season.OFF: 0.90,
}

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

# ─────────────────────────────────────────────────────────────
# Festival Calendar Clusters (month, day_start, day_end, name)
# ─────────────────────────────────────────────────────────────

FESTIVAL_CLUSTERS: list[tuple[int, int, int, str]] = [
    (10, 2, 6, "Navratri / Durga Puja"),
    (10, 12, 15, "Dussehra"),
    (10, 29, 31, "Diwali"),
    (11, 1, 3, "Diwali / Bhai Dooj"),
    (11, 24, 30, "Guru Nanak Jayanti weekend"),
    (12, 24, 26, "Christmas weekend"),
    (12, 31, 31, "New Year's Eve"),
    (1, 1, 1, "New Year's Day"),
    (1, 13, 15, "Makar Sankranti / Lohri / Pongal"),
    (1, 26, 26, "Republic Day"),
    (2, 14, 14, "Valentine's Day (high demand for venues)"),
    (3, 25, 29, "Holi / Spring festival"),
    (4, 9, 14, "Ram Navami / Baisakhi / Eid season"),
    (8, 15, 15, "Independence Day"),
    (8, 19, 26, "Janmashtami / Ganesh Chaturthi prep"),
    (9, 1, 15, "Ganesh Chaturthi season"),
]

# ─────────────────────────────────────────────────────────────
# Vendor Booking Lead Times (Days)
# ─────────────────────────────────────────────────────────────

DEFAULT_LEAD_TIMES: dict[str, int] = {
    "Venue": 90,
    "Catering": 60,
    "Decoration": 45,
    "Photography": 60,
    "Music": 30,
    "Priest": 45,
    "Makeup": 30,
    "Invitations": 21,
    "Transport": 14,
    "Cake": 10,
    "Permissions": 30,
    "AV": 21,
}
