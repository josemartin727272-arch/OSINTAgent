"""
analyzer.py — Keyword-based article scoring with multi-country support.
"""

LOCATION_KEYWORDS = {
    "Peru":      ["Perú", "Peru", "Lima", "peruano", "peruanos", "peruana", "peruanas", "פרו", "Cusco", "Arequipa"],
    "Argentina": ["Argentina", "Buenos Aires", "porteño", "argentino"],
    "Chile":     ["Chile", "Santiago", "chileno", "chilena"],
    "Colombia":  ["Colombia", "Bogotá", "Medellín", "colombiano"],
    "Mexico":    ["México", "Mexico", "Ciudad de México", "mexicano"],
    "Brazil":    ["Brasil", "Brazil", "São Paulo", "Brasília", "brasileiro"],
    "Spain":     ["España", "Spain", "Madrid", "Barcelona", "español"],
    "United States": ["United States", "USA", "New York", "Los Angeles", "Washington"],
    "United Kingdom": ["United Kingdom", "UK", "London", "Britain", "British"],
    "Germany":   ["Deutschland", "Germany", "Berlin", "München", "deutsch"],
    "France":    ["France", "Paris", "français", "française"],
}

CITY_KEYWORDS = {
    "Peru":      ["Lima", "Cusco", "Arequipa", "Trujillo", "Piura", "Iquitos", "Huancayo", "Puno", "Chiclayo"],
    "Argentina": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "Tucumán"],
    "Chile":     ["Santiago", "Valparaíso", "Concepción", "Antofagasta"],
    "Colombia":  ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena"],
    "Mexico":    ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana"],
    "Brazil":    ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"],
    "Spain":     ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao"],
    "United States": ["New York", "Los Angeles", "Chicago", "Houston", "Miami", "Washington"],
    "United Kingdom": ["London", "Manchester", "Birmingham", "Edinburgh", "Liverpool"],
    "Germany":   ["Berlin", "München", "Hamburg", "Frankfurt", "Köln"],
    "France":    ["Paris", "Lyon", "Marseille", "Toulouse", "Nice"],
}

EVENT_TYPES = {
    "demonstration": ["manifestación", "marcha", "protesta", "concentración",
                      "movilización", "demonstration", "protest", "march", "rally",
                      "הפגנה", "עצרת"],
    "boycott":       ["boicot", "boycott", "BDS", "חרם"],
    "violence":      ["ataque", "violencia", "amenaza", "attack", "violence", "threat", "אלימות", "איום"],
    "online_campaign": ["campaña", "campaign", "redes sociales", "publicación", "קמפיין"],
    "statement":     ["declaración", "denuncia", "condena", "statement", "condemn", "גינוי", "הצהרה"],
}

EVENT_TYPE_LABELS = {
    "he": {
        "demonstration":   "🪧 הפגנה / עצרת",
        "boycott":         "🚫 קריאה לחרם",
        "violence":        "⚠️ אירוע אלים / איום",
        "online_campaign": "📱 קמפיין ברשת",
        "statement":       "📢 הצהרה / גינוי",
        "other":           "📌 אירוע כללי",
        "none":            "—",
    },
    "en": {
        "demonstration":   "🪧 Demonstration / Rally",
        "boycott":         "🚫 Boycott / BDS",
        "violence":        "⚠️ Violence / Threat",
        "online_campaign": "📱 Online Campaign",
        "statement":       "📢 Statement / Condemnation",
        "other":           "📌 General Event",
        "none":            "—",
    },
    "es": {
        "demonstration":   "🪧 Manifestación / Marcha",
        "boycott":         "🚫 Boicot / BDS",
        "violence":        "⚠️ Violencia / Amenaza",
        "online_campaign": "📱 Campaña en redes",
        "statement":       "📢 Declaración / Condena",
        "other":           "📌 Evento general",
        "none":            "—",
    },
}


def _text(article: dict) -> str:
    return (article.get("title", "") + " " + article.get("summary", "")).lower()


def _count(text: str, keywords: list) -> int:
    score = 0
    for kw in keywords:
        words = kw.lower().split()
        if len(words) == 1:
            if words[0] in text:
                score += 1
        else:
            if all(w in text for w in words):
                score += 1
    return score


def _detect_event_type(text: str) -> str:
    for etype, keywords in EVENT_TYPES.items():
        if any(kw.lower() in text for kw in keywords):
            return etype
    return "other"


def _detect_location(text: str, country: str) -> str:
    cities = CITY_KEYWORDS.get(country, [])
    for city in cities:
        if city.lower() in text:
            return city
    country_kws = LOCATION_KEYWORDS.get(country, [country])
    if any(kw.lower() in text for kw in country_kws):
        return country
    return None


def get_event_label(event_type: str, lang: str = "he") -> str:
    return EVENT_TYPE_LABELS.get(lang, EVENT_TYPE_LABELS["en"]).get(event_type, event_type)


def analyze_article(article: dict, keywords: dict, country: str = "Peru",
                    threshold: int = 6) -> dict:
    text = _text(article)
    country_kws = LOCATION_KEYWORDS.get(country, [country])

    high   = _count(text, keywords.get("high", []))   * 3
    medium = _count(text, keywords.get("medium", [])) * 2
    low    = _count(text, keywords.get("low", []))    * 1
    country_bonus = 2 if any(kw.lower() in text for kw in country_kws) else 0

    score      = min(10, high + medium + low + country_bonus)
    event_type = _detect_event_type(text) if score > 0 else "none"
    location   = _detect_location(text, country)

    return {
        **article,
        "relevance_score": score,
        "event_type":      event_type,
        "event_date":      None,
        "location":        location,
        "summary_en": f"{article.get('title','')} (Source: {article.get('source','')}). Score: {score}/10.",
        "summary_he": f"זוהה {get_event_label(event_type,'he')} במיקום: {location or 'לא ידוע'}. כותרת: {article.get('title','')}",
        "is_alert":   score >= threshold,
    }


def analyze_all(articles: list, keywords: dict, country: str = "Peru",
                threshold: int = 6) -> list:
    results = []
    for i, article in enumerate(articles):
        enriched = analyze_article(article, keywords, country, threshold)
        score = enriched.get("relevance_score", 0)
        print(f"[analyzer] {i+1}/{len(articles)} score={score}: {article.get('title','')[:60]}")
        if score > 0:
            results.append(enriched)
    return results
