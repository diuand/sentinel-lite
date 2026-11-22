"""Runtime configuration for Sentinel-Lite.

Secrets come from the environment, or from a local git-ignored `.env` file
(see `.env.example`). They never live in source code (B-01).
"""

import os
from pathlib import Path

from .normalize import MAX_BODY_BYTES

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path: Path = BASE_DIR / ".env") -> None:
    """Read KEY=value lines from a local .env file. Real environment variables win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def defaults() -> dict:
    """Default settings; create_app(test_config) can override any of them."""
    load_env_file()
    return {
        "DATABASE": os.environ.get("SENTINEL_DB", str(BASE_DIR / "instance" / "sentinel.db")),
        "INTEL_FEED": str(BASE_DIR / "data" / "intel_feed.json"),
        "INTEL_API_KEY": os.environ.get("SENTINEL_INTEL_API_KEY", ""),
        "MISP_URL": os.environ.get("SENTINEL_MISP_URL", ""),
        "RULES_DIR": str(BASE_DIR / "rules"),
        "REPORTS_DIR": str(BASE_DIR / "reports"),
        "MAX_CONTENT_LENGTH": MAX_BODY_BYTES,
        "HOST": "127.0.0.1",
        "PORT": int(os.environ.get("SENTINEL_PORT", "5000")),
    }
