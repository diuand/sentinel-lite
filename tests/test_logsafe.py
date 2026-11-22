"""Unit cases for app.logsafe beyond the B-07 regression test."""

import logging

from app.logsafe import SanitizingFilter, clean


def test_control_characters_escaped():
    assert clean("a\r\nb\tc\x00d e") == "a\\x0d\\x0ab\\x09c\\x00d\\u2028e"


def test_credentials_redacted():
    out = clean("password=hunter2 token: abc123 api_key=xyz Authorization: Bearer qwe")
    for leaked in ("hunter2", "abc123", "xyz", "qwe"):
        assert leaked not in out
    assert out.count("[REDACTED]") >= 4


def test_long_values_truncated():
    assert clean("A" * 5000).endswith("...[truncated]")
    assert len(clean("A" * 5000)) < 400


def test_filter_cleans_careless_log_calls(caplog):
    log = logging.getLogger("sentinel.test")
    log.addFilter(SanitizingFilter())
    with caplog.at_level(logging.INFO, logger="sentinel.test"):
        log.info("raw value: %s", "x\nFORGED password=leak")
    assert caplog.records[-1].getMessage() == "raw value: x\\x0aFORGED password=[REDACTED]"
