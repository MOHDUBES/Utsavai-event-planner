"""
Pre-configured demo scenarios for UtsavAI.
"""

from __future__ import annotations

from typing import Any

DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "wedding_delhi",
        "title": "💍 Wedding in Delhi",
        "description": "200 guests, ₹10 lakh budget, traditional Hindu ceremony",
        "payload": {
            "event_type": "wedding",
            "event_date": "2027-02-14",
            "city": "Delhi",
            "city_tier": "metro",
            "guest_count": 200,
            "total_budget_inr": 1_000_000,
            "theme": "Royal Rajasthani",
            "dietary": "veg",
            "cultural_customs": "North Indian Hindu wedding customs with haldi, mehendi, sangeet, and pheras",
            "religion_culture": "Hindu",
            "venue_type": "indoor",
            "priorities": ["food", "venue", "photography"],
            "special_requirements": "Separate arrangements for elderly guests; wheelchair accessible venue needed",
        },
    },
    {
        "id": "birthday_mumbai",
        "title": "🎂 Kid's Birthday in Mumbai",
        "description": "30 guests, ₹40,000 budget, superhero theme",
        "payload": {
            "event_type": "birthday",
            "event_date": "2026-12-15",
            "city": "Mumbai",
            "city_tier": "metro",
            "guest_count": 30,
            "total_budget_inr": 40_000,
            "theme": "Superheroes Assemble",
            "dietary": "veg",
            "cultural_customs": "Modern urban celebration",
            "religion_culture": "",
            "venue_type": "indoor",
            "priorities": ["decor", "entertainment", "food"],
            "special_requirements": "Nut-free menu; some guests are lactose intolerant",
        },
    },
    {
        "id": "diwali_mela_jaipur",
        "title": "🪔 Society Diwali Mela in Jaipur",
        "description": "500 guests, ₹1.5 lakh budget, community mela",
        "payload": {
            "event_type": "diwali_mela",
            "event_date": "2026-10-29",
            "city": "Jaipur",
            "city_tier": "tier2",
            "guest_count": 500,
            "total_budget_inr": 150_000,
            "theme": "Traditional Rajasthani Diwali",
            "dietary": "veg",
            "cultural_customs": "Traditional Lakshmi puja, rangoli competition, folk music",
            "religion_culture": "Hindu",
            "venue_type": "outdoor",
            "priorities": ["food", "decor", "entertainment"],
            "special_requirements": "Fire department NOC required for food stalls and fireworks",
        },
    },
]
