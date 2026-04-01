"""
scanner.py — Fetches articles from Google News RSS.
Search queries are loaded from the Keywords sheet in Google Sheets.
"""

import feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

from config import LANGUAGES, COUNTRY_CODE, LOOKBACK_HOURS


def _build_rss_url(query: str, lang: str) -> str:
    encoded = quote_plus(query)
    return (
        f"https://news.google.com/rss/search?q={encoded}"
        f"&hl={lang}&gl={COUNTRY_CODE}&ceid={COUNTRY_CODE}:{lang}"
    )


def _is_recent(entry) -> bool:
    published = entry.get("published_parsed")
    if not published:
        return True
    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    return pub_dt >= cutoff


def _fetch_query(query: str, org_name: str, seen_urls: set) -> list[dict]:
    articles = []
    for lang in LANGUAGES:
        url = _build_rss_url(query, lang)
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[scanner] RSS error for '{query}' ({lang}): {e}")
            continue
        for entry in feed.entries:
            link = entry.get("link", "")
            if link in seen_urls or not _is_recent(entry):
                continue
            seen_urls.add(link)
            articles.append({
                "org_name": org_name,
                "title": entry.get("title", ""),
                "link": link,
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", ""),
                "lang": lang,
            })
    return articles


def fetch_all_articles(organizations: list[dict], keywords: dict) -> list[dict]:
    """
    Fetch articles using search queries from the Keywords sheet + org names.
    """
    seen_urls = set()
    all_articles = []

    # Use keyword phrases as search queries
    search_queries = keywords.get("search_queries", [])
    print(f"[scanner] Running {len(search_queries)} keyword queries...")
    for query in search_queries:
        results = _fetch_query(query, "General", seen_urls)
        if results:
            print(f"[scanner]   '{query}' → {len(results)} articles")
        all_articles.extend(results)

    print(f"[scanner] Keyword queries total: {len(all_articles)} articles\n")

    # Org-specific queries for named organizations
    for org in organizations:
        name = org.get("name", "")
        if not name or (" " not in name and len(name) <= 12):
            continue
        print(f"[scanner] Scanning org: {name}")
        results = _fetch_query(f"{name} Perú", name, seen_urls)
        print(f"[scanner]   → {len(results)} articles")
        all_articles.extend(results)

    return all_articles
