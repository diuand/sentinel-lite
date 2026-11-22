"""Schema cases for detection rules beyond the B-04 regression tests."""

import pytest

from app.rules import RuleError, load_rules

HEAD = "id: R-100\nname: test rule\nseverity: low\n"
VALID = HEAD + "risk: 5\nconditions:\n  - field: message\n    contains: x\n"


@pytest.mark.parametrize("text", [
    HEAD + "risk: 5\nconditions:\n  - field: message\n    contains: x\n    equals: y\n",   # two operators
    HEAD + "risk: 5\nconditions:\n  - field: __class__\n    contains: x\n",                # field not allowed
    HEAD + "risk: 1000\nconditions:\n  - field: message\n    contains: x\n",              # risk out of range
    HEAD + "risk: 5\nexec: echo hi\nconditions:\n  - field: message\n    contains: x\n",  # unknown key
    "- just\n- a list\n",
    "id: [unclosed\n",
])
def test_invalid_rule_rejected(tmp_path, text):
    (tmp_path / "r.yaml").write_text(text)
    with pytest.raises(RuleError):
        load_rules(str(tmp_path))


def test_duplicate_ids_rejected(tmp_path):
    (tmp_path / "a.yaml").write_text(VALID)
    (tmp_path / "b.yaml").write_text(VALID)
    with pytest.raises(RuleError, match="duplicate"):
        load_rules(str(tmp_path))


def test_shipped_rules_are_valid():
    assert [r["id"] for r in load_rules("rules")] == ["R-001", "R-002"]
