"""Entry point: `python -m app` (what `make run` calls)."""

from . import create_app


def main() -> None:
    app = create_app()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=True)


if __name__ == "__main__":
    main()
