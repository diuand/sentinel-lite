"""Generate the text summary served by GET /reports/<name>.

Run with `make report` (python -m app.reports).
"""

from datetime import UTC, datetime
from pathlib import Path

from . import create_app, db


def render_summary(counts: dict) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "Sentinel-Lite summary",
        f"Generated: {now}",
        f"Events stored: {counts['total']}",
        f"Events matching intel feed: {counts['matched']}",
        "Top sources by risk score:",
    ]
    lines += [f"  {ip:<18} {score}" for ip, score in counts["top"]] or ["  (none)"]
    return "\n".join(lines) + "\n"


def main() -> None:
    app = create_app()
    with app.app_context():
        text = render_summary(db.summary_counts())
    out = Path(app.config["REPORTS_DIR"]) / "summary.txt"
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
