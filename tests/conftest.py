import json
import shutil
from pathlib import Path

import pytest

from app import create_app
from tests.open_bugs import OPEN_BUGS

ROOT = Path(__file__).resolve().parent.parent
TEST_API_KEY = "test-only-key-not-a-secret"


def pytest_collection_modifyitems(config, items):
    for item in items:
        marker = item.get_closest_marker("seeded_bug")
        if marker and marker.args[0] in OPEN_BUGS:
            item.add_marker(pytest.mark.xfail(strict=True, reason=f"{marker.args[0]} is open (seeded on purpose)"))


@pytest.fixture
def app(tmp_path):
    rules_dir = tmp_path / "rules"
    reports_dir = tmp_path / "reports"
    shutil.copytree(ROOT / "rules", rules_dir)
    shutil.copytree(ROOT / "reports", reports_dir)
    app = create_app(
        {
            "DATABASE": str(tmp_path / "test.db"),
            "RULES_DIR": str(rules_dir),
            "REPORTS_DIR": str(reports_dir),
            "API_KEY": TEST_API_KEY,
            # Show real 500 responses instead of re-raising inside the test.
            "PROPAGATE_EXCEPTIONS": False,
        }
    )
    yield app


@pytest.fixture
def client(app):
    """A client that sends the correct API key, like a legitimate log shipper."""
    c = app.test_client()
    c.environ_base["HTTP_X_API_KEY"] = TEST_API_KEY
    return c


@pytest.fixture
def anon(app):
    """A client with no credentials at all."""
    return app.test_client()


@pytest.fixture(scope="session")
def samples():
    return json.loads((ROOT / "samples" / "events.json").read_text())


@pytest.fixture(scope="session")
def malformed():
    return json.loads((ROOT / "samples" / "malformed.json").read_text())
