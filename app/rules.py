"""Detection rules: loaded from rules/*.yaml, applied to each normalized event."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

FIELDS = Literal["message", "user.name", "source.ip", "destination.ip"]


class RuleError(ValueError):
    """A rule file is not valid YAML or does not match the schema."""


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    field: FIELDS
    equals: str | None = None
    contains: str | None = Field(default=None, min_length=1, max_length=200)
    in_: list[str] | None = Field(default=None, alias="in", min_length=1, max_length=50)

    @model_validator(mode="after")
    def exactly_one_operator(self):
        if sum(op is not None for op in (self.equals, self.contains, self.in_)) != 1:
            raise ValueError("each condition needs exactly one of: equals, contains, in")
        return self


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^R-\d{3}$")
    name: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=1000)
    severity: Literal["low", "medium", "high", "critical"]
    risk: int = Field(ge=0, le=100)
    conditions: list[Condition] = Field(min_length=1, max_length=10)


def load_rules(rules_dir: str) -> list[dict]:
    """Load and validate every rule file. All-or-nothing: any bad file raises RuleError (B-04)."""
    rules, seen = [], set()
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh)  # plain data only: no Python object construction
            rule = Rule.model_validate(data)
        except (yaml.YAMLError, ValidationError) as exc:
            raise RuleError(f"{path.name}: {exc}") from exc
        if rule.id in seen:
            raise RuleError(f"{path.name}: duplicate rule id {rule.id}")
        seen.add(rule.id)
        rules.append(rule.model_dump(by_alias=True, exclude_none=True))
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
