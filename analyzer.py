"""
analyzer.py — Keyword-based article scoring.
Keywords and weights are loaded from the Keywords sheet in Google Sheets.
"""

from config import COUNTRY, ALERT_THRESHOLD

PERU_KEYWORDS = [
    "Perú", "Peru", "Lima", "peruano", "peruanos",
    "peruana", "peruanas", "פרו",
]

EVENT_TYPES = {
    "demonstration": ["manifestación", "marcha", "protesta", "concentración",
                      "movilización", "demonstration", "protest", "march", "rally",
                      "הפגנה", "עצרת"],
    "boycott":       ["boicot", "boycott", "BDS", "חרם"],
    "violence":      ["ataque", "violencia", "amenaza", "attack", "violence", "threat"],
    "online_campaign": ["campaña", "campaign", "redes sociales", "publicación"],
    "statement":     ["declaración", "denuncia", "condena", "statement", "condemn"],
}

EVENT_TYPE_HE = {
    "demonstration":   "הפגנה / עצרת",
    "boycott":         "קריאה לחרם",
    "violence":        "אירוע אלים / איום",
    "online_campaign": "קמפיין ברשת",
    "statement":       "הצהרה / גינוי",
    "other":           "אירוע כללי",
}


def _text(article: dict) -> str:
    return (article.get("title", "") + " " + article.get("summary", "")).lower()


def _count(text: str, keywords: list) -> int:
    return sum(1 for kw in keywords if kw.lower() in text)


def _detect_event_type(text: str) -> str:
    for etype, keywords in EVENT_TYPES.items():
        if any(kw.lower() in text for kw in keywords):
            return etype
    return "other"


def _detect_location(text: str) -> str | None:
    cities = ["Lima", "Cusco", "Arequipa", "Trujillo", "Piura",
              "Iquitos", "Huancayo", "Puno", "Chiclayo"]
    for city in cities:
        if city.lower() in text:
            return city
    if any(kw.lower() in text for kw in PERU_KEYWORDS):
        return "Peru"
    return None


def analyze_article(article: dict, keywords: dict) -> dict:
    text = _text(article)

    high   = _count(text, keywords.get("high", []))   * 3
    medium = _count(text, keywords.get("medium", [])) * 2
    low    = _count(text, keywords.get("low", []))    * 1
    peru_bonus = 2 if any(kw.lower() in text for kw in PERU_KEYWORDS) else 0

    score      = min(10, high + medium + low + peru_bonus)
    event_type = _detect_event_type(text) if score > 0 else "none"
    location   = _detect_location(text)

    event_he = EVENT_TYPE_HE.get(event_type, "אירוע")
    loc_str  = f"במיקום: {location}" if location else "מיקום לא ידוע"

    return {
        **article,
        "relevance_score": score,
        "event_type":      event_type,
        "event_date":      None,
        "location":        location,
        "summary_en":      f"{article.get('title','')} (Source: {article.get('source','')}). Score: {score}/10.",
        "summary_he":      f"זוהה {event_he} {loc_str}. כותרת: {article.get('title','')}",
        "is_alert":        score >= ALERT_THRESHOLD,
    }


def analyze_all(articles: list[dict], keywords: dict) -> list[dict]:
    results = []
    for i, article in enumerate(articles):
        enriched = analyze_article(article, keywords)
        score = enriched.get("relevance_score", 0)
        print(f"[analyzer] {i+1}/{len(articles)} score={score}: {article.get('title','')[:60]}")
        if score > 0:
            results.append(enriched)
    return results
