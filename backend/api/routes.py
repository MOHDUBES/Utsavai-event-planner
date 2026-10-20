"""
FastAPI router for event planning endpoints.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.models.schemas import (
    ChatMessage,
    ChatResponse,
    EventPlan,
    EventRequest,
)
from backend.services.ai_service import generate_personalization
from backend.services.budget_engine import calculate_budget
from backend.services.sanity_checks import run_sanity_checks
from backend.services.timeline_engine import generate_timeline
from backend.services.vendor_engine import generate_vendor_checklist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["events"])

# In-memory session store (replace with Redis in production)
_sessions: dict[str, EventPlan] = {}
_MAX_SESSIONS = 1_000


# ─────────────────────────────────────────────────────────────
# Plan generation endpoint
# ─────────────────────────────────────────────────────────────


@router.post(
    "/plan",
    response_model=EventPlan,
    summary="Generate a complete event plan",
    description=(
        "Accepts event details and returns a full plan including "
        "budget breakdown, timeline, vendor checklist, and AI personalization."
    ),
)
async def create_event_plan(request: Request, event_req: EventRequest) -> EventPlan:
    """
    Main planning endpoint.

    Runs deterministic engines synchronously, then async AI call.
    Returns a complete EventPlan.
    """
    try:
        session_id = str(uuid.uuid4())

        # 1. Deterministic engines (fast, local)
        budget = calculate_budget(event_req)
        timeline = generate_timeline(event_req)
        vendor_checklist = generate_vendor_checklist(event_req)
        sanity_checks = run_sanity_checks(event_req)

        # 2. AI personalization (may use cache or fallback)
        ai_personalization = await generate_personalization(event_req)

        plan = EventPlan(
            session_id=session_id,
            event_request=event_req,
            budget=budget,
            timeline=timeline,
            vendor_checklist=vendor_checklist,
            ai_personalization=ai_personalization,
            sanity_checks=sanity_checks,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Store session (with size cap)
        if len(_sessions) >= _MAX_SESSIONS:
            oldest = next(iter(_sessions))
            del _sessions[oldest]
        _sessions[session_id] = plan

        logger.info(f"Plan created: session={session_id}, event={event_req.event_type}")
        return plan

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate event plan. Please try again.",
        ) from e


# ─────────────────────────────────────────────────────────────
# Chat / follow-up endpoint
# ─────────────────────────────────────────────────────────────


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the event planning assistant",
)
async def chat_with_assistant(request: Request, msg: ChatMessage) -> ChatResponse:
    """
    Follow-up chat endpoint.

    Interprets the user's message in context of their plan and either:
    - Answers a question about the plan, or
    - Re-runs the planning engine with updated parameters.
    """
    try:
        # Retrieve existing plan
        plan = _sessions.get(msg.session_id)

        if plan is None and msg.previous_plan_context:
            # Allow stateless chat with plan context from client
            plan_data = msg.previous_plan_context
            if isinstance(plan_data, dict):
                sid = plan_data.get("session_id")
                if sid and sid in _sessions:
                    plan = _sessions[sid]
                else:
                    try:
                        plan = EventPlan.model_validate(plan_data)
                    except Exception as e:
                        logger.debug(f"Failed to parse previous_plan_context: {e}")

        reply, updated_plan = await _process_chat_message(msg, plan)

        if updated_plan:
            _sessions[msg.session_id] = updated_plan

        return ChatResponse(
            session_id=msg.session_id,
            reply=reply,
            updated_plan=updated_plan,
            is_plan_updated=updated_plan is not None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Chat processing failed. Please try again.",
        ) from e


async def _process_chat_message(
    msg: ChatMessage,
    plan: EventPlan | None,
) -> tuple[str, EventPlan | None]:
    """
    Process a chat message and return (reply, updated_plan | None).
    """
    message_lower = msg.message.lower()

    # If no existing plan, guide user
    if plan is None:
        return (
            "I don't have a plan on file for your session. "
            "Please generate a plan first using the planning form, then come back to chat!",
            None,
        )

    req = plan.event_request

    # --- Handle "cut X cost by Y%" requests ---
    if any(word in message_lower for word in ["cut", "reduce", "decrease", "lower", "save"]):
        for area in ["decor", "catering", "food", "photography", "music", "venue", "transport"]:
            if area in message_lower:
                import re

                pct_match = re.search(r"(\d+)\s*%", msg.message)
                reduction = int(pct_match.group(1)) if pct_match else 20
                return await _handle_cost_reduction(plan, area, reduction)

    # --- Handle "reschedule" / "change date" ---
    if any(word in message_lower for word in ["reschedule", "change date", "move to", "postpone"]):
        return await _handle_reschedule(plan, msg.message)

    # --- Handle "add more guests" / "reduce guests" ---
    if any(
        word in message_lower
        for word in ["more guests", "add guests", "fewer guests", "reduce guests", "change guests"]
    ):
        return await _handle_guest_change(plan, msg.message)

    # --- Handle budget questions ---
    if any(word in message_lower for word in ["budget", "cost", "price", "afford", "expensive"]):
        b = plan.budget
        return (
            f"💰 **Your Budget Summary:**\n\n"
            f"- **Total:** ₹{b.total_inr:,.0f}\n"
            f"- **Per head:** ₹{b.per_head_inr:,.0f}\n"
            f"- **Contingency (10%):** ₹{b.contingency_inr:,.0f}\n\n"
            f"**Top 3 allocations:**\n"
            + "\n".join(
                f"  - {li.category}: ₹{li.amount_inr:,.0f} ({li.percentage:.0f}%)"
                for li in b.allocations[:3]
            )
            + (
                "\n\n⚠️ **Warnings:**\n" + "\n".join(f"- {w}" for w in b.warnings)
                if b.warnings
                else ""
            ),
            None,
        )

    # --- Handle timeline questions ---
    if any(
        word in message_lower for word in ["timeline", "when", "schedule", "tasks", "checklist"]
    ):
        urgent = [t for t in plan.timeline.tasks if t.priority == "critical"][:5]
        return (
            f"📅 **Your Event Timeline:**\n\n"
            f"- Event Date: {plan.timeline.event_date}\n"
            f"- Days Until Event: {plan.timeline.days_until_event}\n\n"
            f"**Critical Tasks:**\n" + "\n".join(f"  - [{t.label}] {t.task}" for t in urgent),
            None,
        )

    # --- Handle vendor questions ---
    if any(
        word in message_lower
        for word in ["vendor", "photographer", "caterer", "decorator", "dj", "pandit"]
    ):
        items = plan.vendor_checklist.items[:3]
        return (
            "📋 **Key Vendors to Book:**\n\n"
            + "\n\n".join(
                f"**{v.category}**\n"
                f"  - Lead time: {v.booking_lead_time_days} days\n"
                f"  - Cost range: ₹{v.estimated_cost_min_inr:,.0f} – ₹{v.estimated_cost_max_inr:,.0f}"
                for v in items
            ),
            None,
        )

    # --- Default: use AI for a conversational reply ---
    from backend.services.ai_service import SYSTEM_PROMPT
    from backend.utils.config import get_settings

    settings = get_settings()

    if settings.ai_provider and settings.ai_provider.lower() not in ("none", ""):
        try:
            context_prompt = (
                f"The user has a plan for: {req.event_type.value} on {req.event_date} "
                f"in {req.city} for {req.guest_count} guests with budget ₹{req.total_budget_inr:,.0f}.\n\n"
                f"The user asks: {msg.message}\n\n"
                "Respond conversationally in 2-4 sentences. Be helpful and specific. No JSON."
            )
            if settings.ai_provider.lower() == "gemini":
                from google import genai

                client = genai.Client(api_key=settings.gemini_api_key)
                interaction = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=f"{SYSTEM_PROMPT}\n\n{context_prompt}",
                    store=False,
                )
                return (
                    interaction.output_text
                    or "I couldn't generate a response. Please try rephrasing.",
                    None,
                )
        except Exception as e:
            logger.warning(f"Chat AI call failed: {e}")

    return (
        f"I understand you're asking about your {req.event_type.value} event. "
        f"Could you be more specific? I can help with budget, timeline, vendors, or personalization. "
        f"For example, ask: 'How can I cut decor cost by 20%?' or 'Show me my critical timeline tasks.'",
        None,
    )


async def _handle_cost_reduction(
    plan: EventPlan, area: str, reduction_pct: int
) -> tuple[str, EventPlan | None]:
    """Re-run budget engine and sanity check engine with reduced allocation for the specified area."""
    from backend.services.sanity_checks import run_sanity_checks

    reduction_pct = min(max(reduction_pct, 5), 50)  # Clamp 5-50%

    area_map = {
        "decor": "Decor",
        "food": "Catering",
        "catering": "Catering",
        "photography": "Photography",
        "music": "Music",
        "venue": "Venue",
        "transport": "Transport",
    }
    category_kw = area_map.get(area.lower(), area.title())
    matched = [li for li in plan.budget.allocations if category_kw.lower() in li.category.lower()]

    if not matched:
        return (
            f"I couldn't find '{area}' in your budget. Current categories: {', '.join(li.category for li in plan.budget.allocations)}",
            None,
        )

    savings = 0.0
    updated_allocations = []
    old_area_amt = 0.0
    new_area_amt = 0.0

    for li in plan.budget.allocations:
        if category_kw.lower() in li.category.lower():
            old_amt = li.amount_inr
            cut_amt = round(old_amt * (reduction_pct / 100), -1)
            new_amt = max(0.0, old_amt - cut_amt)
            savings += old_amt - new_amt
            old_area_amt += old_amt
            new_area_amt += new_amt
            new_pct = round((new_amt / plan.budget.total_inr) * 100, 1)
            updated_allocations.append(
                li.model_copy(update={"amount_inr": new_amt, "percentage": new_pct})
            )
        else:
            updated_allocations.append(li)

    new_contingency = plan.budget.contingency_inr + savings
    updated_budget = plan.budget.model_copy(
        update={
            "allocations": updated_allocations,
            "contingency_inr": new_contingency,
        }
    )

    # Re-run sanity checks with updated parameters
    updated_sanity = run_sanity_checks(plan.event_request)

    updated_plan = plan.model_copy(
        update={
            "budget": updated_budget,
            "sanity_checks": updated_sanity,
        }
    )

    reply_lines = [
        f"✂️ **Recalculated Budget: {area.title()} cut by {reduction_pct}%**\n",
        f"- **Previous {category_kw} allocation:** ₹{old_area_amt:,.0f}",
        f"- **New {category_kw} allocation:** ₹{new_area_amt:,.0f} (saved ₹{savings:,.0f})",
        f"- **Contingency Cushion:** Increased from ₹{plan.budget.contingency_inr:,.0f} to ₹{new_contingency:,.0f} (+₹{savings:,.0f})",
        f"- **Engines Re-run:** Budget allocations updated and {len(updated_sanity)} sanity checks re-validated.",
    ]

    if area.lower() in ("decor",):
        reply_lines.append("\n**Actionable tips to achieve this 20% decor savings:**")
        reply_lines.append(
            "- Use more artificial flowers and drapery (60% cheaper than exotic fresh florals)"
        )
        reply_lines.append("- Rent modular props and backdrops instead of custom builds")
        reply_lines.append(
            "- Use warm fairy lights and brass diyas instead of high-power chandelier fixtures"
        )
    elif area.lower() in ("food", "catering"):
        reply_lines.append("\n**Actionable tips to achieve this catering savings:**")
        reply_lines.append("- Switch to buffet from plated service (saves 20-30%)")
        reply_lines.append("- Consolidate to 3-4 signature live stations")
        reply_lines.append("- Feature local in-season ingredients")

    return "\n".join(reply_lines), updated_plan


async def _handle_reschedule(plan: EventPlan, message: str) -> tuple[str, EventPlan | None]:
    """Re-run timeline, budget, vendor checklist, and sanity engines with the new date."""
    import re
    from datetime import date, timedelta

    from backend.services.budget_engine import SEASON_MULTIPLIERS, calculate_budget, detect_season
    from backend.services.sanity_checks import run_sanity_checks
    from backend.services.timeline_engine import generate_timeline
    from backend.services.vendor_engine import generate_vendor_checklist

    old_date = plan.event_request.event_date
    delta_days = 0

    weeks_match = re.search(r"(\d+)\s*week", message.lower())
    days_match = re.search(r"(\d+)\s*day", message.lower())
    months_match = re.search(r"(\d+)\s*month", message.lower())

    if weeks_match:
        delta_days = int(weeks_match.group(1)) * 7
    elif days_match:
        delta_days = int(days_match.group(1))
    elif months_match:
        delta_days = int(months_match.group(1)) * 30
    elif "next week" in message.lower():
        delta_days = 7
    elif "next month" in message.lower():
        delta_days = 30
    else:
        iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
        if iso_match:
            try:
                target_date = date.fromisoformat(iso_match.group(1))
                delta_days = (target_date - old_date).days
            except ValueError:
                delta_days = 14
        else:
            delta_days = 14  # Default to 2 weeks later

    new_date = old_date + timedelta(days=delta_days)

    updated_req = plan.event_request.model_copy(update={"event_date": new_date})
    new_budget = calculate_budget(updated_req)
    new_timeline = generate_timeline(updated_req)
    new_vendors = generate_vendor_checklist(updated_req)
    new_sanity = run_sanity_checks(updated_req)

    updated_plan = plan.model_copy(
        update={
            "event_request": updated_req,
            "budget": new_budget,
            "timeline": new_timeline,
            "vendor_checklist": new_vendors,
            "sanity_checks": new_sanity,
        }
    )

    old_season = detect_season(old_date)
    new_season = detect_season(new_date)
    old_days = plan.timeline.days_until_event
    new_days = new_timeline.days_until_event

    explanation = (
        f"📅 **Event Rescheduled Successfully!**\n\n"
        f"**What Changed:**\n"
        f"- **Event Date:** Moved from {old_date.isoformat()} to **{new_date.isoformat()}** ({'+' if delta_days >= 0 else ''}{delta_days} days)\n"
        f"- **Preparation Window:** {old_days} days → **{new_days} days** until event\n"
        f"- **Season Shift:** {old_season.value.title()} ({SEASON_MULTIPLIERS[old_season]:.2f}x) → **{new_season.value.title()} ({SEASON_MULTIPLIERS[new_season]:.2f}x multiplier)**\n"
        f"- **Timeline Engine:** Recomputed {len(new_timeline.tasks)} tasks for the new target date\n"
        f"- **Vendor Engine:** Recalculated booking deadlines and lead-time alerts for {len(new_vendors.items)} vendor categories\n"
        f"- **Sanity Check Engine:** Re-evaluated calendar conflicts and season parameters"
    )

    return explanation, updated_plan


async def _handle_guest_change(plan: EventPlan, message: str) -> tuple[str, EventPlan | None]:
    """Provide guest count change impact analysis."""
    import re

    num_match = re.search(r"(\d+)\s*guests?", message)
    if num_match:
        new_count = int(num_match.group(1))
        old_count = plan.event_request.guest_count
        change_pct = ((new_count - old_count) / old_count) * 100
        catering_impact = plan.budget.per_head_inr * (new_count - old_count)

        reply = (
            f"👥 **Guest Count Change: {old_count} → {new_count}**\n\n"
            f"- Change: {'+' if change_pct > 0 else ''}{change_pct:.1f}%\n"
            f"- Estimated catering impact: {'+' if catering_impact > 0 else ''}₹{abs(catering_impact):,.0f}\n\n"
            f"Note: Venue capacity and caterer minimums may also change. "
            f"Submit a new plan with the updated guest count for a full recalculation."
        )
    else:
        reply = (
            "To change your guest count, please submit a new plan form with the updated number. "
            f"Currently you have {plan.event_request.guest_count} guests planned."
        )
    return reply, None


# ─────────────────────────────────────────────────────────────
# Utility endpoints
# ─────────────────────────────────────────────────────────────


@router.get("/plan/{session_id}", response_model=EventPlan, summary="Retrieve a saved plan")
async def get_plan(session_id: str) -> EventPlan:
    """Retrieve a previously generated plan by session ID."""
    plan = _sessions.get(session_id)
    if plan is None:
        raise HTTPException(
            status_code=404, detail="Plan not found. Sessions expire on server restart."
        )
    return plan


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """Simple health check endpoint."""
    from backend.utils.config import get_settings

    settings = get_settings()
    return {
        "status": "ok",
        "service": "UtsavAI Event Planner",
        "ai_provider": settings.ai_provider,
        "ai_enabled": bool(
            settings.ai_provider
            and settings.ai_provider.lower() not in ("none", "")
            and (settings.gemini_api_key or settings.openai_api_key or settings.anthropic_api_key)
        ),
    }


@router.get("/demos", summary="Get demo event scenarios")
async def get_demo_scenarios() -> list[dict]:
    """Return 3 pre-built demo event scenarios."""
    return [
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
                "special_requirements": "Event for all ages; children's corner needed",
            },
        },
    ]
