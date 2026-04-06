"""
summary_runner.py — Generate and send periodic summary reports.
Called by GitHub Actions on schedule.
Usage: python summary_runner.py --period weekly|monthly|annual
"""

import sys
import argparse
from datetime import datetime, timezone, timedelta
from sheets import load_results, load_settings
from notifier import send_weekly_summary, send_monthly_summary, send_annual_summary

LIMA_TZ = timezone(timedelta(hours=-5))


def filter_by_period(records: list, period: str) -> tuple:
    now = datetime.now(LIMA_TZ)

    def parse_ts(r):
        ts = str(r.get("timestamp", ""))[:16]
        try:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M").replace(tzinfo=LIMA_TZ)
        except Exception:
            return None

    if period == "weekly":
        # Last 7 days
        cutoff = now - timedelta(days=7)
        label = f"{cutoff.strftime('%d/%m/%Y')} – {now.strftime('%d/%m/%Y')}"
    elif period == "monthly":
        # Last 30 days
        cutoff = now - timedelta(days=30)
        label = now.strftime("%B %Y")
    elif period == "annual":
        # Last 365 days
        cutoff = now - timedelta(days=365)
        label = str(now.year)
    else:
        raise ValueError(f"Unknown period: {period}")

    filtered = []
    for r in records:
        ts = parse_ts(r)
        if ts and ts >= cutoff:
            filtered.append(r)

    return filtered, label


def run(period: str):
    print(f"[summary_runner] Generating {period} report...")
    settings = load_settings()

    # Check if this summary type is enabled
    key = f"{period}_summary" if period != "annual" else "annual_summary"
    if settings.get(key, "true").lower() != "true":
        print(f"[summary_runner] {period} summaries disabled in settings. Skipping.")
        return

    records = load_results()
    filtered, label = filter_by_period(records, period)

    print(f"[summary_runner] {len(filtered)} records for period: {label}")

    if not filtered:
        print("[summary_runner] No data for this period, skipping.")
        return

    if period == "weekly":
        send_weekly_summary(filtered, label)
    elif period == "monthly":
        send_monthly_summary(filtered, label)
    elif period == "annual":
        send_annual_summary(filtered, label)

    print("[summary_runner] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=["weekly", "monthly", "annual"], required=True)
    args = parser.parse_args()
    run(args.period)
