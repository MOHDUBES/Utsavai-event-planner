"""
Tests for frontend static files and PWA assets:
1. index.html contains required viewport meta with viewport-fit=cover
2. index.html contains manifest link and lang attribute
3. All local static assets referenced in index.html and manifest exist on disk (no 404s/broken paths)
4. FastApi serves index.html and manifest.webmanifest with 200 OK
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from httpx import AsyncClient

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


class TestFrontendStatic:
    """Verifies static files, HTML semantics, PWA manifests, and referenced assets."""

    def test_index_html_viewport_meta(self) -> None:
        """index.html must have <meta name="viewport" content="...viewport-fit=cover">."""
        index_path = PUBLIC_DIR / "index.html"
        assert index_path.exists(), "public/index.html not found"

        content = index_path.read_text(encoding="utf-8")
        assert 'name="viewport"' in content, "Missing viewport meta tag"
        assert "viewport-fit=cover" in content, (
            "Viewport meta must contain viewport-fit=cover for notch devices"
        )
        assert "width=device-width" in content, "Viewport meta must specify width=device-width"

    def test_index_html_lang_and_manifest(self) -> None:
        """index.html must specify lang attribute and link to manifest.webmanifest."""
        index_path = PUBLIC_DIR / "index.html"
        content = index_path.read_text(encoding="utf-8")

        # HTML lang attribute
        assert re.search(r'<html\s+[^>]*lang=["\'][a-zA-Z\-]+["\']', content), (
            "index.html missing lang attribute on <html>"
        )

        # Manifest link
        assert re.search(
            r'<link\s+[^>]*rel=["\']manifest["\'][^>]*href=["\'][^"\']+manifest\.webmanifest["\']',
            content,
        ), "index.html missing link to manifest.webmanifest"

    def test_all_referenced_local_assets_exist_on_disk(self) -> None:
        """All local assets (css, js, svg, png) referenced in index.html must exist on disk."""
        index_path = PUBLIC_DIR / "index.html"
        content = index_path.read_text(encoding="utf-8")

        # Extract href="..." and src="..." and use href="..."
        patterns = [
            r'href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+)["\']',
        ]

        referenced_urls: set[str] = set()
        for pat in patterns:
            for match in re.findall(pat, content):
                # Filter out external links, anchors, data urls, api endpoints, and mailto/tel
                if (
                    match == "/"
                    or match.startswith("http://")
                    or match.startswith("https://")
                    or match.startswith("#")
                    or match.startswith("data:")
                    or match.startswith("mailto:")
                    or match.startswith("/api/")
                ):
                    continue
                # Strip url anchors if any (e.g., /assets/icons/sprite.svg#icon-venue -> /assets/icons/sprite.svg)
                clean_path = match.split("#")[0].strip()
                if clean_path and clean_path != "/":
                    referenced_urls.add(clean_path)

        assert len(referenced_urls) > 0, "No static assets found in index.html"

        missing_assets: list[str] = []
        for ref in referenced_urls:
            rel = ref.lstrip("/")
            file_path = PUBLIC_DIR / rel
            if not file_path.exists() or not file_path.is_file():
                missing_assets.append(f"{ref} -> resolved to {file_path}")

        assert not missing_assets, f"Broken local asset references found: {missing_assets}"

    def test_manifest_webmanifest_integrity(self) -> None:
        """manifest.webmanifest must have required PWA fields and icons under 20 KB."""
        manifest_path = PUBLIC_DIR / "manifest.webmanifest"
        assert manifest_path.exists(), "manifest.webmanifest not found"

        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data.get("name") == "UtsavAI – Smart Celebration & Event Planner"
        assert manifest_data.get("short_name") == "UtsavAI"
        assert manifest_data.get("display") == "standalone"
        assert "start_url" in manifest_data
        assert "theme_color" in manifest_data
        assert "background_color" in manifest_data

        icons = manifest_data.get("icons", [])
        assert len(icons) >= 3, "Manifest must specify at least 3 icons (svg, 192, 512)"

        icon_sizes = [i.get("sizes") for i in icons]
        assert "192x192" in icon_sizes, "Manifest missing 192x192 icon"
        assert "512x512" in icon_sizes, "Manifest missing 512x512 icon"

        # Check physical existence and file size (< 20 KB)
        for icon in icons:
            src = icon["src"].lstrip("/")
            icon_file = PUBLIC_DIR / src
            assert icon_file.exists(), f"Icon file {src} not found on disk"
            file_size_kb = icon_file.stat().st_size / 1024
            assert file_size_kb < 20, (
                f"Icon {src} size is {file_size_kb:.2f} KB, must be under 20 KB"
            )


@pytest.mark.asyncio
class TestFrontendStaticEndpoints:
    """Verifies that FastAPI serves frontend static files over HTTP correctly."""

    async def test_get_index_html(self, client: AsyncClient) -> None:
        """GET / returns 200 and serves HTML with viewport meta."""
        res = await client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")
        assert "viewport-fit=cover" in res.text

    async def test_get_manifest(self, client: AsyncClient) -> None:
        """GET /manifest.webmanifest returns 200 and valid json."""
        res = await client.get("/manifest.webmanifest")
        assert res.status_code == 200
        data = res.json()
        assert data["short_name"] == "UtsavAI"

    async def test_get_static_css_and_js(self, client: AsyncClient) -> None:
        """GET /static/css/style.css and /static/js/app.js return 200."""
        css_res = await client.get("/static/css/style.css")
        assert css_res.status_code == 200

        js_res = await client.get("/static/js/app.js")
        assert js_res.status_code == 200

    async def test_get_png_icons(self, client: AsyncClient) -> None:
        """GET /assets/icon-192.png and /assets/icon-512.png return 200."""
        res_192 = await client.get("/assets/icon-192.png")
        assert res_192.status_code == 200

        res_512 = await client.get("/assets/icon-512.png")
        assert res_512.status_code == 200
