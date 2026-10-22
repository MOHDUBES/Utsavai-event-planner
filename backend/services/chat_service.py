"""
Conversational Assistant Engine – intent parsing and dynamic plan updates.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from backend.constants import SEASON_MULTIPLIERS
from backend.models.schemas import (
    BudgetLineItem,
    ChatMessage,
    EventPlan,
)
from backend.services.budget_engine import calculate_budget, detect_season
from backend.services.sanity_checks import run_sanity_checks
from backend.services.timeline_engine import generate_timeline
from backend.services.vendor_engine import generate_vendor_checklist

logger = logging.getLogger(__name__)

AREA_KEYWORD_MAP: dict[str, str] = {
    "decor": "Decor",
    "food": "Catering",
    "catering": "Catering",
    "photography": "Photography",
    "music": "Music",
    "venue": "Venue",
    "transport": "Transport",
}


def parse_cost_reduction_params(message: str) -> tuple[str, int] | None:
    """Extract area and percentage from cost reduction intent."""
    msg_lower = message.lower()
    if not any(word in msg_lower for word in ["cut", "reduce", "decrease", "lower", "save"]):
        return None
    for area in ["decor", "catering", "food", "photography", "music", "venue", "transport"]:
        if area in msg_lower:
            pct_match = re.search(r"(\d+)\s*%", message)
            reduction = int(pct_match.group(1)) if pct_match else 20
            return area, min(max(reduction, 5), 50)
    return None


def calculate_area_cut(
    allocations: list[BudgetLineItem],
    category_kw: str,
    reduction_pct: int,
    total_budget: float,
) -> tuple[list[BudgetLineItem], float, float, float]:
    """Calculate reduced line items, savings, old and new area totals."""
    savings = 0.0
    updated: list[BudgetLineItem] = []
    old_area_amt = 0.0
    new_area_amt = 0.0

    for li in allocations:
        if category_kw.lower() in li.category.lower():
            old_amt = li.amount_inr
            cut_amt = round(old_amt * (reduction_pct / 100), -1)
            new_amt = max(0.0, old_amt - cut_amt)
            savings += old_amt - new_amt
            old_area_amt += old_amt
            new_area_amt += new_amt
            new_pct = round((new_amt / total_budget) * 100, 1) if total_budget > 0 else 0.0
            updated.append(li.model_copy(update={"amount_inr": new_amt, "percentage": new_pct}))
        else:
            updated.append(li)

    return updated, savings, old_area_amt, new_area_amt


def build_cost_cut_tips(area: str) -> list[str]:
    """Return actionable savings recommendations by area."""
    if area.lower() == "decor":
        return [
            "- Use more artificial flowers and drapery (60% cheaper than exotic fresh florals)",
            "- Rent modular props and backdrops instead of custom builds",
            "- Use warm fairy lights and brass diyas instead of high-power chandelier fixtures",
        ]
    if area.lower() in ("food", "catering"):
        return [
            "- Switch to buffet from plated service (saves 20-30%)",
            "- Consolidate to 3-4 signature live stations",
            "- Feature local in-season ingredients",
        ]
    return []


async def handle_cost_reduction(
    plan: EventPlan, area: str, reduction_pct: int
) -> tuple[str, EventPlan | None]:
    """Re-run budget allocation and sanity validation for cost reduction."""
    category_kw = AREA_KEYWORD_MAP.get(area.lower(), area.title())
    matched = [li for li in plan.budget.allocations if category_kw.lower() in li.category.lower()]

    if not matched:
        categories_str = ", ".join(li.category for li in plan.budget.allocations)
        return (
            f"I couldn't find '{area}' in your budget. Current categories: {categories_str}",
            None,
        )

    updated_allocs, savings, old_amt, new_amt = calculate_area_cut(
        plan.budget.allocations, category_kw, reduction_pct, plan.budget.total_inr
    )
    new_contingency = plan.budget.contingency_inr + savings
    updated_budget = plan.budget.model_copy(
        update={"allocations": updated_allocs, "contingency_inr": new_contingency}
    )
    updated_sanity = run_sanity_checks(plan.event_request)
    updated_plan = plan.model_copy(
        update={"budget": updated_budget, "sanity_checks": updated_sanity}
    )

    reply_lines = [
        f"✂️ **Recalculated Budget: {area.title()} cut by {reduction_pct}%**\n",
        f"- **Previous {category_kw} allocation:** ₹{old_amt:,.0f}",
        f"- **New {category_kw} allocation:** ₹{new_amt:,.0f} (saved ₹{savings:,.0f})",
        f"- **Contingency Cushion:** Increased to ₹{new_contingency:,.0f} (+₹{savings:,.0f})",
        f"- **Engines Re-run:** Budget allocations updated and {len(updated_sanity)} sanity checks re-validated.",
    ]
    tips = build_cost_cut_tips(area)
    if tips:
        reply_lines.append(f"\n**Actionable tips to achieve this {area.title()} savings:**")
        reply_lines.extend(tips)

    return "\n".join(reply_lines), updated_plan


def parse_reschedule_delta(old_date: date, message: str) -> int:
    """Parse rescheduling delta in days from chat message."""
    msg = message.lower()
    weeks = re.search(r"(\d+)\s*week", msg)
    if weeks:
        return int(weeks.group(1)) * 7
    days = re.search(r"(\d+)\s*day", msg)
    if days:
        return int(days.group(1))
    months = re.search(r"(\d+)\s*month", msg)
    if months:
        return int(months.group(1)) * 30
    if "next week" in msg:
        return 7
    if "next month" in msg:
        return 30
    iso = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
    if iso:
        try:
            return (date.fromisoformat(iso.group(1)) - old_date).days
        except ValueError:
            return 14
    return 14


async def handle_reschedule(plan: EventPlan, message: str) -> tuple[str, EventPlan | None]:
    """Re-run timeline, budget, vendors, and sanity engines with the new date."""
    old_date = plan.event_request.event_date
    delta_days = parse_reschedule_delta(old_date, message)
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
    explanation = (
        f"📅 **Event Rescheduled Successfully!**\n\n"
        f"**What Changed:**\n"
        f"- **Event Date:** Moved from {old_date.isoformat()} to **{new_date.isoformat()}** ({'+' if delta_days >= 0 else ''}{delta_days} days)\n"
        f"- **Preparation Window:** {plan.timeline.days_until_event} days → **{new_timeline.days_until_event} days** until event\n"
        f"- **Season Shift:** {old_season.value.title()} ({SEASON_MULTIPLIERS[old_season]:.2f}x) → **{new_season.value.title()} ({SEASON_MULTIPLIERS[new_season]:.2f}x multiplier)**\n"
        f"- **Timeline Engine:** Recomputed {len(new_timeline.tasks)} tasks for the new target date\n"
        f"- **Vendor Engine:** Recalculated booking deadlines and lead-time alerts for {len(new_vendors.items)} vendor categories\n"
        f"- **Sanity Check Engine:** Re-evaluated calendar conflicts and season parameters"
    )
    return explanation, updated_plan


async def handle_guest_change(plan: EventPlan, message: str) -> tuple[str, EventPlan | None]:
    """Analyze guest count change and impact on per-head catering."""
    num_match = re.search(r"(\d+)\s*guests?", message.lower())
    if not num_match:
        return (
            f"Your current plan is for {plan.event_request.guest_count} guests. "
            f"To recalculate, specify a number: e.g., 'What if we have 250 guests?', or submit a new plan from the form.",
            None,
        )

    new_count = int(num_match.group(1))
    old_count = plan.event_request.guest_count
    change_pct = ((new_count - old_count) / old_count) * 100 if old_count > 0 else 0.0
    catering_impact = plan.budget.per_head_inr * (new_count - old_count)

    reply = (
        f"👥 **Guest Count Change: {old_count} → {new_count}**\n\n"
        f"- Change: {'+' if change_pct > 0 else ''}{change_pct:.1f}%\n"
        f"- Estimated catering impact: {'+' if catering_impact > 0 else ''}₹{abs(catering_impact):,.0f}\n\n"
        f"Note: Venue capacity and caterer minimums may also change. "
        f"To fully re-plan with {new_count} guests, generate a new plan from the form."
    )
    return reply, None


def format_static_inquiry_reply(plan: EventPlan, message_lower: str) -> str | None:
    """Provide structured static responses for budget, timeline, and vendor queries."""
    if any(w in message_lower for w in ["budget", "cost", "price", "afford", "expensive"]):
        b = plan.budget
        allocs = "\n".join(
            f"  - {li.category}: ₹{li.amount_inr:,.0f} ({li.percentage:.0f}%)"
            for li in b.allocations[:3]
        )
        warnings_str = (
            "\n\n⚠️ **Warnings:**\n" + "\n".join(f"- {w}" for w in b.warnings) if b.warnings else ""
        )
        return (
            f"💰 **Your Budget Summary:**\n\n"
            f"- **Total:** ₹{b.total_inr:,.0f}\n"
            f"- **Per head:** ₹{b.per_head_inr:,.0f}\n"
            f"- **Contingency (10%):** ₹{b.contingency_inr:,.0f}\n\n"
            f"**Top 3 allocations:**\n{allocs}{warnings_str}"
        )
    if any(w in message_lower for w in ["timeline", "when", "schedule", "tasks", "checklist"]):
        urgent = [t for t in plan.timeline.tasks if t.priority == "critical"][:5]
        return (
            f"📅 **Your Event Timeline:**\n\n"
            f"- Event Date: {plan.timeline.event_date}\n"
            f"- Days Until Event: {plan.timeline.days_until_event}\n\n"
            f"**Critical Tasks:**\n" + "\n".join(f"  - [{t.label}] {t.task}" for t in urgent)
        )
    if any(
        w in message_lower
        for w in ["vendor", "photographer", "caterer", "decorator", "dj", "pandit"]
    ):
        items = plan.vendor_checklist.items[:3]
        vendors = "\n\n".join(
            f"**{v.category}**\n  - Lead time: {v.booking_lead_time_days} days\n  - Cost range: ₹{v.estimated_cost_min_inr:,.0f} – ₹{v.estimated_cost_max_inr:,.0f}"
            for v in items
        )
        return f"📋 **Key Vendors to Book:**\n\n{vendors}"
    return None


def call_chat_ai(plan: EventPlan, user_message: str) -> str | None:
    """Invoke external AI provider for conversational response."""
    from backend.config import get_settings
    from backend.services.ai_service import SYSTEM_PROMPT

    settings = get_settings()
    if not settings.ai_provider or settings.ai_provider.lower() in ("none", ""):
        return None

    req = plan.event_request
    try:
        context_prompt = (
            f"The user has a plan for: {req.event_type.value} on {req.event_date} "
            f"in {req.city} for {req.guest_count} guests with budget ₹{req.total_budget_inr:,.0f}.\n\n"
            f"The user asks: {user_message}\n\n"
            "Respond conversationally in 2-4 sentences. Be helpful and specific. No JSON."
        )
        if settings.ai_provider.lower() == "gemini":
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            model_name = getattr(settings, "gemini_model", "gemini-3.8-flash")
            interaction = client.interactions.create(
                model=model_name,
                input=f"{SYSTEM_PROMPT}\n\n{context_prompt}",
                store=False,
            )
            return (
                interaction.output_text or "I couldn't generate a response. Please try rephrasing."
            )
    except Exception as e:
        logger.warning(f"Chat AI call failed: {e}")
    return None


async def process_chat_message(
    msg: ChatMessage,
    plan: EventPlan | None,
) -> tuple[str, EventPlan | None]:
    """Route chat message to appropriate intent handler or AI fallback."""
    if plan is None:
        return (
            "I don't have a plan on file for your session. "
            "Please generate a plan first using the planning form, then come back to chat!",
            None,
        )

    msg_lower = msg.message.lower()
    cost_params = parse_cost_reduction_params(msg.message)
    if cost_params:
        area, reduction = cost_params
        return await handle_cost_reduction(plan, area, reduction)

    if any(w in msg_lower for w in ["reschedule", "change date", "move to", "postpone"]):
        return await handle_reschedule(plan, msg.message)

    if "guest" in msg_lower:
        return await handle_guest_change(plan, msg.message)

    inquiry = format_static_inquiry_reply(plan, msg_lower)
    if inquiry is not None:
        return inquiry, None

    ai_reply = call_chat_ai(plan, msg.message)
    if ai_reply:
        return ai_reply, None

    req = plan.event_request
    return (
        f"I understand you're asking about your {req.event_type.value} event. "
        f"Could you be more specific? I can help with budget, timeline, vendors, or personalization. "
        f"For example, ask: 'How can I cut decor cost by 20%?' or 'Show me my critical timeline tasks.'",
        None,
    )
