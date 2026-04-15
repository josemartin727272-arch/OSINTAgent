"""
scanner.py — Fetches articles from Google News RSS.
Reads country/language settings dynamically.
"""

import feedparser
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus

from config import LOOKBACK_HOURS


# ── Social media targets (Peru pro-Palestine accounts) ──────────────────────

INSTAGRAM_ACCOUNTS = [
    "unmsmporpalestina",
    "bdsperu",
    "estudiantesporpalestina.pe",
    "antidotoeditorial",
    "voluntarios_por_palestina_peru",
    "cusco_conpalestina",
    "federacionpalestinaperu",
    "los.ronderos.de.las.redes",
    "pucpxpalestina",
    "cspalestinape",
    "juventudcomunistadelperu",
    "marearojaperu",
    "jcpr.myd",
    "gofmperu",
]

FACEBOOK_PAGES = [
    "Voluntarios por Palestina Perú",
    "Apoyo al pueblo de Palestina",
    "BDS Peruano",
    "apoyo al odio contra israel",
    "Palestina Libre PERU",
    "Cadena de Noticias Palestina Perú",
    "Palestina en Perú",
    "Peruanos Solidarios Con Palestina",
    "BDS Perú",
]

SOCIAL_KEYWORD_QUERIES = [
    "Facebook Palestine Peru protesta",
    "Instagram Palestine Peru manifestación",
    "redes sociales Israel Peru boicot",
    "publicación viral Peru Palestina",
    "Facebook Peru BDS",
]


def _build_rss_url(query: str, lang: str, country_code: str,
                   country_filter: bool = True, country_name: str = None) -> str:
    if country_filter and country_name and country_name.lower() not in query.lower():
        query = f"{query} {country_name}"
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
                 languages: list, country_code: str,
                 country_filter: bool = True, country_name: str = None) -> list:
    articles = []
    for lang in languages:
        url = _build_rss_url(query, lang, country_code, country_filter, country_name)
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


def fetch_social_media_orgs(seen_urls: set, languages: list,
                            country_code: str, country_name: str = "Peru") -> list:
    """Scan Google News for mentions of known pro-Palestine social accounts in the target country."""
    articles = []

    for handle in INSTAGRAM_ACCOUNTS:
        query = f"{handle} Instagram {country_name}"
        results = _fetch_query(query, handle, seen_urls, languages, country_code,
                               country_filter=False, country_name=country_name)
        if results:
            print(f"[scanner] IG '{handle}' → {len(results)}")
        articles.extend(results)

    for page in FACEBOOK_PAGES:
        query = f"{page} Facebook {country_name}"
        results = _fetch_query(query, page, seen_urls, languages, country_code,
                               country_filter=False, country_name=country_name)
        if results:
            print(f"[scanner] FB '{page}' → {len(results)}")
        articles.extend(results)

    print(f"[scanner] Social media total: {len(articles)}")
    return articles


def fetch_all_articles(organizations: list, keywords: dict,
                       languages: list = None, country_code: str = "PE",
                       country_name: str = "Peru") -> list:
    if languages is None:
        languages = ["es", "en", "he"]

    seen_urls = set()
    all_articles = []

    search_queries = keywords.get("search_queries", [])
    print(f"[scanner] {len(search_queries)} keyword queries | langs={languages} "
          f"| country={country_name} ({country_code})")

    for query in search_queries:
        results = _fetch_query(query, "General", seen_urls, languages, country_code,
                               country_filter=True, country_name=country_name)
        if results:
            print(f"[scanner]   '{query}' → {len(results)}")
        all_articles.extend(results)

    print(f"[scanner] Keyword total: {len(all_articles)}")

    # Social-media oriented keyword queries
    for query in SOCIAL_KEYWORD_QUERIES:
        results = _fetch_query(query, "Social", seen_urls, languages, country_code,
                               country_filter=False, country_name=country_name)
        if results:
            print(f"[scanner]   [social-kw] '{query}' → {len(results)}")
        all_articles.extend(results)

    # Direct social-media account scans
    social = fetch_social_media_orgs(seen_urls, languages, country_code, country_name)
    all_articles.extend(social)

    for org in organizations:
        name = org.get("name", "")
        if not name or (" " not in name and len(name) <= 12):
            continue
        country = org.get("country", country_name)
        print(f"[scanner] Org: {name}")
        results = _fetch_query(f"{name} {country}", name, seen_urls, languages, country_code,
                               country_filter=False, country_name=country)
        print(f"[scanner]   → {len(results)}")
        all_articles.extend(results)

    return all_articles
