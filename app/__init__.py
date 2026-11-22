"""Sentinel-Lite: a tiny log-enrichment service."""

import logging

from flask import Flask

from . import config, db
from .intel import LocalFeedProvider
from .routes import bp
from .rules import load_rules


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(config.defaults())
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    db.init_app(app)
    app.extensions["intel"] = LocalFeedProvider(app.config["INTEL_FEED"])
    app.extensions["rules"] = load_rules(app.config["RULES_DIR"])
    app.register_blueprint(bp)
    return app
