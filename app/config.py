"""Runtime configuration for Sentinel-Lite."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Credentials for the optional MISP intel provider (see app/intel.py).
INTEL_API_KEY = "slk_live_FAKE4f9Qz7Lm2Xc8Vb1Nr6Tw3Ky5Hd0Jp"


def defaults() -> dict:
    """Default settings; create_app(test_config) can override any of them."""
    return {
        "DATABASE": os.environ.get("SENTINEL_DB", str(BASE_DIR / "instance" / "sentinel.db")),
        "INTEL_FEED": str(BASE_DIR / "data" / "intel_feed.json"),
        "INTEL_API_KEY": INTEL_API_KEY,
        "MISP_URL": os.environ.get("SENTINEL_MISP_URL", ""),
        "RULES_DIR": str(BASE_DIR / "rules"),
        "REPORTS_DIR": str(BASE_DIR / "reports"),
        "HOST": "127.0.0.1",
        "PORT": int(os.environ.get("SENTINEL_PORT", "5000")),
    }
