"""
scanner.py — Fetches articles from Google News RSS.
Reads country/language settings dynamically.
"""

import feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

from config import LOOKBACK_HOURS


def _build_rss_url(query: str, lang: str, country_code: str) -> str:
    encoded = quote_plus(query)
    return (
        f"https://news.google.com/rss/search?q={encoded}"
        f"&hl={lang}&gl={country_code}&ceid={country_code}:{lang}"
    )


def _is_recent(entry, lookback_hours=None) -> bool:
    hours = lookback_hours or LOOKBACK_HOURS
    published = entry.get("published_parsed")
    if not published:
        return True
    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return pub_dt >= cutoff


def _fetch_query(query: str, org_name: str, seen_urls: set,
                 languages: list, country_code: str) -> list:
    articles = []
    for lang in languages:
        url = _build_rss_url(query, lang, country_code)
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[scanner] RSS error '{query}' ({lang}): {e}")
            continue
        for entry in feed.entries:
            link = entry.get("link", "")
            if link in seen_urls or not _is_recent(entry):
                continue
            seen_urls.add(link)
            articles.append({
                "org_name":  org_name,
                "title":     entry.get("title", ""),
                "link":      link,
                "summary":   entry.get("summary", ""),
                "published": entry.get("published", ""),
                "source":    entry.get("source", {}).get("title", ""),
                "lang":      lang,
            })
    return articles


def fetch_all_articles(organizations: list, keywords: dict,
                       languages: list = None, country_code: str = "PE") -> list:
    if languages is None:
        languages = ["es", "en", "he"]

    seen_urls = set()
    all_articles = []

    search_queries = keywords.get("search_queries", [])
    print(f"[scanner] {len(search_queries)} keyword queries | langs={languages} | country={country_code}")

    for query in search_queries:
        results = _fetch_query(query, "General", seen_urls, languages, country_code)
        if results:
            print(f"[scanner]   '{query}' → {len(results)}")
        all_articles.extend(results)

    print(f"[scanner] Keyword total: {len(all_articles)}")

    for org in organizations:
        name = org.get("name", "")
        if not name or (" " not in name and len(name) <= 12):
            continue
        country = org.get("country", "Peru")
        print(f"[scanner] Org: {name}")
        results = _fetch_query(f"{name} {country}", name, seen_urls, languages, country_code)
        print(f"[scanner]   → {len(results)}")
        all_articles.extend(results)

    return all_articles
