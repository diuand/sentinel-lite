#!/usr/bin/env python3
"""Show that enrichment changes the outcome: the same kind of event, from a feed IP and from a clean IP.

Runs the real app in-process (Flask test client, temporary database), so no
port is opened and nothing leaves the machine. Usage: python3 scripts/demo_enrichment.py
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402

KEY = "demo-demo-demo-demo"
samples = json.loads((ROOT / "samples" / "events.json").read_text())

with tempfile.TemporaryDirectory() as tmp:
    app = create_app({"DATABASE": f"{tmp}/demo.db", "API_KEY": KEY})
    client = app.test_client()
    client.environ_base["HTTP_X_API_KEY"] = KEY
    for name in ("intel_match", "clean", "r001_positive", "r002_positive"):
        sent = samples[name]
        got = client.post("/ingest", json=sent).get_json()
        print(f"--- {name}: src_ip={sent['src_ip']} user={sent['user']}")
        print(f"    tags       = {got['tags']}")
        print(f"    risk_score = {got['risk_score']}")
        if "threat" in got:
            print(f"    threat     = {json.dumps(got['threat'])}")
    print("--- GET /intel/check")
    for ip in ("203.0.113.66", "192.0.2.10"):
        r = client.get(f"/intel/check?ip={ip}").get_json()
        print(f"    {ip:<14} matched={r['matched']}")
