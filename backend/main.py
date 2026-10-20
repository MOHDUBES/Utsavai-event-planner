"""
UtsavAI FastAPI application entry point.

Configures:
- CORS with restricted origins
- Security headers
- Rate limiting
- Static file serving for frontend
- Safe error handlers (no stack traces to client)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.api.routes import router
from backend.utils.config import get_settings

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Rate limiter
# ─────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

# ─────────────────────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="UtsavAI – Smart Celebration & Event Planner",
        description=(
            "An AI-powered event planning assistant for Indian weddings, birthdays, "
            "and community celebrations. India-first: INR currency, cultural awareness, "
            "and regional customs."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── Rate limiting ──────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=getattr(settings, "cors_origin_regex", None),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Accept"],
    )

    # ── Security headers middleware ────────────────────────────
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # CSP: allow inline scripts for our SPA, restrict external sources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response

    # ── Global error handlers ──────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Return clean, user-friendly error messages for validation errors."""
        messages: list[str] = []
        clean_errors: list[dict[str, Any]] = []
        for err in exc.errors():
            msg = str(err.get("msg", "Invalid value"))
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, ") :]
            loc = [str(part) for part in err.get("loc", []) if part != "body"]
            field_name = loc[-1] if loc else ""
            if field_name:
                field_label = field_name.replace("_", " ").title()
                messages.append(f"{field_label}: {msg}")
            else:
                messages.append(msg)
            clean_errors.append(
                {
                    "loc": [str(part) for part in err.get("loc", [])],
                    "msg": msg,
                    "type": str(err.get("type", "validation_error")),
                }
            )
        joined_msg = " | ".join(messages) if messages else "Invalid input data provided."
        return JSONResponse(
            status_code=422,
            content={"detail": joined_msg, "errors": clean_errors},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Return safe error messages — no stack traces."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."},
        )

    # ── API routes ─────────────────────────────────────────────
    app.include_router(router)

    # ── Static frontend (public/ or fallback to frontend/) ──────
    base_dir = Path(__file__).parent.parent
    frontend_dir = base_dir / "public"
    if not frontend_dir.exists():
        frontend_dir = base_dir / "frontend"

    if frontend_dir.exists():
        assets_dir = frontend_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        static_dir = frontend_dir / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_frontend():
            """Serve the main SPA index page."""
            return FileResponse(str(frontend_dir / "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            """Fallback route for SPA navigation or static file serving."""
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            index_path = frontend_dir / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            return JSONResponse(status_code=404, content={"detail": "Frontend not found"})

    logger.info(f"UtsavAI started — AI provider: {settings.ai_provider}")
    return app


app = create_app()
