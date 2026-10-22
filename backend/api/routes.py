"""
FastAPI router for event planning, chat, health, and demo endpoints.
Routes focus strictly on HTTP handling, status codes, and response serialization.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.data.demos import DEMO_SCENARIOS
from backend.models.schemas import (
    ChatMessage,
    ChatResponse,
    EventPlan,
    EventRequest,
)
from backend.services.ai_service import generate_personalization
from backend.services.budget_engine import calculate_budget
from backend.services.chat_service import process_chat_message
from backend.services.sanity_checks import run_sanity_checks
from backend.services.timeline_engine import generate_timeline
from backend.services.vendor_engine import generate_vendor_checklist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["events"])

# In-memory session store (replace with Redis in production)
_sessions: dict[str, EventPlan] = {}
_MAX_SESSIONS = 1_000


def _evict_oldest_session() -> None:
    """Evict oldest session if memory threshold exceeded."""
    if len(_sessions) >= _MAX_SESSIONS:
        oldest_key = next(iter(_sessions))
        del _sessions[oldest_key]


def _resolve_chat_plan(msg: ChatMessage) -> EventPlan | None:
    """Resolve plan from session store or client-provided context."""
    plan = _sessions.get(msg.session_id)
    if plan is not None or not msg.previous_plan_context:
        return plan

    plan_data = msg.previous_plan_context
    if isinstance(plan_data, dict):
        sid = plan_data.get("session_id")
        if sid and sid in _sessions:
            return _sessions[sid]
        try:
            return EventPlan.model_validate(plan_data)
        except Exception as e:
            logger.debug(f"Failed to parse previous_plan_context: {e}")
    return None


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
    """Main planning endpoint orchestrating deterministic engines and AI suggestions."""
    _ = request
    try:
        session_id = str(uuid.uuid4())
        budget = calculate_budget(event_req)
        timeline = generate_timeline(event_req)
        vendor_checklist = generate_vendor_checklist(event_req)
        sanity_checks = run_sanity_checks(event_req)
        ai_personalization = await generate_personalization(event_req)

        plan = EventPlan(
            session_id=session_id,
            generated_at=datetime.now(UTC).isoformat(),
            event_request=event_req,
            budget=budget,
            timeline=timeline,
            vendor_checklist=vendor_checklist,
            sanity_checks=sanity_checks,
            ai_personalization=ai_personalization,
        )

        _evict_oldest_session()
        _sessions[session_id] = plan
        return plan

    except Exception as e:
        logger.error(f"Failed to create event plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate event plan. Please check your inputs and try again.",
        ) from e


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the event planning assistant",
)
async def chat_with_assistant(request: Request, msg: ChatMessage) -> ChatResponse:
    """Follow-up chat endpoint for questions, cost cutting, and rescheduling."""
    _ = request
    try:
        plan = _resolve_chat_plan(msg)
        reply, updated_plan = await process_chat_message(msg, plan)

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


@router.get("/plan/{session_id}", response_model=EventPlan, summary="Retrieve a saved plan")
async def get_event_plan(session_id: str) -> EventPlan:
    """Retrieve an existing plan by its session ID."""
    plan = _sessions.get(session_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found or expired.")
    return plan


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, Any]:
    """Simple health check endpoint returning system status."""
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
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/demos", summary="Get demo event scenarios")
async def get_demo_scenarios() -> list[dict[str, Any]]:
    """Return pre-built demo event scenarios."""
    return DEMO_SCENARIOS
