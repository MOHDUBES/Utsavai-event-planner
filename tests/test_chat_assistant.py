"""
Tests for UtsavAI Chat Assistant.

Validates conversational follow-up interactions:
1. "cut decor cost by 20%" re-runs engines, updates budget and contingency, and explains changes.
2. "reschedule 2 weeks later" re-runs timeline, vendor, budget, and sanity check engines and explains changes.
3. Stateless plan context fallback.
4. Error handling and unknown session handling.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestChatAssistantEngineReRun:
    """Test engine re-runs triggered via the chat assistant."""

    async def test_cut_decor_cost_by_20_percent(self, client: AsyncClient, wedding_payload: dict):
        """
        'cut decor cost by 20%' must re-run the budget & sanity engines,
        update the plan's allocations, and return an explanation of what changed.
        """
        # 1. Generate baseline plan
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        assert plan_res.status_code == 200
        plan = plan_res.json()
        session_id = plan["session_id"]

        # Identify baseline decor line item
        baseline_decor = next(
            li for li in plan["budget"]["allocations"] if "decor" in li["category"].lower()
        )
        baseline_decor_amt = baseline_decor["amount_inr"]
        baseline_contingency = plan["budget"]["contingency_inr"]

        # 2. Issue chat request: "cut decor cost by 20%"
        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Can you cut decor cost by 20%?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()

        # 3. Assert plan was updated
        assert data["is_plan_updated"] is True
        assert data["updated_plan"] is not None
        updated_plan = data["updated_plan"]

        # 4. Verify decor was cut by 20%
        updated_decor = next(
            li for li in updated_plan["budget"]["allocations"] if "decor" in li["category"].lower()
        )
        expected_cut = round(baseline_decor_amt * 0.20, -1)
        expected_decor_amt = max(0.0, baseline_decor_amt - expected_cut)
        assert updated_decor["amount_inr"] == pytest.approx(expected_decor_amt, abs=15)
        assert updated_decor["amount_inr"] < baseline_decor_amt

        # 5. Verify contingency absorbed the savings
        assert updated_plan["budget"]["contingency_inr"] > baseline_contingency
        assert updated_plan["budget"]["contingency_inr"] == pytest.approx(
            baseline_contingency + (baseline_decor_amt - updated_decor["amount_inr"]), abs=15
        )

        # 6. Verify explanation of what changed
        reply = data["reply"]
        assert "Recalculated Budget" in reply or "cut by 20%" in reply
        assert "Decor" in reply
        assert "saved" in reply.lower() or "save" in reply.lower()
        assert "contingency" in reply.lower()
        assert "tips" in reply.lower() or "how to achieve" in reply.lower()

    async def test_reschedule_2_weeks_later(self, client: AsyncClient, wedding_payload: dict):
        """
        'reschedule 2 weeks later' must re-run timeline, budget, vendor checklist,
        and sanity engines and return an explanation of what changed.
        """
        # 1. Generate baseline plan
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        assert plan_res.status_code == 200
        plan = plan_res.json()
        session_id = plan["session_id"]

        orig_date_str = plan["event_request"]["event_date"]
        orig_date = date.fromisoformat(orig_date_str)
        orig_days_until = plan["timeline"]["days_until_event"]

        # 2. Issue chat request: "reschedule 2 weeks later"
        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Please reschedule 2 weeks later",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()

        # 3. Assert plan was updated
        assert data["is_plan_updated"] is True
        assert data["updated_plan"] is not None
        updated_plan = data["updated_plan"]

        # 4. Verify new date is exactly 14 days later
        new_date_str = updated_plan["event_request"]["event_date"]
        new_date = date.fromisoformat(new_date_str)
        expected_date = orig_date + timedelta(days=14)
        assert new_date == expected_date
        assert updated_plan["timeline"]["event_date"] == expected_date.isoformat()
        assert updated_plan["timeline"]["days_until_event"] == orig_days_until + 14

        # 5. Verify timeline and vendor checklist engines re-ran
        assert len(updated_plan["timeline"]["tasks"]) > 0
        assert len(updated_plan["vendor_checklist"]["items"]) > 0
        assert len(updated_plan["sanity_checks"]) > 0

        # 6. Verify explanation of what changed
        reply = data["reply"]
        assert "Rescheduled Successfully" in reply
        assert "Moved from" in reply
        assert orig_date_str in reply
        assert expected_date.isoformat() in reply
        assert "Timeline Engine" in reply
        assert "Vendor Engine" in reply

    async def test_stateless_chat_with_previous_plan_context(
        self, client: AsyncClient, wedding_payload: dict
    ):
        """
        If session_id is lost from memory or client is stateless,
        previous_plan_context provides the full plan for modification.
        """
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        plan = plan_res.json()

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": "ep_stateless_999",
                "message": "Cut decor cost by 20%",
                "previous_plan_context": plan,
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["is_plan_updated"] is True
        assert data["updated_plan"] is not None
        assert "saved" in data["reply"].lower()

    async def test_chat_timeline_query(self, client: AsyncClient, wedding_payload: dict):
        """Ask chat about timeline or schedule."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "When are my critical timeline tasks scheduled?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "Event Timeline" in data["reply"]
        assert "Critical Tasks" in data["reply"]

    async def test_chat_vendor_query(self, client: AsyncClient, wedding_payload: dict):
        """Ask chat about vendor bookings or photographers."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Which photographer and vendor should I book first?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "Key Vendors to Book" in data["reply"]

    async def test_chat_guest_count_change(self, client: AsyncClient, wedding_payload: dict):
        """Ask chat about increasing guest count."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "What happens if we invite 300 guests?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "Guest Count Change" in data["reply"]
        assert "catering impact" in data["reply"].lower()

    async def test_chat_guest_count_general(self, client: AsyncClient, wedding_payload: dict):
        """Ask chat general guest count change question without number."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "How do I change the guest count?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "submit a new plan" in data["reply"].lower()

    async def test_chat_reschedule_months(self, client: AsyncClient, wedding_payload: dict):
        """Reschedule event by months."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Can we postpone the event by 2 months?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert data["is_plan_updated"] is True
        assert "Rescheduled Successfully" in data["reply"]

    async def test_chat_general_ai_fallback(self, client: AsyncClient, wedding_payload: dict):
        """General non-engine question should return helpful conversational prompt."""
        plan_res = await client.post("/api/v1/plan", json=wedding_payload)
        session_id = plan_res.json()["session_id"]

        chat_res = await client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Hello, how are you today?",
            },
        )
        assert chat_res.status_code == 200
        data = chat_res.json()
        assert "reply" in data
        assert len(data["reply"]) > 10
