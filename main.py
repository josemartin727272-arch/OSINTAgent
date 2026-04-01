"""
main.py — OSINTAgent entry point.
Orchestrates: load orgs → scan → analyze → save → alert.
"""

import sys
from scanner import fetch_all_articles
from analyzer import analyze_all
from sheets import load_organizations, save_results, get_existing_links
from notifier import send_alert_email
from config import ALERT_THRESHOLD


def run():
    print("=" * 60)
    print("OSINTAgent — Starting scan")
    print("=" * 60)

    # 1. Load organizations from Google Sheets
    try:
        organizations = load_organizations()
    except Exception as e:
        print(f"[main] Failed to load organizations: {e}")
        sys.exit(1)

    if not organizations:
        print("[main] No organizations found. Exiting.")
        sys.exit(0)

    # 2. Fetch articles from Google News RSS
    articles = fetch_all_articles(organizations)
    print(f"\n[main] Total articles fetched: {len(articles)}")

    if not articles:
        print("[main] No new articles found.")
        return

    # 3. Remove already-saved articles (deduplication)
    try:
        existing_links = get_existing_links()
        articles = [a for a in articles if a["link"] not in existing_links]
        print(f"[main] After deduplication: {len(articles)} new articles")
    except Exception as e:
        print(f"[main] Warning: could not check duplicates: {e}")

    if not articles:
        print("[main] All articles already processed.")
        return

    # 4. Analyze with Gemini
    print(f"\n[main] Analyzing {len(articles)} articles with Gemini...")
    results = analyze_all(articles)
    print(f"[main] Relevant results: {len(results)}")

    # 5. Save all results to Google Sheets
    try:
        save_results(results)
    except Exception as e:
        print(f"[main] Failed to save results: {e}")

    # 6. Send email for high-relevance alerts
    alerts = [r for r in results if r.get("relevance_score", 0) >= ALERT_THRESHOLD]
    print(f"\n[main] High-relevance alerts (score >= {ALERT_THRESHOLD}): {len(alerts)}")

    if alerts:
        try:
            send_alert_email(alerts)
        except Exception as e:
            print(f"[main] Email error: {e}")

    print("\n[main] Scan complete.")
    print(f"  Total fetched:  {len(articles)}")
    print(f"  Relevant:       {len(results)}")
    print(f"  Alerts sent:    {len(alerts)}")


if __name__ == "__main__":
    run()
