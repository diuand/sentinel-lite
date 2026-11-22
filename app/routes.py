"""HTTP endpoints."""

import ipaddress
import logging
import os

from flask import Blueprint, Response, abort, current_app, jsonify, request

from . import db
from .intel import enrich
from .normalize import normalize
from .rules import apply_rules, load_rules

bp = Blueprint("api", __name__)
log = logging.getLogger("sentinel")


@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.post("/ingest")
def ingest():
    raw = request.get_json(force=True)
    log.info("ingest request headers=%s", dict(request.headers))
    log.info("event user=%s message=%s", raw.get("user"), raw.get("message"))
    doc = normalize(raw)
    doc = enrich(doc, current_app.extensions["intel"])
    doc = apply_rules(doc, current_app.extensions["rules"])
    doc["event"] = {"id": db.insert_event(doc)}
    return jsonify(doc), 201


@bp.get("/events/search")
def search():
    user = request.args.get("user", "")
    return jsonify(results=db.search_by_user(user))


@bp.get("/reports/<path:name>")
def report(name):
    path = os.path.join(current_app.config["REPORTS_DIR"], name)
    if not os.path.isfile(path):
        abort(404)
    with open(path, encoding="utf-8") as fh:
        return Response(fh.read(), mimetype="text/plain")


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
    rules = load_rules(current_app.config["RULES_DIR"])
    current_app.extensions["rules"] = rules
    log.info("rules reloaded: %d", len(rules))
    return jsonify(loaded=len(rules), ids=[r["id"] for r in rules])
