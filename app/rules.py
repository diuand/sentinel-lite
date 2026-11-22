"""Detection rules: loaded from rules/*.yaml, applied to each normalized event."""

from pathlib import Path

import yaml


def load_rules(rules_dir: str) -> list[dict]:
    rules = []
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        with open(path, encoding="utf-8") as fh:
            rules.append(yaml.load(fh, Loader=yaml.Loader))
    return rules


def _field(doc: dict, dotted: str):
    value = doc
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches(doc: dict, cond: dict) -> bool:
    value = _field(doc, cond["field"])
    if value is None:
        return False
    if "equals" in cond:
        return value == cond["equals"]
    if "contains" in cond:
        return cond["contains"] in str(value)
    if "in" in cond:
        return value in cond["in"]
    return False


def apply_rules(doc: dict, rules: list[dict]) -> dict:
    for rule in rules:
        if all(_matches(doc, cond) for cond in rule["conditions"]):
            doc["tags"].append(f"rule:{rule['id']}")
            doc.setdefault("rule", []).append({"id": rule["id"], "name": rule["name"], "severity": rule["severity"]})
            doc["risk_score"] = min(100, doc["risk_score"] + int(rule.get("risk", 0)))
    return doc
