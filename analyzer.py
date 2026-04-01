"""
analyzer.py — Analyzes articles with Gemini API to score relevance and extract insights.
"""

import json
import google.generativeai as genai

from config import GEMINI_API_KEY, COUNTRY, ALERT_THRESHOLD

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-1.5-flash")  # free tier model

ANALYSIS_PROMPT = """
You are an intelligence analyst monitoring organizational activity in {country}.

Analyze the following news article and return a JSON object with these fields:
- "relevance_score": integer 0-10 (10 = highly relevant hostile/anti-Israel activity, 0 = not relevant)
- "event_type": one of ["demonstration", "boycott", "statement", "violence", "online_campaign", "other", "none"]
- "event_date": ISO date string if mentioned, else null
- "location": specific city/place in {country} if mentioned, else null
- "summary_he": 2-sentence summary in Hebrew
- "summary_en": 2-sentence summary in English
- "is_alert": true if relevance_score >= {threshold}

Relevance criteria (score 7-10):
- Planned or recent protest/demonstration against Israel or Jewish community in {country}
- Calls for boycotts of Israeli goods/institutions in {country}
- Antisemitic incidents or statements by the organization
- Violence or threats against Jewish/Israeli targets in {country}

Score 4-6: General anti-Israel statements, international campaigns with {country} participation
Score 0-3: Unrelated content, general news not involving the organization's anti-Israel activity

Article:
Title: {title}
Source: {source}
Published: {published}
Content: {summary}

Return ONLY valid JSON, no markdown, no explanation.
"""


def analyze_article(article: dict) -> dict:
    """
    Send article to Gemini for analysis. Returns enriched article dict.
    """
    prompt = ANALYSIS_PROMPT.format(
        country=COUNTRY,
        threshold=ALERT_THRESHOLD,
        title=article.get("title", ""),
        source=article.get("source", ""),
        published=article.get("published", ""),
        summary=article.get("summary", "")[:2000],  # cap to avoid token limits
    )

    try:
        response = _model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code blocks if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        analysis = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[analyzer] JSON parse error: {e}")
        analysis = {
            "relevance_score": 0,
            "event_type": "none",
            "event_date": None,
            "location": None,
            "summary_he": "",
            "summary_en": "",
            "is_alert": False,
        }
    except Exception as e:
        print(f"[analyzer] Gemini error: {e}")
        analysis = {
            "relevance_score": 0,
            "event_type": "none",
            "event_date": None,
            "location": None,
            "summary_he": "",
            "summary_en": "",
            "is_alert": False,
        }

    return {**article, **analysis}


def analyze_all(articles: list[dict]) -> list[dict]:
    """Analyze a list of articles. Returns only those with relevance_score > 0."""
    results = []
    for i, article in enumerate(articles):
        print(f"[analyzer] Analyzing {i+1}/{len(articles)}: {article.get('title', '')[:60]}")
        enriched = analyze_article(article)
        if enriched.get("relevance_score", 0) > 0:
            results.append(enriched)
    return results
