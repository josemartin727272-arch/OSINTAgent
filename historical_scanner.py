"""
historical_scanner.py — One-shot historical ingestion for OSINTAgent.

Sources:
  - GDELT DOC API (primary — full year range coverage)
  - Google News RSS with after:/before: operators
  - NewsAPI.org (optional, requires NEWSAPI_KEY)

Usage:
    python3 historical_scanner.py --year 2025
    python3 historical_scanner.py --year 2024 --methods gdelt gnews
    NEWSAPI_KEY=xxx python3 historical_scanner.py --methods gdelt gnews newsapi
"""

import os
import sys
import time
import argparse
import requests
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from analyzer import analyze_all
from sheets import save_results, get_existing_links, load_keywords, load_settings


# ── GDELT DOC API ───────────────────────────────────────────────────────────

GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"

GDELT_QUERIES = [
    "Israel Palestine Peru protest",
    "BDS Peru Lima",
    "Israel Peru Lima manifestacion",
    "protesta Israel Lima Peru",
    "boicot Israel Peru",
    "Palestina Peru marcha",
    "antisemitismo Peru Lima",
    "comunidad judia Lima Peru",
    "embajada Israel Lima Peru",
]


def fetch_gdelt_articles(query: str, start_date: str, end_date: str,
                         max_records: int = 250) -> list:
    """GDELT DOC API. Dates in YYYYMMDDHHMMSS."""
    params = {
        "query":         query,
        "mode":          "artlist",
        "maxrecords":    max_records,
        "startdatetime": start_date,
        "enddatetime":   end_date,
        "format":        "json",
        "sort":          "DateDesc",
    }
    try:
        resp = requests.get(GDELT_API, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"[gdelt] HTTP {resp.status_code} for '{query}'")
            return []
        data = resp.json() if resp.text.strip().startswith("{") else {}
        articles = data.get("articles", [])
    except Exception as e:
        print(f"[gdelt] Error '{query}': {e}")
        return []

    result = []
    for a in articles:
        result.append({
            "org_name":  "General",
            "title":     a.get("title", ""),
            "link":      a.get("url", ""),
            "summary":   a.get("seendescription", "") or a.get("title", ""),
            "published": a.get("seendate", ""),
            "source":    a.get("domain", ""),
            "lang":      str(a.get("language", ""))[:2].lower(),
        })
    print(f"[gdelt] '{query}' {start_date[:8]}–{end_date[:8]}: {len(result)}")
    return result


def scan_historical_gdelt(start_year: int = 2025, sleep_sec: float = 5.0) -> list:
    all_articles = []
    seen_urls = set()

    start = datetime(start_year, 1, 1)
    end   = datetime.now()

    current = start
    while current < end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        if next_month > end:
            next_month = end

        start_str = current.strftime("%Y%m%d%H%M%S")
        end_str   = next_month.strftime("%Y%m%d%H%M%S")

        print(f"\n[historical/gdelt] {current.strftime('%B %Y')}")

        for query in GDELT_QUERIES:
            for a in fetch_gdelt_articles(query, start_str, end_str):
                if a["link"] and a["link"] not in seen_urls:
                    seen_urls.add(a["link"])
                    all_articles.append(a)
            time.sleep(sleep_sec)

        current = next_month

    print(f"\n[historical/gdelt] Total unique: {len(all_articles)}")
    return all_articles


# ── Google News historical ──────────────────────────────────────────────────

HISTORICAL_QUERIES = [
    "protesta Lima Israel Palestina",
    "manifestación Lima Israel",
    "BDS Peru Lima",
    "boicot Israel Peru",
    "marcha Lima Palestina",
    "antisemitismo Peru",
    "comunidad judía Lima Israel",
    "embajada Israel Lima",
    "universidades Peru Palestina Israel",
    "UNMSM Palestina protesta",
]


def fetch_google_news_historical(query: str, after: str, before: str,
                                 lang: str = "es",
                                 country_code: str = "PE") -> list:
    """after/before in YYYY-MM-DD."""
    enhanced = f"{query} after:{after} before:{before}"
    encoded = quote_plus(enhanced)
    url = (f"https://news.google.com/rss/search?q={encoded}"
           f"&hl={lang}&gl={country_code}&ceid={country_code}:{lang}")
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        print(f"[gnews_hist] Error: {e}")
        return []

    return [{
        "org_name":  "General",
        "title":     entry.get("title", ""),
        "link":      entry.get("link", ""),
        "summary":   entry.get("summary", ""),
        "published": entry.get("published", ""),
        "source":    entry.get("source", {}).get("title", ""),
        "lang":      lang,
    } for entry in feed.entries]


def scan_google_news_historical(start_year: int = 2025,
                                sleep_sec: float = 0.3) -> list:
    all_articles = []
    seen_urls = set()

    start = datetime(start_year, 1, 1)
    end   = datetime.now()
    current = start

    while current < end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        if next_month > end:
            next_month = end

        after  = current.strftime("%Y-%m-%d")
        before = next_month.strftime("%Y-%m-%d")
        print(f"[gnews_hist] {after} → {before}")

        for query in HISTORICAL_QUERIES:
            for lang in ("es", "en"):
                for a in fetch_google_news_historical(query, after, before, lang):
                    if a["link"] and a["link"] not in seen_urls:
                        seen_urls.add(a["link"])
                        all_articles.append(a)
                time.sleep(sleep_sec)

        current = next_month

    print(f"[gnews_hist] Total unique: {len(all_articles)}")
    return all_articles


# ── NewsAPI (optional) ──────────────────────────────────────────────────────

def fetch_newsapi_historical(query: str, from_date: str, to_date: str) -> list:
    key = os.environ.get("NEWSAPI_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query, "from": from_date, "to": to_date,
                "language": "es", "sortBy": "relevancy",
                "pageSize": 100, "apiKey": key,
            },
            timeout=20,
        )
        articles = resp.json().get("articles", [])
    except Exception as e:
        print(f"[newsapi] Error: {e}")
        return []
    return [{
        "org_name":  "General",
        "title":     a.get("title", ""),
        "link":      a.get("url", ""),
        "summary":   a.get("description", "") or a.get("title", ""),
        "published": a.get("publishedAt", ""),
        "source":    a.get("source", {}).get("name", ""),
        "lang":      "es",
    } for a in articles if a.get("url")]


def scan_newsapi_historical(start_year: int = 2025) -> list:
    if not os.environ.get("NEWSAPI_KEY"):
        print("[newsapi] NEWSAPI_KEY not set — skipping")
        return []

    all_articles = []
    seen_urls = set()
    start = datetime(start_year, 1, 1)
    end   = datetime.now()
    current = start

    while current < end:
        next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
        if next_month > end:
            next_month = end
        from_d = current.strftime("%Y-%m-%d")
        to_d   = next_month.strftime("%Y-%m-%d")
        print(f"[newsapi] {from_d} → {to_d}")
        for query in HISTORICAL_QUERIES[:5]:
            for a in fetch_newsapi_historical(query, from_d, to_d):
                if a["link"] and a["link"] not in seen_urls:
                    seen_urls.add(a["link"])
                    all_articles.append(a)
            time.sleep(0.3)
        current = next_month

    print(f"[newsapi] Total unique: {len(all_articles)}")
    return all_articles


# ── Orchestration ───────────────────────────────────────────────────────────

def run_historical_scan(start_year: int = 2025, methods=None):
    methods = methods or ["gdelt", "gnews"]
    print("=" * 60)
    print(f"Historical Scan — {start_year} → {datetime.now().year}")
    print(f"Methods: {methods}")
    print("=" * 60)

    settings  = load_settings()
    keywords  = load_keywords()
    threshold = 4  # lower than live threshold for historical coverage

    existing_links = get_existing_links()
    seen_urls = set(existing_links)
    all_articles = []

    if "gdelt" in methods:
        print("\n--- GDELT Scan ---")
        for a in scan_historical_gdelt(start_year):
            if a["link"] and a["link"] not in seen_urls:
                seen_urls.add(a["link"])
                all_articles.append(a)

    if "gnews" in methods:
        print("\n--- Google News Historical ---")
        for a in scan_google_news_historical(start_year):
            if a["link"] and a["link"] not in seen_urls:
                seen_urls.add(a["link"])
                all_articles.append(a)

    if "newsapi" in methods:
        print("\n--- NewsAPI Historical ---")
        for a in scan_newsapi_historical(start_year):
            if a["link"] and a["link"] not in seen_urls:
                seen_urls.add(a["link"])
                all_articles.append(a)

    print(f"\n[historical] New unique articles: {len(all_articles)}")
    if not all_articles:
        print("[historical] Nothing to process.")
        return

    print("[historical] Analyzing...")
    results = analyze_all(
        all_articles, keywords,
        country=settings.get("country", "Peru"),
        threshold=threshold,
        feedback=None,
        organizations=None,
    )

    relevant = [r for r in results if r.get("relevance_score", 0) > 0]
    print(f"[historical] Relevant (score>0): {len(relevant)} / {len(results)}")

    if relevant:
        save_results(relevant)
        print(f"[historical] Saved {len(relevant)} results")

    print("\n=== TOP 20 ===")
    top = sorted(relevant, key=lambda x: x.get("relevance_score", 0), reverse=True)[:20]
    for r in top:
        print(f"[{r.get('relevance_score', 0)}] {str(r.get('title',''))[:70]}")
        print(f"   {r.get('source','')} | {str(r.get('published',''))[:10]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSINTAgent historical scan")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--methods", nargs="+",
                        default=["gdelt", "gnews"],
                        choices=["gdelt", "gnews", "newsapi"])
    args = parser.parse_args()
    try:
        run_historical_scan(args.year, args.methods)
    except KeyboardInterrupt:
        print("\n[historical] Interrupted by user.")
        sys.exit(130)
