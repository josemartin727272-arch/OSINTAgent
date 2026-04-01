"""
analyzer.py — Keyword-based article scoring (no external API needed).
Scores articles based on presence of relevant keywords in title/summary.
"""

from config import COUNTRY, ALERT_THRESHOLD

# Keywords by category and weight
HIGH_WEIGHT = [
    # Demonstrations/events
    "manifestación", "marcha", "protesta", "concentración", "movilización",
    "demonstration", "protest", "march", "rally",
    "הפגנה", "עצרת", "מחאה",
    # Boycott
    "boicot", "boycott", "BDS", "חרם",
    # Antisemitism
    "antisemitismo", "antisemita", "antisemitism", "אנטישמיות",
    # Violence/threats
    "amenaza", "ataque", "violencia", "threat", "attack",
    "איום", "תקיפה",
]

MEDIUM_WEIGHT = [
    # General anti-Israel
    "contra Israel", "anti-Israel", "anti Israel",
    "against Israel", "נגד ישראל",
    # Palestine solidarity
    "Palestina libre", "Free Palestine", "Palestina",
    "פלסטין", "עזה", "Gaza",
    # Calls to action
    "convoca", "llama", "exige", "denuncia",
    "calls for", "demands", "condemns",
]

LOW_WEIGHT = [
    # General mentions
    "Israel", "palestino", "palestina", "Palestinian",
    "Gaza", "ocupación", "occupation",
    "Medio Oriente", "Middle East",
]

# Location keywords (article must mention Peru to be most relevant)
PERU_KEYWORDS = [
    "Perú", "Peru", "Lima", "peruano", "peruanos",
    "peruana", "peruanas", "פרו",
]

EVENT_TYPES = {
    "demonstration": ["manifestación", "marcha", "protesta", "concentración",
                      "movilización", "demonstration", "protest", "march", "rally",
                      "הפגנה", "עצרת"],
    "boycott": ["boicot", "boycott", "BDS", "חרם"],
    "violence": ["ataque", "violencia", "amenaza", "attack", "violence", "threat"],
    "online_campaign": ["campaña", "campaign", "publicación", "post", "redes sociales"],
    "statement": ["declaración", "denuncia", "condena", "statement", "condemn"],
}


def _text(article: dict) -> str:
    """Combine title and summary for analysis."""
    return (article.get("title", "") + " " + article.get("summary", "")).lower()


def _count_keywords(text: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw.lower() in text)


def _detect_event_type(text: str) -> str:
    for event_type, keywords in EVENT_TYPES.items():
        if any(kw.lower() in text for kw in keywords):
            return event_type
    return "other"


def _detect_location(text: str) -> str | None:
    locations = ["Lima", "Cusco", "Arequipa", "Trujillo", "Piura",
                 "Iquitos", "Huancayo", "Puno", "Chiclayo"]
    for loc in locations:
        if loc.lower() in text:
            return loc
    if any(kw.lower() in text for kw in PERU_KEYWORDS):
        return "Peru"
    return None


def _build_summary_en(article: dict, score: int) -> str:
    title = article.get("title", "")
    source = article.get("source", "")
    return f"{title} (Source: {source}). Relevance score: {score}/10."


def _build_summary_he(article: dict, event_type: str, location: str) -> str:
    title = article.get("title", "")
    loc_str = f"במיקום: {location}" if location else "מיקום לא ידוע"
    event_str = {
        "demonstration": "הפגנה/עצרת",
        "boycott": "קריאה לחרם",
        "violence": "אירוע אלים/איום",
        "online_campaign": "קמפיין ברשת",
        "statement": "הצהרה/גינוי",
        "other": "אירוע",
    }.get(event_type, "אירוע")
    return f"זוהה {event_str} {loc_str}. כותרת: {title}"


def analyze_article(article: dict) -> dict:
    text = _text(article)

    # Score calculation
    high = _count_keywords(text, HIGH_WEIGHT) * 3
    medium = _count_keywords(text, MEDIUM_WEIGHT) * 2
    low = _count_keywords(text, LOW_WEIGHT) * 1

    # Peru bonus — article mentioning Peru is more relevant
    peru_bonus = 2 if any(kw.lower() in text for kw in PERU_KEYWORDS) else 0

    raw_score = high + medium + low + peru_bonus
    # Normalize to 0-10
    score = min(10, raw_score)

    event_type = _detect_event_type(text) if score > 0 else "none"
    location = _detect_location(text)

    return {
        **article,
        "relevance_score": score,
        "event_type": event_type,
        "event_date": None,
        "location": location,
        "summary_en": _build_summary_en(article, score),
        "summary_he": _build_summary_he(article, event_type, location),
        "is_alert": score >= ALERT_THRESHOLD,
    }


def analyze_all(articles: list[dict]) -> list[dict]:
    results = []
    for i, article in enumerate(articles):
        title = article.get("title", "")[:60]
        enriched = analyze_article(article)
        score = enriched.get("relevance_score", 0)
        print(f"[analyzer] {i+1}/{len(articles)} score={score}: {title}")
        if score > 0:
            results.append(enriched)
    return results
