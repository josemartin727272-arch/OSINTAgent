"""
analyzer.py — Keyword-based article scoring with multi-country support.
"""

import re
from collections import Counter

_WORD_RE = re.compile(r"[\wáéíóúñüÁÉÍÓÚÑÜ]{4,}", re.UNICODE)

_STOPWORDS = {
    "para", "pero", "como", "porque", "cuando", "donde", "sobre", "entre",
    "this", "that", "with", "from", "have", "were", "their", "they", "them",
    "sobre", "hacia", "desde", "hasta", "según", "aunque",
    "está", "esta", "este", "estos", "estas",
    "tras", "dice", "dijo", "dicen", "video", "noticia", "noticias",
    "peru", "perú", "lima", "israel", "palestina", "palestine",
}

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
    "Peru":      ["Lima", "Cusco", "Arequipa", "Trujillo", "Piura",
                  "Iquitos", "Huancayo", "Puno", "Chiclayo", "Tacna",
                  "Juliaca", "Ayacucho", "Cajamarca", "Ica", "Huaraz",
                  "Moquegua", "Tumbes", "Pucallpa", "Tarapoto", "Chimbote"],
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

GLOBAL_CITIES = [
    "London", "Paris", "Berlin", "Madrid", "Rome",
    "New York", "Washington", "Sydney", "Toronto",
    "Amsterdam", "Brussels", "Stockholm", "Oslo",
]

MASS_EVENT_KEYWORDS = [
    "thousands", "hundreds of thousands", "massive", "huge rally",
    "miles de", "masiva", "gran marcha", "multitudinaria",
    "embassy", "embajada", "שגרירות",
]


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


def _is_peru_relevant(text: str, country: str = "Peru") -> bool:
    """False if the article text does not mention the target country at all."""
    country_kws = LOCATION_KEYWORDS.get(country, [country])
    return any(kw.lower() in text for kw in country_kws)


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


def _build_summary_by_lang(article: dict, event_type: str,
                           location: str, lang: str = "he") -> str:
    title = article.get("title", "")
    loc = location or "—"
    if lang == "he":
        return f"זוהה {get_event_label(event_type, 'he')} במיקום: {loc}. כותרת: {title}"
    if lang == "es":
        return f"Detectado {get_event_label(event_type, 'es')} en: {loc}. Título: {title}"
    return f"Detected {get_event_label(event_type, 'en')} in: {loc}. Title: {title}"


def _build_summary_en(article: dict, event_type: str,
                      location: str, score: int) -> str:
    title = article.get("title", "")
    source = article.get("source", "")
    loc = location or "unknown"
    return f"{get_event_label(event_type, 'en')} in {loc}. {title} (Source: {source}, Score: {score}/10)"


def _title_words(record: dict) -> list:
    title = str(record.get("title", "")).lower()
    return [w for w in _WORD_RE.findall(title) if w not in _STOPWORDS]


def build_feedback_boost(rated_results: list, low_rated_results: list = None) -> dict:
    """Extract boost/penalty signals from user star ratings."""
    low_rated_results = low_rated_results or []

    word_counter = Counter()
    org_counter  = Counter()
    loc_counter  = Counter()
    for r in rated_results:
        word_counter.update(_title_words(r))
        org = str(r.get("org_name", "")).strip()
        if org:
            org_counter[org] += 1
        loc = str(r.get("location", "")).strip()
        if loc:
            loc_counter[loc] += 1

    low_words = Counter()
    for r in low_rated_results:
        low_words.update(_title_words(r))

    boosted_keywords = {w for w, c in word_counter.items() if c >= 2}
    low_patterns     = {w for w, c in low_words.items() if c >= 2} - boosted_keywords

    return {
        "boosted_keywords":    boosted_keywords,
        "high_value_orgs":     {o for o in org_counter},
        "preferred_locations": {l for l in loc_counter},
        "low_rated_patterns":  low_patterns,
    }


def _matches_low_rated_pattern(text: str, patterns: set) -> bool:
    if not patterns:
        return False
    hits = sum(1 for p in patterns if p in text)
    return hits >= 2


def _detect_org(text: str, organizations: list) -> str:
    """Return the name of the first organization whose name or keyword appears in the text."""
    text_lower = text.lower()
    for org in organizations or []:
        name = str(org.get("name", "")).strip()
        if not name or len(name) < 4:
            continue
        if name.lower() in text_lower:
            return name
        raw_kws = org.get("keywords", [])
        if isinstance(raw_kws, list):
            kws = raw_kws
        else:
            kws = [k.strip() for k in str(raw_kws).split(",") if k.strip()]
        for kw in kws:
            if len(kw) > 4 and kw.lower() in text_lower:
                return name
    return ""


def _detect_global_location(text: str) -> str:
    for city in GLOBAL_CITIES:
        if city.lower() in text:
            return city
    return None


def analyze_article(article: dict, keywords: dict, country: str = "Peru",
                    threshold: int = 6, feedback: dict = None,
                    organizations: list = None) -> dict:
    text = _text(article)
    is_global = article.get("org_name") == "🌍 Global"

    detected_org = article.get("org_name", "") or ""
    if not is_global and detected_org in ("", "General") and organizations:
        match = _detect_org(text, organizations)
        if match:
            detected_org = match
            article = {**article, "org_name": detected_org}

    if not is_global and not _is_peru_relevant(text, country):
        return {
            **article,
            "relevance_score": 0,
            "event_type":      "none",
            "event_date":      None,
            "location":        None,
            "summary_en":      "",
            "summary_he":      "",
            "summary_es":      "",
            "is_alert":        False,
            "is_global":       False,
        }

    country_kws = LOCATION_KEYWORDS.get(country, [country])

    high   = _count(text, keywords.get("high", []))   * 3
    medium = _count(text, keywords.get("medium", [])) * 2
    low    = _count(text, keywords.get("low", []))    * 1
    keyword_score = high + medium + low
    country_bonus = 2 if any(kw.lower() in text for kw in country_kws) else 0

    if is_global:
        global_bonus = 2 if any(kw in text for kw in MASS_EVENT_KEYWORDS) else 0
        score = keyword_score + global_bonus
    else:
        score = keyword_score + country_bonus

    if feedback:
        high_value_orgs    = feedback.get("high_value_orgs", set())
        boosted_keywords   = feedback.get("boosted_keywords", set())
        low_rated_patterns = feedback.get("low_rated_patterns", set())

        if article.get("org_name") in high_value_orgs:
            score += 2

        boost_hits = sum(1 for kw in boosted_keywords if kw in text)
        if boost_hits:
            score += min(2, boost_hits)

        if _matches_low_rated_pattern(text, low_rated_patterns):
            score = max(0, score - 2)

    score      = min(10, score)
    event_type = _detect_event_type(text) if score > 0 else "none"
    location   = _detect_global_location(text) if is_global else _detect_location(text, country)

    return {
        **article,
        "relevance_score": score,
        "event_type":      event_type,
        "event_date":      None,
        "location":        location,
        "summary_en": _build_summary_en(article, event_type, location, score),
        "summary_he": _build_summary_by_lang(article, event_type, location, "he"),
        "summary_es": _build_summary_by_lang(article, event_type, location, "es"),
        "is_alert":   score >= threshold,
        "is_global":  is_global,
    }


def analyze_all(articles: list, keywords: dict, country: str = "Peru",
                threshold: int = 6, feedback: dict = None,
                organizations: list = None) -> list:
    results = []
    for i, article in enumerate(articles):
        enriched = analyze_article(article, keywords, country, threshold,
                                   feedback, organizations)
        score = enriched.get("relevance_score", 0)
        print(f"[analyzer] {i+1}/{len(articles)} score={score}: {article.get('title','')[:60]}")
        if score > 0:
            results.append(enriched)
    return results
