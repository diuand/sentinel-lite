"""Turn a raw log event into a small ECS-like document."""

BASE_RISK = 10


def normalize(raw: dict) -> dict:
    """Map the raw fields (ts, src_ip, dst_ip, user, message) to ECS-like names."""
    return {
        "@timestamp": raw["ts"],
        "source": {"ip": raw["src_ip"]},
        "destination": {"ip": raw["dst_ip"]},
        "user": {"name": raw["user"].strip().lower()},
        "message": raw["message"].strip(),
        "tags": [],
        "risk_score": BASE_RISK,
    }
