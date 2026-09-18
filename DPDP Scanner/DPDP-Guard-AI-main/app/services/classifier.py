import asyncio
import json
from app.services.llm_service import call_llm

VALID_CATEGORIES = {
    "ecommerce", "finance", "education", "healthcare", "government",
    "social_media", "travel", "entertainment", "saas", "news_media",
    "insurance", "other",
}

_SYSTEM_PROMPT = """You are a website classification expert.
Classify the website strictly based on the crawled evidence provided.
Do NOT classify based on the domain name or URL alone.

Respond with a JSON object in this exact format:
{
    "category": "<category>",
    "confidence": <float 0.0 to 1.0>,
    "reason": "<one sentence citing specific evidence from the crawled data>"
}

Valid categories: ecommerce, finance, education, healthcare, government, social_media, travel, entertainment, saas, news_media, insurance, other"""


def _extract_evidence(crawler_data: dict) -> dict:
    pages = crawler_data.get("pages", [])

    page_titles = []
    page_texts = []
    privacy_policy = ""

    for page in pages:
        title = page.get("title", "")
        content = page.get("content", "")
        name = page.get("name", "")

        if title:
            page_titles.append(title)

        if content:
            page_texts.append(
                f"Page: {name}\n"
                f"Title: {title}\n"
                f"Content: {content}"
            )

        # Identify the privacy policy page
        if "privacy" in name.lower() or "privacy" in title.lower():
            privacy_policy += content + "\n"

    return {
        "url": crawler_data.get("website", ""),
        "title": page_titles[0] if page_titles else "",
        "description": "",
        "page_titles": page_titles,
        "page_text": "\n\n".join(page_texts)[:3000],
        "forms": [],
        "products_services": [],
        "personal_data_collected": [],
        "cookies": [],
        "consent_mechanisms": [],
        "privacy_policy": privacy_policy[:5000],
    }


def _classify_deterministically(crawler_data: dict) -> dict:
    url = str(crawler_data.get("website", "")).lower()
    page_texts = []
    for p in crawler_data.get("pages", []):
        page_texts.append(str(p.get("title", "")).lower())
        page_texts.append(str(p.get("name", "")).lower())
        page_texts.append(str(p.get("content", ""))[:500].lower())
    combined = (url + " " + " ".join(page_texts)).lower()

    if any(k in url for k in (".gov.in", ".nic.in")) or any(k in combined for k in ("passport seva", "government of india", "ministry of")):
        return {"category": "government", "confidence": 0.85, "reason": "Deterministic classification: Government domain / keywords identified (Gemini fallback)."}
    if any(k in url for k in (".edu", ".ac.in")) or any(k in combined for k in ("college", "university", "admissions", "academics", "institution")):
        return {"category": "education", "confidence": 0.85, "reason": "Deterministic classification: Educational institution domain / academic keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("shopping", "wishlist", "bag", "cart", "checkout", "add to cart", "myntra", "flipkart", "nike", "return policy", "order tracking")):
        return {"category": "ecommerce", "confidence": 0.85, "reason": "Deterministic classification: E-commerce shopping / cart / product keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("netflix", "streaming", "watch movies", "tv shows", "entertainment")):
        return {"category": "entertainment", "confidence": 0.80, "reason": "Deterministic classification: Entertainment / media streaming keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("insurance", "policyholder", "premium")):
        return {"category": "insurance", "confidence": 0.80, "reason": "Deterministic classification: Insurance keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("banking", "bank", "credit card", "loan", "investment", "financial")):
        return {"category": "finance", "confidence": 0.80, "reason": "Deterministic classification: Financial / banking keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("hospital", "clinic", "patient", "healthcare", "medical")):
        return {"category": "healthcare", "confidence": 0.80, "reason": "Deterministic classification: Healthcare keywords identified (Gemini fallback)."}
    if any(k in combined for k in ("software as a service", "api", "cloud platform", "developer documentation")):
        return {"category": "saas", "confidence": 0.75, "reason": "Deterministic classification: SaaS / software keywords identified (Gemini fallback)."}

    return {"category": "other", "confidence": 0.50, "reason": "Deterministic fallback: General website category assigned (Gemini fallback)."}


async def classify_website(crawler_data: dict) -> dict:
    det = _classify_deterministically(crawler_data)
    if det.get("confidence", 0.0) >= 0.80:
        return det

    evidence = _extract_evidence(crawler_data)
    user_prompt = f"Crawled website evidence:\n{json.dumps(evidence, indent=2)}"

    try:
        result = await asyncio.wait_for(call_llm(_SYSTEM_PROMPT, user_prompt), timeout=5.0)
        category = result.get("category", "other")
        if category not in VALID_CATEGORIES:
            category = "other"

        return {
            "category": category,
            "confidence": float(result.get("confidence", 0.0)),
            "reason": result.get("reason", ""),
        }
    except Exception as exc:
        print(f"Gemini website classification skipped or timed out ({exc}); using deterministic classification.")
        return det
