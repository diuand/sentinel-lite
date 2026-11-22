"""Make untrusted values safe to write into a log line (B-07).

- Control characters (CR, LF, tabs, NUL, Unicode line separators...) are
  escaped, so one event is always one log line and nobody can forge a second.
- `key=value` pairs that look like credentials are redacted.
- Long values are truncated, so one request cannot flood the log.
"""

import logging
import re

MAX_LEN = 300
_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|authorization|bearer)\b(\s*[=:]\s*|\s+)([^\s,;&]+)"
)
_SCHEME = re.compile(r"(?i)\b(bearer|basic)\s+[^\s,;&]+")  # Authorization: Bearer <token>
_CONTROL = re.compile(r"[\x00-\x1f\x7f\x85  ]")


def _escape(match: re.Match) -> str:
    code = ord(match.group())
    return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}"


def clean(value: object, limit: int = MAX_LEN) -> str:
    text = _SCHEME.sub(lambda m: f"{m.group(1)} [REDACTED]", str(value))
    text = _SECRET.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
    text = _CONTROL.sub(_escape, text)
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


class SanitizingFilter(logging.Filter):
    """Safety net on the `sentinel` logger: even a careless future log call ends up as one clean line."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = clean(record.getMessage(), limit=2000)
        record.args = None
        return True
