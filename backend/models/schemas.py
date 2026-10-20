"""Pydantic models (schemas) for UtsavAI request/response validation."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────


class EventType(str, Enum):
    """Supported event categories."""

    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    DIWALI_MELA = "diwali_mela"
    EID_CELEBRATION = "eid_celebration"
    NAVRATRI = "navratri"
    COLLEGE_FEST = "college_fest"
    CORPORATE = "corporate"
    ANNIVERSARY = "anniversary"
    BABY_SHOWER = "baby_shower"
    RWA_EVENT = "rwa_event"
    OTHER = "other"


class CityTier(str, Enum):
    """City classification for cost calibration."""

    METRO = "metro"  # Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Kolkata
    TIER2 = "tier2"  # Jaipur, Pune, Ahmedabad, Lucknow, etc.
    TIER3 = "tier3"  # Smaller cities / rural


class DietaryType(str, Enum):
    """Dietary preference options."""

    VEG = "veg"
    JAIN = "jain"
    HALAL = "halal"
    NON_VEG = "non_veg"
    MIXED = "mixed"


class VenueType(str, Enum):
    """Venue setting."""

    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    HYBRID = "hybrid"


class PriorityArea(str, Enum):
    """Budget priority areas selected by the user."""

    FOOD = "food"
    DECOR = "decor"
    PHOTOGRAPHY = "photography"
    MUSIC = "music"
    VENUE = "venue"
    ENTERTAINMENT = "entertainment"
    INVITATIONS = "invitations"
    TRANSPORT = "transport"


class Season(str, Enum):
    """Indian event-season classification."""

    PEAK = "peak"  # Oct-Feb (wedding/festive season)
    SHOULDER = "shoulder"  # Mar-Apr, Sep
    OFF = "off"  # May-Aug (monsoon / summer)


# ─────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────


class EventRequest(BaseModel):
    """
    Complete event planning intake form.

    All string fields are stripped and length-limited to prevent
    oversized inputs or prompt-injection attempts.
    """

    # Core fields
    event_type: EventType
    event_date: date
    city: str = Field(..., min_length=2, max_length=100)
    city_tier: CityTier = CityTier.METRO
    guest_count: int = Field(..., ge=1, le=10_000)
    total_budget_inr: float = Field(..., ge=1_000, le=100_000_000)

    # Style & Culture
    theme: str = Field(default="", max_length=200)
    dietary: DietaryType = DietaryType.MIXED
    cultural_customs: str = Field(default="", max_length=500)
    religion_culture: str = Field(default="", max_length=100)
    venue_type: VenueType = VenueType.INDOOR

    # Priorities (ordered list, front = highest priority)
    priorities: list[PriorityArea] = Field(
        default_factory=lambda: [PriorityArea.FOOD, PriorityArea.VENUE, PriorityArea.DECOR]
    )

    # Additional notes (sanitized before LLM)
    special_requirements: str = Field(default="", max_length=1_000)

    @field_validator(
        "city",
        "theme",
        "cultural_customs",
        "religion_culture",
        "special_requirements",
        mode="before",
    )
    @classmethod
    def strip_and_sanitize_strings(cls, v: Any) -> str:
        """Strip whitespace; remove potential prompt-injection markers."""
        if not isinstance(v, str):
            return str(v) if v is not None else ""
        v = v.strip()
        # Remove common prompt-injection patterns
        dangerous = ["ignore previous", "system prompt", "forget", "jailbreak", "###", "---"]
        v_lower = v.lower()
        for pat in dangerous:
            if pat in v_lower:
                v = v.replace(pat, "").replace(pat.upper(), "").replace(pat.title(), "")
        return v[:1_000]  # Hard cap

    @field_validator("priorities", mode="before")
    @classmethod
    def deduplicate_priorities(cls, v: Any) -> list[PriorityArea]:
        """Ensure unique priorities, max 6."""
        if not isinstance(v, list):
            return [PriorityArea.FOOD, PriorityArea.VENUE, PriorityArea.DECOR]
        seen: set[str] = set()
        result = []
        for item in v[:6]:
            key = item if isinstance(item, str) else item.value
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    @model_validator(mode="after")
    def validate_budget_sanity(self) -> EventRequest:
        """Warn if budget is critically low (validation only; engine provides suggestions)."""
        per_head = self.total_budget_inr / self.guest_count
        if per_head < 100:  # ₹100/head absolute floor
            raise ValueError(
                f"Budget of ₹{self.total_budget_inr:,.0f} for {self.guest_count} guests "
                f"(₹{per_head:.0f}/head) is below the absolute minimum of ₹100/head. "
                "Please increase budget or reduce guest count."
            )
        return self


class ChatMessage(BaseModel):
    """A follow-up chat message for the assistant."""

    session_id: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., min_length=1, max_length=2_000)
    previous_plan_context: dict[str, Any] | None = None

    @field_validator("message", mode="before")
    @classmethod
    def sanitize_message(cls, v: Any) -> str:
        """Sanitize chat message."""
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 2_000:
            raise ValueError("message cannot exceed 2000 characters")
        dangerous = ["ignore previous instructions", "system:", "###system", "<|im_start|>"]
        v_lower = v.lower()
        for pat in dangerous:
            if pat in v_lower:
                v = v.replace(pat, "[filtered]")
        return v


# ─────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────


class BudgetLineItem(BaseModel):
    """A single budget allocation line."""

    category: str
    percentage: float
    amount_inr: float
    min_amount_inr: float
    notes: str = ""


class BudgetBreakdown(BaseModel):
    """Full deterministic budget breakdown."""

    total_inr: float
    per_head_inr: float
    contingency_inr: float
    allocations: list[BudgetLineItem]
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    season: Season
    city_tier: CityTier
    realistic_minimum_inr: float


class TimelineTask(BaseModel):
    """A single timeline task."""

    days_before: int  # Negative = days before event; 0 = day-of
    label: str  # e.g. "T-90"
    task: str
    category: str
    priority: str  # "critical" | "high" | "medium" | "low"
    is_urgent: bool = False
    status: str = "pending"  # pending | done
    notes: str = ""


class Timeline(BaseModel):
    """Backward-planned event timeline."""

    event_date: date
    days_until_event: int
    tasks: list[TimelineTask]
    warnings: list[str] = Field(default_factory=list)
    is_compressed: bool = False  # True when < 30 days to event


class VendorItem(BaseModel):
    """A vendor checklist item."""

    category: str
    vendor_type: str
    questions_to_ask: list[str]
    booking_lead_time_days: int
    estimated_cost_min_inr: float
    estimated_cost_max_inr: float
    notes: str = ""
    is_mandatory: bool = True


class VendorChecklist(BaseModel):
    """Complete vendor checklist."""

    items: list[VendorItem]
    total_categories: int


class AIPersonalization(BaseModel):
    """GenAI-generated personalization layer (or template fallback)."""

    theme_ideas: list[str]
    menu_suggestions: list[str]
    decor_ideas: list[str]
    invitation_wording: str
    games_activities: list[str]
    speech_toast: str
    is_ai_generated: bool  # False = template fallback
    provider_used: str = "fallback"


class SanityCheck(BaseModel):
    """Event sanity/conflict check results."""

    check_name: str
    status: str  # "ok" | "warning" | "error"
    message: str
    suggestion: str = ""


class EventPlan(BaseModel):
    """The complete event plan returned to the client."""

    session_id: str
    event_request: EventRequest
    budget: BudgetBreakdown
    timeline: Timeline
    vendor_checklist: VendorChecklist
    ai_personalization: AIPersonalization
    sanity_checks: list[SanityCheck]
    generated_at: str  # ISO datetime string


class ChatResponse(BaseModel):
    """Response from the chat assistant."""

    session_id: str
    reply: str
    updated_plan: EventPlan | None = None
    is_plan_updated: bool = False
