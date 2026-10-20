"""
Vercel serverless entrypoint for UtsavAI.
Imports the FastAPI ASGI application as `app`.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path for absolute imports
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.main import app  # noqa: E402

__all__ = ["app"]
