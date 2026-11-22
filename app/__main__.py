"""Entry point: `python -m app` (what `make run` calls)."""

from . import create_app


def main() -> None:
    app = create_app()
    if not app.config["API_KEY"]:
        raise SystemExit("SENTINEL_API_KEY is not set. Run `make setup` (writes a random key to .env) or export it.")
    # Loopback only, debugger off (B-06). Put a TLS reverse proxy in front for anything beyond this laptop.
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)


if __name__ == "__main__":
    main()
