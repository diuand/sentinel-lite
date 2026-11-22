"""Defence-in-depth cases for /reports/<name> beyond the B-03 regression tests."""

import os
from pathlib import Path

import pytest


def test_symlink_out_of_reports_dir_is_refused(client, app):
    reports = Path(app.config["REPORTS_DIR"])
    outside = reports.parent / "outside.txt"
    outside.write_text("B03-SYMLINK-MARKER")
    os.symlink(outside, reports / "linked.txt")
    resp = client.get("/reports/linked.txt")
    assert resp.status_code == 404
    assert b"B03-SYMLINK-MARKER" not in resp.data


@pytest.mark.parametrize("name", [".hidden.txt", "Daily-Summary.txt", "daily-summary.TXT", "daily.summary.txt",
                                  "summary.txt.bak", "..", "%2E%2E"])
def test_names_outside_the_allowlist_are_refused(client, name):
    assert client.get(f"/reports/{name}").status_code == 404
