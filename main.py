"""
main.py — OSINTAgent entry point.
"""

import sys
import time
from scanner import fetch_all_articles
from analyzer import analyze_all
from sheets import (load_organizations, load_keywords, load_settings,
                    save_results, get_existing_links, log_scan)
from notifier import send_alert_email
from config import ALERT_THRESHOLD


def run():
    start = time.time()
    print("=" * 60)
    print("OSINTAgent — Starting scan")
    print("=" * 60)

    # 1. Load runtime settings
    settings = load_settings()
    country      = settings.get("country", "Peru")
    country_code = settings.get("country_code", "PE")
    languages    = [l.strip() for l in settings.get("languages", "es,en,he").split(",") if l.strip()]
    threshold    = int(settings.get("alert_threshold", str(ALERT_THRESHOLD)))
    email_alerts = settings.get("email_alerts", "true").lower() == "true"

    print(f"[main] Country={country} ({country_code}) | Languages={languages} | Threshold={threshold}")

    # 2. Load organizations + keywords
    try:
        organizations = load_organizations()
        keywords = load_keywords()
    except Exception as e:
        print(f"[main] Failed to load data: {e}")
        log_scan("ERROR", 0, 0, 0, time.time()-start, str(e))
        sys.exit(1)

    if not organizations:
        print("[main] No organizations found. Exiting.")
        sys.exit(0)

    # 3. Fetch
    articles = fetch_all_articles(organizations, keywords, languages, country_code)
    print(f"\n[main] Fetched: {len(articles)}")

    if not articles:
        log_scan("OK", 0, 0, 0, time.time()-start, "No articles fetched")
        return

    # 4. Deduplicate
    try:
        existing_links = get_existing_links()
        articles = [a for a in articles if a["link"] not in existing_links]
        print(f"[main] After dedup: {len(articles)}")
    except Exception as e:
        print(f"[main] Dedup warning: {e}")

    if not articles:
        log_scan("OK", 0, 0, 0, time.time()-start, "All duplicates")
        return

    # 5. Analyze
    results = analyze_all(articles, keywords, country, threshold)
    print(f"[main] Relevant: {len(results)}")

    # 6. Save
    try:
        save_results(results)
    except Exception as e:
        print(f"[main] Save failed: {e}")

    # 7. Alert
    alerts = [r for r in results if r.get("relevance_score", 0) >= threshold]
    if alerts and email_alerts:
        try:
            send_alert_email(alerts)
        except Exception as e:
            print(f"[main] Email error: {e}")

    duration = time.time() - start
    log_scan("OK", len(articles), len(results), len(alerts), duration)
    print(f"\n[main] Done in {duration:.1f}s | fetched={len(articles)} relevant={len(results)} alerts={len(alerts)}")


if __name__ == "__main__":
    run()
