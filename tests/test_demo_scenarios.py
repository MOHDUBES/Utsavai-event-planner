"""
Tests to verify the 3 required UtsavAI demo scenarios:
1. Wedding in Delhi (200 guests, Rs 10L)
2. Kid's Birthday in Mumbai (30 guests, Rs 40k)
3. Society Diwali Mela in Jaipur (500 guests, Rs 1.5L)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDemoScenarios:
    """Verifies that the demo scenarios endpoint exists and all 3 produce working plans."""

    async def test_get_demos_list(self, client: AsyncClient):
        """GET /api/v1/demos returns exactly the 3 required demo scenarios."""
        res = await client.get("/api/v1/demos")
        assert res.status_code == 200
        demos = res.json()
        assert len(demos) == 3

        ids = [d["id"] for d in demos]
        assert "wedding_delhi" in ids
        assert "birthday_mumbai" in ids
        assert "diwali_mela_jaipur" in ids

    async def test_demo_1_wedding_in_delhi(self, client: AsyncClient):
        """
        Demo 1: Wedding in Delhi (200 guests, Rs 10L).
        Verifies complete budget breakdown, timeline, vendors, and sanity checks.
        """
        res = await client.get("/api/v1/demos")
        demos = res.json()
        wedding_demo = next(d for d in demos if d["id"] == "wedding_delhi")
        payload = wedding_demo["payload"]

        assert payload["guest_count"] == 200
        assert payload["total_budget_inr"] == 1_000_000
        assert payload["city"] == "Delhi"

        plan_res = await client.post("/api/v1/plan", json=payload)
        assert plan_res.status_code == 200
        plan = plan_res.json()

        # Validate budget
        b = plan["budget"]
        assert b["total_inr"] == 1_000_000
        assert b["per_head_inr"] == 5_000.0
        assert b["contingency_inr"] == 100_000.0  # 10%
        assert len(b["allocations"]) >= 6

        # Validate timeline
        t = plan["timeline"]
        assert len(t["tasks"]) >= 5
        assert t["days_until_event"] > 0

        # Validate vendor checklist
        v = plan["vendor_checklist"]
        assert len(v["items"]) >= 5
        categories = [item["category"] for item in v["items"]]
        assert "Venue" in categories
        assert "Catering" in categories

        # Validate sanity checks
        assert len(plan["sanity_checks"]) > 0

    async def test_demo_2_kids_birthday(self, client: AsyncClient):
        """
        Demo 2: Kid's Birthday (30 guests, Rs 40k).
        Verifies cake, games/entertainment, and tight budget handling.
        """
        res = await client.get("/api/v1/demos")
        demos = res.json()
        bday_demo = next(d for d in demos if d["id"] == "birthday_mumbai")
        payload = bday_demo["payload"]

        assert payload["guest_count"] == 30
        assert payload["total_budget_inr"] == 40_000
        assert payload["city"] == "Mumbai"

        plan_res = await client.post("/api/v1/plan", json=payload)
        assert plan_res.status_code == 200
        plan = plan_res.json()

        # Validate budget
        b = plan["budget"]
        assert b["total_inr"] == 40_000
        assert b["per_head_inr"] == pytest.approx(1333.33, rel=1e-2)
        assert b["contingency_inr"] == 4_000.0  # 10%

        # Birthday specific categories
        categories = [item["category"] for item in b["allocations"]]
        assert any("Cake" in c for c in categories)

        # Timeline
        assert len(plan["timeline"]["tasks"]) >= 4

        # Vendors
        vendor_cats = [item["category"] for item in plan["vendor_checklist"]["items"]]
        assert any("Cake" in c for c in vendor_cats)

    async def test_demo_3_society_diwali_mela(self, client: AsyncClient):
        """
        Demo 3: Society Diwali Mela (500 guests, Rs 1.5L).
        Verifies outdoor community festival handling, NOC/police permissions,
        and high-volume catering/lighting.
        """
        res = await client.get("/api/v1/demos")
        demos = res.json()
        diwali_demo = next(d for d in demos if d["id"] == "diwali_mela_jaipur")
        payload = diwali_demo["payload"]

        assert payload["guest_count"] == 500
        assert payload["total_budget_inr"] == 150_000
        assert payload["city"] == "Jaipur"
        assert payload["venue_type"] == "outdoor"

        plan_res = await client.post("/api/v1/plan", json=payload)
        assert plan_res.status_code == 200
        plan = plan_res.json()

        # Validate budget
        b = plan["budget"]
        assert b["total_inr"] == 150_000
        assert b["per_head_inr"] == 300.0
        assert b["contingency_inr"] == 15_000.0  # 10%

        # Outdoor festival specific tasks and vendors
        timeline_tasks = [t["task"].lower() for t in plan["timeline"]["tasks"]]
        assert any("permission" in t or "noc" in t or "license" in t for t in timeline_tasks)

        vendor_cats = [v["category"] for v in plan["vendor_checklist"]["items"]]
        assert any("Permission" in v or "NOC" in v for v in vendor_cats)
