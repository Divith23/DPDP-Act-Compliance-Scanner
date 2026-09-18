"""Batched semantic evidence-discovery layer for the DPDP compliance scanner.

LLM #1 only identifies observable website evidence. It never decides
applicability or legal compliance.

This version batches incomplete requirements to reduce Gemini API calls and
adds requirement-specific semantic slices of the crawler data. This lets LLM
#1 recover evidence that deterministic pattern matching may have missed,
without sending the entire crawler payload for every requirement.
"""

import json
import re
from typing import Any

from app.services.llm_service import call_evidence_llm
from app.services.evidence_engine import (
    assess_requirement,
    build_llm_evidence_package,
)


MAX_DISCOVERY_EVIDENCE_CHARS = 900
MAX_SEMANTIC_SLICE_CHARS = 1400
BATCH_SIZE = 12


def _compact_text(value: Any, limit: int = MAX_DISCOVERY_EVIDENCE_CHARS) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return text[:head] + "\n...[omitted]...\n" + text[-tail:]


def _requirement_search_terms(requirement: dict) -> list[str]:
    """Build conservative search terms from the requirement itself."""
    raw_parts = [
        requirement.get("id", ""),
        requirement.get("title", ""),
        requirement.get("legal_reference", ""),
        requirement.get("requirement", ""),
    ]

    for element in requirement.get("assessment_elements", []):
        raw_parts.append(str(element))

    text = " ".join(str(x or "") for x in raw_parts).lower()

    # Useful multi-word concepts should remain intact.
    phrases = [
        "privacy policy",
        "privacy notice",
        "consent",
        "withdraw consent",
        "withdrawal",
        "grievance",
        "grievance officer",
        "data protection officer",
        "data protection board",
        "complaint",
        "personal data",
        "personal data breach",
        "security safeguard",
        "technical and organisational measures",
        "reasonable security safeguards",
        "retention period",
        "delete",
        "erasure",
        "correction",
        "access",
        "nominee",
        "child",
        "children",
        "parental consent",
        "language",
        "english",
        "eighth schedule",
        "automated",
        "profiling",
        "tracking",
        "monitoring",
        "behaviour",
        "marketing",
        "advertising",
        "contact",
        "email",
        "phone",
        "address",
        "terms of use",
        "cookie",
    ]

    terms: list[str] = []
    for phrase in phrases:
        if phrase in text:
            terms.append(phrase)

    # Add meaningful words from the requirement so the slice is not limited
    # to the fixed vocabulary above.
    words = re.findall(r"[a-z][a-z0-9_-]{3,}", text)
    stop = {
        "this", "that", "with", "from", "into", "must", "shall", "should",
        "where", "when", "have", "been", "being", "their", "they", "them",
        "only", "each", "such", "under", "section", "rule", "requirement",
        "means", "period", "provide", "provided", "public", "website",
        "data", "processing", "process", "applicable", "currently",
    }

    for word in words:
        if word not in stop and word not in terms and len(word) >= 5:
            terms.append(word)

    # Preserve order and cap prompt growth.
    return list(dict.fromkeys(terms))[:35]


def _score_text(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    score = 0

    for term in terms:
        if term in lowered:
            # Multi-word phrases are stronger signals.
            score += 3 if " " in term else 1

    return score


def _extract_relevant_window(
    text: str,
    terms: list[str],
    limit: int = 900,
) -> str:
    """Return a compact text window around the strongest matching terms."""
    text = str(text or "").strip()
    if not text:
        return ""

    if len(text) <= limit:
        return text

    lowered = text.lower()
    positions = []

    for term in terms:
        start = lowered.find(term.lower())
        if start >= 0:
            positions.append(start)

    if not positions:
        return text[:limit]

    center = positions[0]
    start = max(0, center - limit // 3)
    end = min(len(text), start + limit)

    if end - start < limit:
        start = max(0, end - limit)

    prefix = "...[context omitted]...\n" if start > 0 else ""
    suffix = "\n...[context omitted]..." if end < len(text) else ""

    return prefix + text[start:end].strip() + suffix


def _iter_crawler_fields(value: Any, path: str = ""):
    """Yield (field path, string value) pairs from nested crawler data."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _iter_crawler_fields(child, child_path)

    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield from _iter_crawler_fields(child, child_path)

    elif isinstance(value, (str, int, float, bool)):
        text = str(value).strip()
        if text:
            yield path, text


def _build_semantic_crawler_slice(
    requirement: dict,
    crawler_data: dict,
) -> dict:
    """Build a small requirement-specific view of crawler evidence.

    The full crawler payload can be very large. We therefore rank fields by
    overlap with the requirement and keep only the most relevant excerpts.
    This is evidence discovery only; the model still has to quote the source.
    """
    terms = _requirement_search_terms(requirement)

    candidates = []

    for path, value in _iter_crawler_fields(crawler_data):
        # Never expose Mongo internals as evidence.
        if path == "_id" or path.startswith("_id."):
            continue

        searchable = f"{path} {value}"
        score = _score_text(searchable, terms)

        # Structured compliance fields are valuable even when their exact
        # wording does not match the requirement.
        path_lower = path.lower()
        if any(
            marker in path_lower
            for marker in (
                "privacy", "consent", "grievance", "security", "breach",
                "retention", "rights", "child", "language", "contact",
                "ui", "form", "cookie", "page_text", "personal_data",
            )
        ):
            score += 2

        if score > 0:
            candidates.append((score, path, value))

    candidates.sort(key=lambda item: (-item[0], len(item[2])))

    selected = []
    used_paths = set()
    total_chars = 0

    for score, path, value in candidates:
        if path in used_paths:
            continue

        # Page content is usually huge, so extract a local window rather than
        # sending the complete page.
        excerpt = _extract_relevant_window(value, terms, limit=600)

        item = {
            "source_field": path,
            "relevance_score": score,
            "excerpt": excerpt,
        }

        item_chars = len(json.dumps(item, ensure_ascii=False))

        if selected and total_chars + item_chars > MAX_SEMANTIC_SLICE_CHARS:
            continue

        selected.append(item)
        used_paths.add(path)
        total_chars += item_chars

        if total_chars >= MAX_SEMANTIC_SLICE_CHARS:
            break

    # If no lexical match was found, expose a small set of likely high-value
    # structured fields. This gives the semantic model a recovery path.
    if not selected:
        fallback_markers = (
            "privacy", "consent", "grievance", "security", "breach",
            "retention", "rights", "child", "ui_information", "pages",
        )

        for path, value in _iter_crawler_fields(crawler_data):
            path_lower = path.lower()
            if any(marker in path_lower for marker in fallback_markers):
                selected.append({
                    "source_field": path,
                    "relevance_score": 0,
                    "excerpt": _compact_text(value, 500),
                })

                if len(selected) >= 5:
                    break

    return {
        "requirement_id": requirement.get("id"),
        "search_terms": terms[:20],
        "crawler_evidence": selected,
    }


def _compact_deterministic_package(package: dict) -> dict:
    """Keep only the element-level signals needed by LLM #1."""
    if not isinstance(package, dict):
        return {}

    return {
        "requirement_id": package.get("requirement_id"),
        "elements": [
            {
                "element": item.get("element"),
                "status": item.get("status"),
                "evidence": [str(x)[:500] for x in item.get("evidence", [])][:2],
                "source_fields": item.get("source_fields", [])[:4],
            }
            for item in package.get("elements", [])
            if isinstance(item, dict)
        ],
    }


def _build_batch_prompt(
    requirements: list[dict],
    deterministic_packages: dict[str, dict],
    semantic_slices: dict[str, dict] | None = None,
) -> str:
    compact_requirements = []

    for requirement in requirements:
        compact_requirements.append({
            "id": requirement.get("id"),
            "title": requirement.get("title"),
            "legal_reference": requirement.get("legal_reference"),
            "requirement": requirement.get("requirement"),
            "assessment_elements": requirement.get("assessment_elements", []),
        })

    compact_packages = {
        rid: _compact_deterministic_package(deterministic_packages.get(rid, {}))
        for rid in [r.get("id") for r in requirements]
    }

    compact_semantic_slices = {
        rid: (semantic_slices or {}).get(rid, {})
        for rid in [r.get("id") for r in requirements]
    }

    return f"""You are the EVIDENCE DISCOVERY model in a DPDP compliance scanner.

Your ONLY task is to identify observable evidence in the supplied crawler
evidence for EACH supplied requirement.

You are NOT deciding legal compliance.
You are NOT deciding applicability.
You are NOT allowed to invent, infer, or assume evidence.

Rules:
1. Use ONLY the supplied crawler evidence.
2. Analyze EVERY requirement in the batch.
3. Return exactly one result object for every supplied requirement ID.
4. Every FOUND or PARTIAL claim MUST quote or closely reproduce supporting text.
5. If the supplied evidence does not establish an element, return NOT_FOUND.
6. If an element concerns an internal process that cannot be established from a
   public website, return NOT_OBSERVABLE.
7. A generic privacy-policy statement must not be treated as proof of a specific
   operational mechanism unless the text explicitly describes it.
8. Distinguish an actual UI mechanism from merely mentioning that a mechanism
   exists in a policy.
9. Do not turn legal requirements into evidence merely because the requirement
   says something should exist.
10. Preserve crawler field names whenever possible.
11. Do not combine evidence from different requirements unless the same supplied
    evidence genuinely supports both.
12. Never manufacture an excerpt.
13. The SEMANTIC CRAWLER SLICE is a search aid, not proof by itself. Verify every
    claim against its supplied excerpt.
14. If an excerpt contains relevant evidence, quote the smallest useful passage.
15. Do not mark an element FOUND merely because a keyword appears. The excerpt
    must actually support the factual element.

Return STRICT JSON in exactly this shape:
{{
  "results": [
    {{
      "requirement_id": "...",
      "elements": [
        {{
          "element": "...",
          "status": "FOUND|PARTIAL|NOT_FOUND|NOT_OBSERVABLE",
          "evidence": ["exact supporting excerpt"],
          "source_fields": ["crawler field"],
          "reason": "short factual reason"
        }}
      ]
    }}
  ]
}}

=== REQUIREMENTS ===
{json.dumps(compact_requirements, indent=2, ensure_ascii=False)}

=== DETERMINISTIC EVIDENCE DETECTION ===
{json.dumps(compact_packages, indent=2, ensure_ascii=False)}

=== REQUIREMENT-SPECIFIC SEMANTIC CRAWLER EVIDENCE ===
{json.dumps(compact_semantic_slices, indent=2, ensure_ascii=False)}
"""


def _normalise_result(result: Any, requirement: dict) -> dict:
    if not isinstance(result, dict):
        return {
            "requirement_id": requirement["id"],
            "elements": [],
            "error": "Evidence discovery model returned invalid JSON structure.",
        }

    raw_elements = result.get("elements", [])
    if not isinstance(raw_elements, list):
        raw_elements = []

    allowed_elements = set(requirement.get("assessment_elements", []))
    cleaned = []

    for item in raw_elements:
        if not isinstance(item, dict):
            continue

        element = str(item.get("element", "")).strip()
        if not element or (allowed_elements and element not in allowed_elements):
            continue

        status = str(item.get("status", "NOT_FOUND")).upper()
        if status not in {"FOUND", "PARTIAL", "NOT_FOUND", "NOT_OBSERVABLE"}:
            status = "NOT_FOUND"

        evidence = item.get("evidence", [])
        if isinstance(evidence, str):
            evidence = [evidence]
        if not isinstance(evidence, list):
            evidence = []

        evidence = [
            _compact_text(x)
            for x in evidence
            if str(x).strip()
        ][:4]

        # A FOUND/PARTIAL result without evidence is not trustworthy.
        if status in {"FOUND", "PARTIAL"} and not evidence:
            status = "NOT_FOUND"

        source_fields = item.get("source_fields", [])
        if isinstance(source_fields, str):
            source_fields = [source_fields]
        if not isinstance(source_fields, list):
            source_fields = []

        source_fields = [str(x)[:100] for x in source_fields][:6]

        cleaned.append({
            "element": element,
            "status": status,
            "evidence": evidence,
            "source_fields": source_fields,
            "reason": _compact_text(item.get("reason", ""), 500),
        })

    return {
        "requirement_id": requirement["id"],
        "elements": cleaned,
    }


def _normalise_batch_result(
    result: Any,
    requirements: list[dict],
) -> dict[str, dict]:
    """Validate a batch response and return one result per known requirement."""

    by_id = {
        requirement["id"]: requirement
        for requirement in requirements
    }

    if not isinstance(result, dict):
        return {
            rid: {
                "requirement_id": rid,
                "elements": [],
                "error": "Batch evidence discovery returned invalid JSON structure.",
            }
            for rid in by_id
        }

    raw_results = result.get("results", [])
    if not isinstance(raw_results, list):
        raw_results = []

    output: dict[str, dict] = {}

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        rid = str(item.get("requirement_id", "")).strip()

        # Never accept an unexpected requirement ID.
        if rid not in by_id:
            continue

        if rid in output:
            continue

        output[rid] = _normalise_result(item, by_id[rid])

    # Always return an entry for every requested requirement.
    for rid, requirement in by_id.items():
        if rid not in output:
            output[rid] = {
                "requirement_id": rid,
                "elements": [],
                "error": "Batch response omitted this requirement.",
            }

    return output


async def discover_requirement_evidence(
    requirement: dict,
    crawler_data: dict,
) -> dict:
    """Run semantic evidence discovery for one requirement.

    Kept for compatibility with existing callers. New analysis should use the
    batched discover_incomplete_evidence() function below.
    """
    deterministic = assess_requirement(requirement["id"], crawler_data)
    package = build_llm_evidence_package(deterministic)
    semantic_slice = _build_semantic_crawler_slice(requirement, crawler_data)

    prompt = _build_batch_prompt(
        [requirement],
        {requirement["id"]: package},
        {requirement["id"]: semantic_slice},
    )

    result = await call_evidence_llm(
        "You are a strict evidence extraction model. Return JSON only.",
        prompt,
    )

    return _normalise_batch_result(result, [requirement])[requirement["id"]]


async def discover_incomplete_evidence(
    requirements: list[dict],
    crawler_data: dict,
    deterministic_assessments: dict[str, dict] | list[dict] | None = None,
) -> dict[str, dict]:
    """Discover semantic evidence for incomplete requirements in batches.

    Requirements whose deterministic evidence is already FOUND are skipped.
    The remaining requirements are processed in batches to reduce API calls.
    """

    assessments = deterministic_assessments or {}

    if isinstance(assessments, list):
        assessments = {
            item.get("requirement_id"): item
            for item in assessments
            if isinstance(item, dict) and item.get("requirement_id")
        }

    incomplete: list[dict] = []

    for requirement in requirements:
        rid = requirement["id"]
        assessment = assessments.get(rid)

        if assessment is None:
            assessment = assess_requirement(rid, crawler_data)

        if assessment.get("overall_evidence_status") == "FOUND":
            continue

        incomplete.append(requirement)

    results: dict[str, dict] = {}

    for start in range(0, len(incomplete), BATCH_SIZE):
        batch = incomplete[start:start + BATCH_SIZE]

        packages = {}
        semantic_slices = {}

        for requirement in batch:
            rid = requirement["id"]
            assessment = assessments.get(rid)

            if assessment is None:
                assessment = assess_requirement(rid, crawler_data)

            packages[rid] = build_llm_evidence_package(assessment)
            semantic_slices[rid] = _build_semantic_crawler_slice(
                requirement,
                crawler_data,
            )

        prompt = _build_batch_prompt(
            batch,
            packages,
            semantic_slices,
        )

        result = await call_evidence_llm(
            "You are a strict evidence extraction model. Return JSON only.",
            prompt,
        )

        batch_results = _normalise_batch_result(result, batch)
        results.update(batch_results)

    return results
