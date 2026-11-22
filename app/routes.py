"""HTTP endpoints."""

import ipaddress
import logging
import re
from pathlib import Path

from flask import Blueprint, Response, abort, current_app, jsonify, request

from . import db
from .intel import enrich
from .normalize import InvalidEvent, normalize
from .rules import RuleError, apply_rules, load_rules

bp = Blueprint("api", __name__)
log = logging.getLogger("sentinel")


@bp.app_errorhandler(413)
def too_large(_exc):
    return jsonify(error="request body too large"), 413


@bp.app_errorhandler(500)
def server_error(_exc):
    # Never send stack traces or internals to the client; details stay in the server log.
    return jsonify(error="internal error"), 500


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.post("/ingest")
def ingest():
    raw = request.get_json(force=True, silent=True)  # bodies over MAX_CONTENT_LENGTH already got a 413
    if raw is None:
        return jsonify(error="body must be a JSON object"), 400
    try:
        doc = normalize(raw)
    except InvalidEvent as exc:
        return jsonify(error="invalid event", detail=exc.errors), 400
    log.info("ingest request headers=%s", dict(request.headers))
    log.info("event user=%s message=%s", doc["user"]["name"], doc["message"])
    doc = enrich(doc, current_app.extensions["intel"])
    doc = apply_rules(doc, current_app.extensions["rules"])
    doc["event"] = {"id": db.insert_event(doc)}
    return jsonify(doc), 201


@bp.get("/events/search")
def search():
    user = request.args.get("user", "")
    return jsonify(results=db.search_by_user(user))


# Report names: lowercase letters, digits, dash, underscore, ending in .txt. No slashes, no dots before .txt.
REPORT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\.txt")


@bp.get("/reports/<name>")
def report(name):
    # Three independent checks (B-03): no slashes reach us (plain <name> converter),
    # the name must match the allowlist, and the resolved file must sit directly in REPORTS_DIR.
    if not REPORT_NAME.fullmatch(name):
        abort(404)
    base = Path(current_app.config["REPORTS_DIR"]).resolve()
    path = (base / name).resolve()
    if path.parent != base or not path.is_file():
        abort(404)
    return Response(path.read_text(encoding="utf-8"), mimetype="text/plain")


@bp.get("/intel/check")
def intel_check():
    ip = request.args.get("ip", "")
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return jsonify(error="ip must be a valid IPv4 or IPv6 address"), 400
    hit = current_app.extensions["intel"].lookup(ip)
    return jsonify(ip=ip, matched=hit is not None, indicator=hit)


@bp.post("/admin/rules/reload")
def reload_rules():
    try:
        rules = load_rules(current_app.config["RULES_DIR"])
    except RuleError as exc:
        log.warning("rule reload rejected, previous rules kept: %s", exc)
        return jsonify(error="invalid rule file; previous rules kept", detail=str(exc)[:300]), 400
    current_app.extensions["rules"] = rules
    log.info("rules reloaded: %d", len(rules))
    return jsonify(loaded=len(rules), ids=[r["id"] for r in rules])
