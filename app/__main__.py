"""Entry point: `python -m app` (what `make run` calls)."""

from . import create_app


def main() -> None:
    app = create_app()
    # tracked exception: seeded bug B-06, open until its fix PR (see tests/test_tracked_exceptions.py)
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=True)  # nosec B201


if __name__ == "__main__":
    main()
