"""
scanner.py — Fetches articles from Google News RSS.
Uses two strategies:
1. General topic queries (protests, BDS, antisemitism in Peru)
2. Organization name queries for well-known groups
"""

import feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

from config import (
    GOOGLE_NEWS_RSS_TEMPLATE,
    LANGUAGES,
    COUNTRY,
    COUNTRY_CODE,
    LOOKBACK_HOURS,
)

# General queries to run on every scan (regardless of org list)
GENERAL_QUERIES = [
    # Spanish
    "manifestación Israel Perú",
    "protesta Israel Lima",
    "marcha Palestina Perú",
    "boicot Israel Perú",
    "BDS Perú",
    "antisemitismo Perú",
    "contra Israel Lima",
    "solidaridad Palestina Perú",
    # English
    "protest Israel Peru",
    "BDS Peru",
    "antisemitism Peru",
    # Hebrew
    "הפגנה פרו ישראל",
]


def _build_rss_url(query: str, lang: str) -> str:
    encoded = quote_plus(query)
    return GOOGLE_NEWS_RSS_TEMPLATE.format(
        query=encoded,
        lang=lang,
        country=COUNTRY_CODE,
    )


def _is_recent(entry) -> bool:
    """Return True if the article was published within LOOKBACK_HOURS."""
    published = entry.get("published_parsed")
    if not published:
        return True
    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    return pub_dt >= cutoff


def _fetch_query(query: str, org_name: str, seen_urls: set) -> list[dict]:
    """Fetch articles for a single query string across all languages."""
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
            if link in seen_urls:
                continue
            if not _is_recent(entry):
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


def fetch_all_articles(organizations: list[dict]) -> list[dict]:
    """
    Fetch articles using:
    1. General protest/BDS/antisemitism queries for Peru
    2. Specific org name queries for larger/named organizations
    """
    seen_urls = set()
    all_articles = []

    # Strategy 1: General topic queries
    print("[scanner] Running general topic queries...")
    for query in GENERAL_QUERIES:
        results = _fetch_query(query, "General", seen_urls)
        if results:
            print(f"[scanner]   '{query}' → {len(results)} articles")
        all_articles.extend(results)

    print(f"[scanner] General queries total: {len(all_articles)} articles\n")

    # Strategy 2: Organization-specific queries (only for multi-word/named orgs)
    for org in organizations:
        name = org.get("name", "")
        if not name:
            continue
        # Only search by name if it looks like a real organization name (has spaces or > 10 chars)
        if " " in name or len(name) > 12:
            print(f"[scanner] Scanning org: {name}")
            results = _fetch_query(f"{name} Perú", name, seen_urls)
            print(f"[scanner]   → {len(results)} articles")
            all_articles.extend(results)

    return all_articles
