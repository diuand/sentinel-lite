"""Validate a raw log event and turn it into a small ECS-like document (B-05)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, ValidationError

BASE_RISK = 10
MAX_BODY_BYTES = 64 * 1024  # Flask MAX_CONTENT_LENGTH: anything larger is a 413 before parsing


class InvalidEvent(ValueError):
    def __init__(self, errors: list[dict]):
        super().__init__("invalid event")
        self.errors = errors


class RawEvent(BaseModel):
    """The only shape /ingest accepts. Unknown extra fields are dropped."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    ts: datetime
    src_ip: IPvAnyAddress
    dst_ip: IPvAnyAddress
    user: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._@-]+$")
    message: str = Field(min_length=1, max_length=4096)


def normalize(raw: object) -> dict:
    """Validate, then map the raw fields to ECS-like names. Raises InvalidEvent, never crashes."""
    try:
        event = RawEvent.model_validate(raw)
    except ValidationError as exc:
        # Report which field failed and why, without echoing the submitted values back.
        raise InvalidEvent([{"field": ".".join(map(str, e["loc"])) or "body", "problem": e["msg"]}
                            for e in exc.errors()]) from exc
    return {
        "@timestamp": event.ts.isoformat().replace("+00:00", "Z"),
        "source": {"ip": str(event.src_ip)},
        "destination": {"ip": str(event.dst_ip)},
        "user": {"name": event.user.lower()},
        "message": event.message,
        "tags": [],
        "risk_score": BASE_RISK,
    }
