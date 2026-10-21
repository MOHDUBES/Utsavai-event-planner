"""
AI Personalization Service – provider-agnostic LLM wrapper for UtsavAI.

Architecture:
- Single batched structured-JSON call to LLM.
- In-memory LRU cache keyed by normalized request hash.
- Timeout + exponential backoff retry logic.
- Offline template fallback when no API key / provider is 'none'.
- Prompt injection defense via sanitized context injection.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from backend.models.schemas import AIPersonalization, EventRequest, EventType
from backend.utils import config

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Template fallback data (used when no API key is available)
# ─────────────────────────────────────────────────────────────

FALLBACK_THEMES: dict[str, list[str]] = {
    EventType.WEDDING: [
        "Royal Rajasthani Palace – marigold and royal blue palette with mirror work",
        "Bohemian Garden – fairy lights, macramé, and wildflower arrangements",
        "Minimalist Contemporary – ivory, gold, and geometric accents",
        "Bollywood Glamour – sequins, deep reds, and vintage cinema posters",
    ],
    EventType.BIRTHDAY: [
        "Enchanted Forest – fairy lights, greenery, and mushroom props",
        "Superheroes Assemble – DC/Marvel themed with cape stations",
        "Retro 90s Bollywood – VHS tapes, cassettes, and Amul butter ads",
        "Under the Sea – blue drapes, coral props, and mermaid tails",
    ],
    EventType.DIWALI_MELA: [
        "Traditional Mela – clay diyas, rangoli stations, and folk art stalls",
        "Luminous Diwali – LED lit trees, sparkling pathways, and lantern artistry",
        "Heritage Bazaar – antique-style stalls with kachori and jalebi vendors",
    ],
    EventType.EID_CELEBRATION: [
        "Arabian Nights – crescents, stars, lanterns, and deep jewel tones",
        "Garden of Paradise – white and gold with rose petal pathways",
    ],
    EventType.NAVRATRI: [
        "Amba Maa Pandal – traditional style with ghee lamp arrangements",
        "Modern Garba Night – LED dance floor, colorful chaniya cholis, and dhol beats",
    ],
    EventType.COLLEGE_FEST: [
        "Neon Future – UV lights, fluorescent themes, and futuristic installations",
        "Desi Street Food Festival – food trucks, mehendi, and cultural performances",
    ],
}

FALLBACK_MENUS: dict[str, dict[str, list[str]]] = {
    "wedding_veg": [
        "Welcome drinks: Aam Panna, Shikanji, Coconut Water",
        "Starters: Dahi Puri, Paneer Tikka, Aloo Tikki Chaat",
        "Main: Dal Makhani, Shahi Paneer, Jeera Rice, Butter Naan, Biryani (Veg)",
        "Desserts: Gulab Jamun, Rasmalai, Phirni, Kulfi Falooda",
        "Live stations: Pav Bhaji, Chaat, Dosa, Ice Cream",
    ],
    "wedding_non_veg": [
        "Welcome drinks: Aam Panna, Nimbu Pani, Kokum Sherbet",
        "Starters: Seekh Kebab, Chicken Tikka, Dahi Puri, Paneer Tikka",
        "Main: Chicken Biryani, Mutton Rogan Josh, Dal Tadka, Butter Naan, Raita",
        "Desserts: Gajar Halwa, Gulab Jamun, Kulfi Falooda, Rasmalai",
        "Live stations: Chaat, Kebab Grill, Dosa",
    ],
    "birthday_veg": [
        "Finger food: Mini Samosas, Veg Spring Rolls, Dahi Puri",
        "Main: Pizza (assorted), Pav Bhaji, Pasta",
        "Desserts: Custom Cake, Brownies, Milkshake station",
        "Juices: Mango, Watermelon, Orange",
    ],
    "birthday_non_veg": [
        "Finger food: Chicken Wings, Fish Fingers, Mini Burgers",
        "Main: Chicken Biryani, Butter Chicken, Naan",
        "Desserts: Custom Cake, Gulab Jamun, Ice Cream Bar",
    ],
    "community": [
        "Breakfast/Snacks: Poha, Jalebi, Chai",
        "Main course: Pulao, Dal, Sabzi, Roti, Raita",
        "Desserts: Kheer, Halwa",
        "Drinks: Chaas, Nimbu Pani",
    ],
}

FALLBACK_DECOR: dict[str, list[str]] = {
    EventType.WEDDING: [
        "Floral mandap with marigold and rose garlands – a timeless choice",
        "Entrance arch with fairy lights and hanging jasmine – fragrant and photogenic",
        "Table centerpieces: brass urli with floating candles and petals",
        "Backdrop: gold and ivory drapes with name monogram neon sign",
        "Mehendi area: swing decorated with roses and string lights",
    ],
    EventType.BIRTHDAY: [
        "Photo booth with themed props (crowns, mustaches, balloons)",
        "Balloon garland arch in theme colors at the entrance",
        "Table runner: confetti scattered on kraft paper",
        "Personalized banner: '[Name]'s Big Day' in neon or wood letters",
        "Dessert table with tiered cake stand and floral backdrop",
    ],
    EventType.DIWALI_MELA: [
        "100+ clay diyas arranged in a grand rangoli design at the entrance",
        "Paper lanterns strung across the entire venue",
        "Torana (marigold door hanging) on every stall entrance",
        "Traditional kolam/rangoli competition station for guests",
    ],
    "default": [
        "Floral centerpieces in season blooms",
        "String lights for a warm, festive ambiance",
        "Themed color palette carried across tablecloths and napkins",
        "Photo-worthy backdrop with the event name and date",
    ],
}

FALLBACK_GAMES: dict[str, list[str]] = {
    EventType.WEDDING: [
        "Ring-in-the-flour game (Antakshari variant with bride/groom trivia)",
        "Shoe-hiding game (Joota Chhupai) – groomsmen vs bridesmaids",
        "Photo scavenger hunt across the wedding venue",
        "Best advice for the couple: handwritten card collection",
        "Who knows the couple better? – Q&A game on the big screen",
    ],
    EventType.BIRTHDAY: [
        "Musical chairs with Bollywood hits",
        "Treasure hunt around the venue",
        "DIY craft station (decorate a tote bag / flower pot)",
        "Tambola/Housie – birthday edition with prizes",
        "Karaoke corner with a playlist of favorites",
    ],
    EventType.DIWALI_MELA: [
        "Rangoli making competition",
        "Diya decoration contest",
        "Antakshari – devotional and Bollywood songs",
        "Matka phod / lucky dip stall for children",
        "Traditional games: Tug of War, Lemon & Spoon, Sack Race",
    ],
    "default": [
        "Tambola/Housie with event-themed lucky board",
        "Photo booth with fun props",
        "Group quiz on general knowledge / Bollywood",
        "Musical chairs or freeze dance",
    ],
}

FALLBACK_SPEECHES: dict[str, str] = {
    EventType.WEDDING: (
        "Dear [Bride] and [Groom], today you don't just gain a partner — you gain a family, "
        "a home, and a thousand new memories waiting to be made. May your love be as enduring "
        "as the mountains, as warm as chai on a winter morning, and as full of laughter as every "
        "Bollywood wedding you ever dreamed about. Here's to a lifetime of adventures, of "
        "disagreements settled over biryani, and of love that only grows richer with time. "
        "From all of us — wishing you every happiness. Cheers! 🥂"
    ),
    EventType.BIRTHDAY: (
        "Happy Birthday, [Name]! Another year older, another year wiser — and another perfectly "
        "good excuse to eat cake without guilt! May this year bring you everything you have been "
        "working toward: the laughter that echoes, the friendships that matter, and the successes "
        "that make all the hard work worth it. We are so proud of who you are. Here's to many more "
        "celebrations! 🎂🎉"
    ),
    EventType.DIWALI_MELA: (
        "Shubh Deepawali to each and every one of you! Diwali is not just the festival of lights "
        "— it is the celebration of knowledge over ignorance, hope over despair, and community "
        "over isolation. As these diyas light up the night, may your homes be filled with warmth, "
        "your hearts with joy, and your year ahead with prosperity and good health. Let us celebrate "
        "together — this is what it means to be a community! 🪔✨"
    ),
    "default": (
        "Thank you all for being here to celebrate this special occasion. Your presence makes this "
        "event truly memorable. May the joy we share today stay with all of us long after this "
        "celebration ends. Here's to great memories and wonderful company! 🎉"
    ),
}

FALLBACK_INVITATIONS: dict[str, str] = {
    EventType.WEDDING: (
        "🌸 With joy in our hearts and blessings of the Almighty,\n"
        "[Family Name] cordially invite you to grace the wedding of\n\n"
        "✨ [BRIDE'S NAME] & [GROOM'S NAME] ✨\n\n"
        "📅 [Date] | 🕕 [Time onwards]\n"
        "📍 [Venue Name], [City]\n\n"
        "Your presence will make our celebration complete.\n"
        "RSVP by [Date]: [Contact Number]\n\n"
        "— With love, [Family Name]"
    ),
    EventType.BIRTHDAY: (
        "🎉 Come join the party! 🎉\n\n"
        "[Name] is turning [Age]!\n\n"
        "📅 [Date] | ⏰ [Time]\n"
        "📍 [Venue], [City]\n\n"
        "Fun, food, and lots of cake await!\n"
        "Please RSVP by [Date]: [Contact Number]\n\n"
        "— [Host Name]"
    ),
    EventType.DIWALI_MELA: (
        "🪔 Shubh Deepawali! 🪔\n\n"
        "Dear Neighbour,\n"
        "[Society/Colony Name] invites you to the Annual Diwali Mela!\n\n"
        "📅 [Date] | ⏰ [Time]\n"
        "📍 [Venue/Community Ground]\n\n"
        "Enjoy: Food Stalls • Cultural Programs • Rangoli Contest • Diyas • Fun & Festivities!\n\n"
        "Come one, come all — let's celebrate together!\n"
        "— [Organizing Committee]"
    ),
    "default": (
        "You are cordially invited to celebrate [Event Name]!\n\n"
        "📅 [Date] | ⏰ [Time]\n"
        "📍 [Venue], [City]\n\n"
        "RSVP: [Contact]\n\n"
        "— [Host Name]"
    ),
}


# ─────────────────────────────────────────────────────────────
# Cache (LRU, keyed by normalized request hash)
# ─────────────────────────────────────────────────────────────

_ai_cache: dict[str, AIPersonalization] = {}
_MAX_CACHE_SIZE = 128  # Will read from settings


def _make_cache_key(req: EventRequest) -> str:
    """
    Create a deterministic cache key from normalized request fields.
    Uses only creative-relevant fields to maximize cache hits.
    """
    key_data = {
        "event_type": req.event_type,
        "guest_count": round(req.guest_count / 50) * 50,  # Bucket guest count
        "city_tier": req.city_tier,
        "dietary": req.dietary,
        "theme": req.theme.lower().strip(),
        "cultural_customs": req.cultural_customs.lower().strip()[:100],
        "religion_culture": req.religion_culture.lower().strip(),
    }
    raw = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────
# LLM prompt builder
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are UtsavAI, a professional Indian event planning assistant.
You specialize in weddings, birthdays, and cultural events in India.
Your output must be structured, practical, and culturally appropriate.
You must respond ONLY with valid JSON matching the requested schema.
Do not include markdown fences, explanations, or any text outside the JSON object.
All suggestions should be India-specific, in INR context, and culturally sensitive."""


def _build_user_prompt(req: EventRequest) -> str:
    """
    Build a safe, sanitized prompt for the LLM.
    User inputs are already sanitized via Pydantic validators.
    """
    return f"""Generate personalized event planning ideas for the following event:

Event Type: {req.event_type.value}
Date: {req.event_date}
City Tier: {req.city_tier.value}
Guest Count: {req.guest_count}
Budget: ₹{req.total_budget_inr:,.0f}
Theme: {req.theme or "No specific theme"}
Dietary: {req.dietary.value}
Cultural/Religious Context: {req.religion_culture or req.cultural_customs or "General Indian"}
Special Requirements: {req.special_requirements or "None"}

Respond with a JSON object with EXACTLY these keys:
{{
  "theme_ideas": ["<4 unique, specific, India-appropriate theme ideas>"],
  "menu_suggestions": ["<5 menu items/courses appropriate for dietary preference>"],
  "decor_ideas": ["<5 specific decor ideas with product suggestions>"],
  "invitation_wording": "<A complete, warm invitation text in English with [PLACEHOLDER] for variable fields>",
  "games_activities": ["<5 fun activities suitable for the event type and guest demographics>"],
  "speech_toast": "<A heartfelt, culturally appropriate 100-150 word speech or toast>"
}}

Ensure all suggestions are:
1. Budget-appropriate for ₹{req.total_budget_inr:,.0f} total
2. Culturally sensitive and India-specific
3. Suitable for {req.dietary.value} dietary requirements
4. Practical and actionable"""


# ─────────────────────────────────────────────────────────────
# Provider implementations
# ─────────────────────────────────────────────────────────────


async def _call_gemini(prompt: str, system: str, settings: object) -> dict:
    """Call Google Gemini API using google-genai SDK."""
    try:
        from google import genai  # type: ignore[import]

        client = genai.Client(api_key=settings.gemini_api_key)

        full_prompt = f"{system}\n\n{prompt}"
        model_name = getattr(settings, "gemini_model", "gemini-3.8-flash")
        interaction = client.interactions.create(
            model=model_name,
            input=full_prompt,
            store=False,  # No need to retain
        )

        raw = interaction.output_text or ""
        # Strip any accidental markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)

    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
        raise


async def _call_openai(prompt: str, system: str, settings: object) -> dict:
    """Call OpenAI API."""
    try:
        import openai  # type: ignore[import]

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            timeout=settings.llm_timeout_seconds,
        )
        return json.loads(response.choices[0].message.content or "{}")
    except Exception as e:
        logger.warning(f"OpenAI call failed: {e}")
        raise


async def _call_anthropic(prompt: str, system: str, settings: object) -> dict:
    """Call Anthropic Claude API."""
    try:
        import anthropic  # type: ignore[import]

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        message = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text if message.content else "{}"
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Anthropic call failed: {e}")
        raise


# ─────────────────────────────────────────────────────────────
# Template fallback
# ─────────────────────────────────────────────────────────────


def _get_fallback(req: EventRequest) -> AIPersonalization:
    """Return template-based personalization without any LLM call."""
    event = req.event_type

    theme_ideas = FALLBACK_THEMES.get(
        event,
        FALLBACK_THEMES.get(
            EventType.BIRTHDAY,
            [
                "Festive Indian Traditional",
                "Modern Minimal with Floral Accents",
                "Bollywood Glamour",
                "Garden Party with Marigolds and Fairy Lights",
            ],
        ),
    )

    # Menu lookup
    menu_key = f"{event}_{'veg' if req.dietary.value in ('veg', 'jain') else 'non_veg'}"
    if event in {
        EventType.DIWALI_MELA,
        EventType.NAVRATRI,
        EventType.RWA_EVENT,
        EventType.EID_CELEBRATION,
        EventType.COLLEGE_FEST,
        EventType.CORPORATE,
    }:
        menu_key = "community"
    menu = FALLBACK_MENUS.get(menu_key, FALLBACK_MENUS["community"])

    decor = FALLBACK_DECOR.get(event, FALLBACK_DECOR["default"])
    games = FALLBACK_GAMES.get(event, FALLBACK_GAMES["default"])
    speech = FALLBACK_SPEECHES.get(event, FALLBACK_SPEECHES["default"])
    invite = FALLBACK_INVITATIONS.get(event, FALLBACK_INVITATIONS["default"])

    return AIPersonalization(
        theme_ideas=theme_ideas[:4],
        menu_suggestions=menu[:5],
        decor_ideas=decor[:5],
        invitation_wording=invite,
        games_activities=games[:5],
        speech_toast=speech,
        is_ai_generated=False,
        provider_used="template-fallback",
    )


# ─────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────


def _sanitize_output_text(text: str) -> str:
    """Remove HTML tags from LLM output."""
    import re

    return re.sub(r"<[^>]+>", "", str(text))


async def _dispatch_llm_call(
    provider: str, prompt: str, settings: config.Settings
) -> dict[str, Any]:
    """Dispatch prompt to configured LLM provider."""
    if provider == "gemini":
        return await _call_gemini(prompt, SYSTEM_PROMPT, settings)
    if provider == "openai":
        return await _call_openai(prompt, SYSTEM_PROMPT, settings)
    if provider == "anthropic":
        return await _call_anthropic(prompt, SYSTEM_PROMPT, settings)
    raise ValueError(f"Unknown provider: {provider}")


def _build_ai_personalization(data: dict[str, Any], provider: str) -> AIPersonalization:
    """Validate and parse raw LLM response dict into AIPersonalization model."""
    required_keys = {
        "theme_ideas",
        "menu_suggestions",
        "decor_ideas",
        "invitation_wording",
        "games_activities",
        "speech_toast",
    }
    if not required_keys.issubset(data.keys()):
        raise ValueError(f"LLM response missing keys: {required_keys - data.keys()}")

    return AIPersonalization(
        theme_ideas=[_sanitize_output_text(t) for t in data["theme_ideas"][:6]],
        menu_suggestions=[_sanitize_output_text(m) for m in data["menu_suggestions"][:6]],
        decor_ideas=[_sanitize_output_text(d) for d in data["decor_ideas"][:6]],
        invitation_wording=_sanitize_output_text(data["invitation_wording"]),
        games_activities=[_sanitize_output_text(g) for g in data["games_activities"][:6]],
        speech_toast=_sanitize_output_text(data["speech_toast"]),
        is_ai_generated=True,
        provider_used=provider,
    )


def _store_in_cache(cache_key: str, result: AIPersonalization, max_size: int) -> None:
    """Store result in LRU cache with eviction if capacity exceeded."""
    if len(_ai_cache) >= max_size and _ai_cache:
        oldest_key = next(iter(_ai_cache))
        del _ai_cache[oldest_key]
    _ai_cache[cache_key] = result


async def generate_personalization(req: EventRequest) -> AIPersonalization:
    """
    Generate AI personalization for an event.

    1. Check LRU cache.
    2. If cache miss, call configured LLM with retries.
    3. On any failure, return template fallback.
    4. Store successful result in cache.

    Args:
        req: Validated event request.

    Returns:
        AIPersonalization (AI-generated or template fallback).
    """
    settings = config.get_settings()
    provider = (settings.ai_provider or "").lower()

    # No provider configured → immediate fallback
    if not provider or provider == "none":
        logger.info("AI provider is 'none'; using template fallback.")
        return _get_fallback(req)

    cache_key = _make_cache_key(req)

    # Cache hit
    if cache_key in _ai_cache:
        logger.info(f"Cache hit for key {cache_key}")
        return _ai_cache[cache_key]

    prompt = _build_user_prompt(req)
    max_retries = 2
    backoff = 1.5
    max_cache = settings.llm_cache_size or _MAX_CACHE_SIZE

    for attempt in range(max_retries + 1):
        try:
            raw_data = await _dispatch_llm_call(provider, prompt, settings)
            result = _build_ai_personalization(raw_data, provider)
            _store_in_cache(cache_key, result, max_cache)

            logger.info(f"AI personalization generated via {provider} (attempt {attempt + 1})")
            return result

        except Exception as e:
            logger.warning(f"AI call attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff**attempt)
            else:
                logger.error("All AI retries exhausted. Using template fallback.")
                return _get_fallback(req)

    return _get_fallback(req)
