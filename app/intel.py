"""Threat-intel providers and the enrichment step.

The default provider reads a local JSON feed, so nothing leaves the laptop.
MispProvider is a documented stub for a real MISP instance; it is never used
by default and never called in tests. Shodan is a possible future provider
(see docs/PROJECT.md), not implemented.
"""

import json
from abc import ABC, abstractmethod

INTEL_RISK_BOOST = 60
MATCH_TAG = "threat.indicator.matched"


class IntelProvider(ABC):
    name = "abstract"

    @abstractmethod
    def lookup(self, ip: str) -> dict | None:
        """Return the indicator for this IP, or None when it is not known-bad."""


class LocalFeedProvider(IntelProvider):
    name = "local-feed"

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as fh:
            feed = json.load(fh)
        self.feed_name = feed.get("name", "local")
        self._index = {ind["value"]: ind for ind in feed["indicators"] if ind.get("type") == "ip-src"}

    def lookup(self, ip: str) -> dict | None:
        return self._index.get(ip)


class MispProvider(IntelProvider):
    """Stub for MISP's REST search API. Not wired in by default."""

    name = "misp"

    def __init__(self, url: str, api_key: str, timeout: float = 5.0):
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def lookup(self, ip: str) -> dict | None:
        import requests  # imported lazily: only needed if this provider is enabled

        resp = requests.post(
            f"{self.url}/attributes/restSearch",
            json={"value": ip, "type": "ip-src", "returnFormat": "json"},
            headers={"Authorization": self.api_key, "Accept": "application/json"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        hits = resp.json().get("response", {}).get("Attribute", [])
        if not hits:
            return None
        return {"type": "ip-src", "value": ip, "threat": hits[0].get("comment", "MISP match"), "confidence": 70}


def enrich(doc: dict, provider: IntelProvider) -> dict:
    """Tag events whose source IP is in the feed and raise their risk score."""
    hit = provider.lookup(doc["source"]["ip"])
    if hit:
        doc["tags"].append(MATCH_TAG)
        doc["threat"] = {
            "indicator": {"type": "ipv4-addr", "ip": hit["value"], "description": hit.get("threat", "")},
            "feed": {"name": getattr(provider, "feed_name", provider.name)},
            "confidence": hit.get("confidence", 50),
        }
        doc["risk_score"] = min(100, doc["risk_score"] + INTEL_RISK_BOOST)
    return doc
