"""
scanner.py — Fetches articles from Google News RSS for each organization.
"""

import feedparser
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

from config import (
    GOOGLE_NEWS_RSS_TEMPLATE,
    LANGUAGES,
    COUNTRY,
    COUNTRY_CODE,
    LOOKBACK_HOURS,
)


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
        return True  # include if no date info
    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    return pub_dt >= cutoff


def fetch_articles_for_org(org_name: str, extra_keywords: list[str] = None) -> list[dict]:
    """
    Search Google News for an organization name across all configured languages.
    Returns a deduplicated list of article dicts.
    """
    seen_urls = set()
    articles = []

    search_terms = [org_name]
    if extra_keywords:
        # Also search org_name + each keyword for more targeted results
        for kw in extra_keywords[:3]:  # limit to 3 extra terms
            search_terms.append(f"{org_name} {kw}")

    for query in search_terms:
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
    Fetch articles for all organizations.
    Each org dict should have at least: {"name": str, "keywords": list[str]}
    """
    all_articles = []
    for org in organizations:
        name = org.get("name", "")
        keywords = org.get("keywords", [])
        if not name:
            continue
        print(f"[scanner] Scanning: {name}")
        articles = fetch_articles_for_org(name, keywords)
        print(f"[scanner]   → {len(articles)} articles found")
        all_articles.extend(articles)
    return all_articles
