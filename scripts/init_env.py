#!/usr/bin/env python3
"""Create .env from .env.example (if missing) and give SENTINEL_API_KEY a random value if empty.

Run by `make setup`. The key is generated locally with `secrets`, is never
printed, and .env is git-ignored.
"""

import re
import secrets
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
env, example = root / ".env", root / ".env.example"

if not env.exists():
    shutil.copyfile(example, env)
    print("created .env from .env.example (git-ignored)")

text = env.read_text(encoding="utf-8")
if not re.search(r"^SENTINEL_API_KEY=\S+", text, re.MULTILINE):
    key = secrets.token_urlsafe(32)
    if re.search(r"^SENTINEL_API_KEY=", text, re.MULTILINE):
        text = re.sub(r"^SENTINEL_API_KEY=.*$", f"SENTINEL_API_KEY={key}", text, flags=re.MULTILINE)
    else:
        text += f"\nSENTINEL_API_KEY={key}\n"
    env.write_text(text, encoding="utf-8")
    env.chmod(0o600)
    print("generated a random SENTINEL_API_KEY in .env (clients send it as the X-API-Key header)")
