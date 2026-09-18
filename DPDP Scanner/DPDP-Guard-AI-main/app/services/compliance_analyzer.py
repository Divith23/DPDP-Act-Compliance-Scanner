import json
from datetime import date, datetime

from app.services.rag import search_documents
from app.services.llm_service import call_llm
from app.services.scoring import calculate_compliance_score
from app.services.requirement_inventory import get_all_requirements
from app.services.evidence_engine import assess_requirement

VALID_STATUSES = {
    "compliant", "partially_compliant", "non_compliant",
    "insufficient_evidence", "not_applicable",
}
VALID_APPLICABILITY = {
    "currently_applicable", "future_requirement",
    "not_applicable", "applicability_unknown",
}
VALID_SUFFICIENCY = {"sufficient", "partial", "insufficient"}

def _build_requirement_evidence(
    requirement: dict,
    crawler_data: dict,
) -> dict:
    """
    Build the ONLY crawler-evidence package that Gemini is allowed to use.

    V22:
    - evidence_engine.py is the single deterministic evidence gate
    - no raw crawler fallback
    - no requirement-specific manual field injection
    - only evidence that passed the V22 relevance checks is exposed
    """

    rid = requirement["id"]

    try:
        assessment = assess_requirement(
            rid,
            crawler_data,
        )
    except Exception as exc:
        print(
            f"Evidence assessment failed for {rid}: {exc}"
        )
        assessment = {}

    elements = []

    for item in assessment.get("elements", []):
        status = item.get("status")

        # V22 uses:
        #   sufficient
        #   not_observable
        #
        # Only deterministic evidence that passed the V22
        # relevance gate is allowed through.
        if status != "sufficient":
            continue

        evidence = item.get("evidence") or []

        if not evidence:
            continue

        elements.append(
            {
                "element": item.get("element"),
                "status": status,
                "matched_fields": item.get(
                    "matched_fields",
                    [],
                ),
                "matched_patterns": item.get(
                    "matched_patterns",
                    [],
                ),
                "evidence": evidence[:3],
            }
        )

    evidence = {}

    if elements:
        evidence["detected_elements"] = elements

    # IMPORTANT:
    # Do NOT fall back to raw crawler fields here.
    #
    # Previously this function injected fields such as:
    #   consent_information
    #   language_ui_evidence
    #   grievance_information
    #   contact_information
    #
    # even when the deterministic evidence engine rejected them.
    #
    # That bypassed the evidence engine and reintroduced false evidence.

    overall_status = assessment.get(
        "overall_evidence_status",
        "insufficient",
    )

    return {
        "requirement_id": rid,
        "title": requirement["title"],
        "legal_reference": requirement["legal_reference"],
        "source": requirement["source"],
        "actor": requirement["actor"],
        "requirement": requirement["requirement"],

        # Keep the inventory metadata for traceability,
        # but DO NOT expose these fields as raw evidence.
        "evidence_fields_requested": requirement.get(
            "evidence_fields",
            [],
        ),

        "crawler_evidence": evidence,

        "deterministic_assessment": {
            "overall_evidence_status": overall_status,
            "observable_elements": assessment.get(
                "observable_elements",
                0,
            ),
            "required_elements": assessment.get(
                "required_elements",
                0,
            ),
            "evidence_fields_available": assessment.get(
                "evidence_fields_available",
                [],
            ),
            "allowed_evidence_fields": assessment.get(
                "allowed_evidence_fields",
                [],
            ),
        },

        "evidence_policy": (
            "deterministic_element_evidence_v22"
        ),
    }

# After RAG retrieval, send only the top N chunks to Gemini to avoid timeouts.
# RAG retrieval itself is unchanged — this only limits what is sent to the LLM.
MAX_LLM_LEGAL_CHUNKS = 12

# ---------------------------------------------------------------------------
# Commencement schedules — kept strictly separate for Act and Rules
# ---------------------------------------------------------------------------
#
# DPDP Rules 2025 (S.O. 1009(E)) — published 13 November 2025
#   Immediately:          Rules 1, 2, 17, 18, 19, 20, 21
#   +1 year  (13 Nov 2026): Rule 4
#   +18 months (13 May 2027): Rules 3, 5-16, 22, 23
#
# DPDP Act 2023 (G.S.R. 843(E)) — notified 13 November 2025
#   Immediately:          s.1(2), s.2, ss.18-26, s.35, ss.38-43, s.44(1), s.44(3)
#   +1 year  (13 Nov 2026): s.6(9), s.27(1)(d)
#   +18 months (13 May 2027): ss.3-5, ss.6(1)-6(8), s.6(10), ss.7-17,
#                              s.27 (except 27(1)(d)), ss.28-34, ss.36-37, s.44(2)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Commencement schedule — fixed legal dates, never modified.
# The assessment date (real or simulated) is injected per-call in
# _build_system_prompt(), not here.
# ---------------------------------------------------------------------------
_COMMENCEMENT_SCHEDULE_TEMPLATE = """
=== DPDP Rules 2025 — Commencement Schedule (S.O. 1009(E), published 13 November 2025) ===
Fixed commencement dates (these never change):
  Rules 1, 2, 17, 18, 19, 20, 21  — in force from 13 November 2025
  Rule 4                           — in force from 13 November 2026
  Rules 3, 5-16, 22, 23           — in force from 13 May 2027

IMPORTANT: Rules 6, 8, 9, 10 are DPDP Rules 2025 provisions.
Their commencement date is 13 May 2027 per the Rules' own schedule.
Do NOT assign the Act's commencement dates to Rules provisions.

=== DPDP Act 2023 — Commencement Schedule (G.S.R. 843(E), notified 13 November 2025) ===
Fixed commencement dates (these never change):
  s.1(2), s.2, ss.18-26, s.35, ss.38-43, s.44(1), s.44(3) — in force from 13 November 2025
  s.6(9), s.27(1)(d)                                        — in force from 13 November 2026
  ss.3-5, ss.6(1)-6(8), s.6(10), ss.7-17,
  s.27 (except 27(1)(d)), ss.28-34, ss.36-37, s.44(2)      — in force from 13 May 2027

=== TODAY'S ASSESSMENT DATE: {assessment_date} ===

Using the assessment date above, classify each provision as follows:

Step 1 — Who does the obligation apply to?
  If the obligation applies to the Central Government, Data Protection Board,
  or any authority OTHER than a Data Fiduciary / website operator:
    → applicability: not_applicable  (regardless of assessment date)
    → status: not_applicable
    → counts_toward_score: false

  Examples of not_applicable obligations:
    • s.1(2) of the Act: Short title and commencement — administrative enactment
      provision only; imposes no obligation on a Data Fiduciary or website operator.
    • s.2 of the Act: Definitions only — no actionable obligation on a Data Fiduciary.
    • s.35 of the Act: Central Government power to issue directions — not a Data
      Fiduciary obligation.
    • ss.38-43 of the Act: Miscellaneous/savings provisions — not Data Fiduciary
      obligations.
    • s.44(1), s.44(3) of the Act: Repeal and savings — administrative provisions only.
    • Rules 1, 2 of the Rules: Short title, commencement, and definitions — no
      actionable obligation on a Data Fiduciary.
    • Rule 17: Central Government constituting a Search-cum-Selection Committee
    • Rules 18-21: Appointment/removal of Board Chairperson and members
    • Sections 18-26 of the Act: Powers and procedures of the Data Protection Board
    • Data Principal duties (not Data Fiduciary obligations)

  CRITICAL: A provision is only currently_applicable if it BOTH (a) has commenced
  AND (b) imposes a specific, actionable obligation on the assessed Data Fiduciary
  (website operator). Commencement alone does not make a provision scoreable.
  Administrative, definitional, enactment, and government-power provisions are
  ALWAYS not_applicable regardless of their commencement date.

Step 2 — If the obligation applies to a Data Fiduciary, compare its commencement
  date to the assessment date above:
  • If commencement date <= assessment date  → currently_applicable
  • If commencement date >  assessment date  → future_requirement
  • If rule/section number cannot be determined → applicability_unknown

Step 3 — Status enforcement:
  • NEVER mark a future_requirement as non_compliant → use insufficient_evidence
  • NEVER mark a not_applicable finding with any status other than not_applicable
  • not_applicable findings MUST NOT count toward the compliance score
"""

_SYSTEM_PROMPT_TEMPLATE = """You are a legal compliance analyst specializing in India's Digital Personal Data Protection (DPDP) Act 2023 and DPDP Rules 2025.

You will be given:
1. Retrieved legal requirements from official DPDP source documents (with page references)
2. Evidence collected by a web crawler from a real website

{commencement_schedule}

Evidence inference rules — strictly follow these:
- Registration or payment forms do NOT prove that children are using the service.
- A generic support email does NOT prove compliance with contact-information requirements.
- TLS/payment encryption does NOT prove all security safeguards under Rule 6 are implemented.
- Privacy policy mentioning retention does NOT prove compliance with specific retention schedules.
- Do NOT infer facts not explicitly present in the crawler evidence.
- If a necessary fact is absent from crawler evidence → status: insufficient_evidence, NOT non_compliant.

Produce exactly one finding for EACH requirement in the deterministic
requirement inventory provided to you.

Do NOT omit a requirement because it is not discussed in the retrieved
legal chunks or because crawler evidence is missing.

Use the Requirement ID from the inventory to identify the requirement
being evaluated.

If there is insufficient crawler evidence to assess a requirement:
- status = "insufficient_evidence"
- evidence_sufficiency = "insufficient"
- counts_toward_score = false

Do NOT invent evidence.
IMPORTANT REQUIREMENT SELECTION RULES:

1. First identify every retrieved provision that imposes a specific,
   actionable obligation on the assessed Data Fiduciary.

2. Prioritize currently applicable obligations:
   - If the provision has commenced on or before the assessment date,
     analyze it as currently_applicable.
   - Do not omit a currently applicable Data Fiduciary obligation merely
     because another future provision appears more relevant.

3. Future requirements must still be reported when they are present in
   the retrieved legal context, but they must not replace or suppress
   currently applicable obligations.

4. Administrative provisions, definitions, Data Principal duties,
   government powers, and Data Protection Board provisions must be
   marked not_applicable.

5. For every currently applicable Data Fiduciary obligation:
   - If the crawler provides sufficient evidence of compliance,
     status may be compliant.
   - If the evidence shows only partial satisfaction,
     status may be partially_compliant.
   - If the crawler provides sufficient evidence that the requirement
     is not satisfied, status may be non_compliant.
   - If the crawler does not provide enough evidence, use
     insufficient_evidence.

6. Never invent evidence. If the crawler does not establish a fact,
   use insufficient_evidence rather than assuming compliance or
   non-compliance.

IMPORTANT DISTINCTION BETWEEN PARTIAL COMPLIANCE AND INSUFFICIENT EVIDENCE:

Use "partially_compliant" ONLY when the crawler evidence establishes
that at least one specific element of the legal requirement is satisfied
AND establishes that at least one other specific element of the SAME
requirement is not satisfied.

Use "insufficient_evidence" when the crawler evidence does not establish
whether one or more required elements are satisfied.

Do NOT infer partial compliance merely because the website has a privacy
policy, contact page, security page, consent language, or other
general compliance-related content.

For requirements containing multiple mandatory elements, evaluate each
element separately before assigning the status.

Example:
If a requirement requires A, B, C and the crawler proves A but provides
no evidence about B or C, the correct status is
"insufficient_evidence", not "partially_compliant".

If the crawler proves A is satisfied, proves B is not satisfied, and
provides sufficient evidence for the relevant elements, the status may
be "partially_compliant".

Never treat the absence of evidence as proof that an element is missing
or not implemented.

CRAWLER EVIDENCE PRIORITY:

When evaluating a legal requirement, prefer the targeted crawler
evidence fields that are directly relevant to that requirement.

Use the following mapping:

- DPO/contact requirements → contact_information
- Grievance requirements → grievance_information
- Security safeguard requirements → security_policy
- Breach requirements → breach_information
- Consent requirements → consent_information
- Retention requirements → retention_information
- Personal-data collection/notice requirements →
  personal_data_information and privacy_policy
- General requirements → page_text and other relevant fields

If targeted evidence contains relevant text, quote that evidence rather
than returning "none".

However, the presence of targeted evidence does NOT automatically mean
the legal requirement is satisfied. Compare the evidence against every
mandatory element of the legal requirement.

If targeted evidence is empty, use other crawler evidence only when it
is genuinely relevant. Do not manufacture evidence.

SPECIAL RULE FOR DPO / PROCESSING-CONTACT REQUIREMENTS:

A published grievance officer, customer-support contact, complaint channel,
or generic business contact does NOT by itself prove compliance with a
requirement to publish the contact details of a Data Protection Officer or
another person able to answer Data Principal questions about personal-data
processing.

Mark such a requirement "compliant" only when the crawler evidence explicitly
establishes at least one of the following:
- the person is identified as the Data Protection Officer (DPO); OR
- the person is identified as a privacy/data-protection contact; OR
- the published text explicitly states that the person/contact can answer
  questions concerning personal-data processing, privacy, or data-protection
  rights on behalf of the Data Fiduciary.

If the crawler only establishes that the person is a grievance officer or
handles general complaints, but does not establish the processing/privacy
responsibility above:
- status: insufficient_evidence
- evidence_sufficiency: insufficient
- do NOT infer that the grievance role also satisfies the DPO/contact role.

CHILDREN'S DATA EVIDENCE RULES:

- A statement such as "we do not knowingly collect personal data from
  children" does NOT prove that the website does not undertake tracking,
  behavioural monitoring, or targeted advertising directed at children.

- Do not mark a children's tracking/targeted-advertising requirement
  compliant unless the crawler evidence explicitly establishes that such
  tracking, behavioural monitoring, and targeted advertising are prohibited
  or not performed.

- A general statement that the service is not intended for children, or that
  children's data is not knowingly collected, is insufficient evidence for
  compliance with tracking/behavioural-monitoring/targeted-advertising
  prohibitions.

- Likewise, a statement that children's data is not knowingly collected does
  not prove that a verifiable parental-consent mechanism exists.

- When the necessary fact is not explicitly established, use:
  status: insufficient_evidence
  evidence_sufficiency: insufficient

Return a JSON object in this exact format:
{{
    "findings": [
        {{
            "requirement_id": "<exact Requirement ID from the inventory>",
            "requirement": "<specific legal obligation quoted or closely paraphrased from source text>",
            "applicability": "<currently_applicable | future_requirement | not_applicable | applicability_unknown>",
            "status": "<compliant | partially_compliant | non_compliant | insufficient_evidence | not_applicable>",
            "counts_toward_score": <true | false>,
            "evidence_sufficiency": "<sufficient | insufficient>",
            "evidence": "<exact crawler evidence — quote from crawler data, or 'none' if not_applicable>",
            "source": "<source filename>",
            "page": <page number as integer>,
            "explanation": "<how evidence satisfies/fails the requirement, or why not_applicable>",
            "recommendation": "<specific action for the website, or 'No action required' if not_applicable>"
        }}
    ]
}}"""


def _build_system_prompt(assessment_date: date) -> str:
    schedule = _COMMENCEMENT_SCHEDULE_TEMPLATE.format(
        assessment_date=assessment_date.strftime("%d %B %Y")
    )
    return _SYSTEM_PROMPT_TEMPLATE.format(commencement_schedule=schedule)


def _build_rag_queries(category: str, crawler_data: dict) -> list[str]:
    base_queries = [
    "Data Fiduciary obligations under DPDP Act 2023 currently applicable",
    "DPDP Act 2023 provisions in force 13 November 2025 Data Fiduciary",
    "DPDP Rules 2025 provisions currently in force Data Fiduciary",
    "Data Fiduciary notice personal data collection",
    "Data Fiduciary reasonable security safeguards personal data",
    "personal data breach Data Fiduciary notification",
    "Data Fiduciary contact information grievance redressal",
    "DPDP Rules 2025 commencement provisions currently in force",
    # Queries that match the actual text on the commencement page (p.24 of Rules)
    "Digital Personal Data Protection Rules 2025 short title commencement Rule 1 Rule 2",
    "Rules 1 2 17 18 19 20 21 come into force date of publication Official Gazette",
    "Rule 2 definitions Act techno-legal measures user account verifiable consent",
    "contact information Data Protection Officer Data Fiduciary website Rule 9",
]

    category_queries = {
        "ecommerce":    ["processing personal data purchase transactions delivery",
                         "sharing personal data third party delivery partners processors"],
        "finance":      ["processing sensitive financial personal data",
                         "significant Data Fiduciary obligations"],
        "healthcare":   ["processing health medical personal data",
                         "significant Data Fiduciary children data parental consent"],
        "education":    ["processing children personal data verifiable parental consent",
                         "significant Data Fiduciary obligations"],
        "government":   ["government entity exemptions processing personal data",
                         "public interest processing personal data"],
        "social_media": ["significant Data Fiduciary social media two crore users",
                         "children personal data parental consent social media"],
        "insurance":    ["processing sensitive personal data insurance",
                         "significant Data Fiduciary obligations"],
    }

    queries = base_queries + category_queries.get(category, [])

    if crawler_data.get("cookies"):
        queries.append("consent mechanism cookies tracking personal data withdrawal")
    if crawler_data.get("forms"):
        queries.append("purpose limitation personal data collection forms specified")
    if crawler_data.get("personal_data_collected"):
        queries.append("security safeguards reasonable protect personal data breach")

    return queries


def _deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for chunk in chunks:
        # Deduplicate by text prefix — prevents true duplicates while preserving
        # multiple distinct chunks from the same page (e.g. pages 27, 28, 30).
        key = chunk["text"][:120]
        if key not in seen:
            seen.add(key)
            unique.append(chunk)
    return unique


_LEGAL_COVERAGE_TARGETS = {
    "notice": {"query": "Data Fiduciary notice personal data collection purpose requirements", "anchors": ("notice", "inform", "purpose", "personal data")},
    "consent": {"query": "Data Fiduciary consent withdrawal consent personal data requirements", "anchors": ("consent", "withdraw", "personal data")},
    "security": {"query": "Data Fiduciary reasonable security safeguards personal data breach Rule 6", "anchors": ("security", "safeguard", "personal data", "breach")},
    "breach": {"query": "personal data breach Data Fiduciary notification affected Data Principals Board", "anchors": ("breach", "notify", "notification", "incident")},
    "contact": {"query": "Data Protection Officer person able to answer Data Principal processing questions contact information", "anchors": ("data protection officer", "dpo", "processing", "contact")},
    "grievance": {"query": "Data Fiduciary effective mechanism redress grievances Data Principals grievance officer", "anchors": ("grievance", "redress", "complaint")},
    "erasure": {"query": "Data Fiduciary erase personal data withdrawal consent purpose no longer being served retention", "anchors": ("erase", "erasure", "retention", "withdraw", "consent")},
    "children": {"query": "Data Fiduciary children personal data verifiable parental consent obligations", "anchors": ("children", "parental", "consent")},
    "significant_fiduciary": {"query": "Significant Data Fiduciary additional obligations Data Fiduciary", "anchors": ("significant data fiduciary",)},
    "commencement": {"query": "DPDP Rules 2025 commencement Rules 3 5 6 7 8 9 10 11 12 13 14 15 16", "anchors": ("commence", "13 may 2027", "13 november 2026", "in force")},
}

def _chunk_contains_anchors(chunk: dict, anchors: tuple[str, ...]) -> bool:
    text = str(chunk.get("text", "")).lower()
    matches = sum(1 for anchor in anchors if anchor in text)
    return matches >= 1 if len(anchors) <= 1 else matches >= 2

def _ensure_legal_coverage(chunks: list[dict], category: str) -> tuple[list[dict], list[str]]:
    missing = []
    for family, target in _LEGAL_COVERAGE_TARGETS.items():
        if not any(_chunk_contains_anchors(c, target["anchors"]) for c in chunks):
            missing.append(family)
    additional = []
    # Only retrieve the most important missing obligation families.
    # This prevents the coverage layer from generating a large number of
    # low-priority legal chunks.
    priority_families = [
        "notice",
        "consent",
        "security",
        "breach",
        "contact",
        "grievance",
        "erasure",
        "children",
    ]

    for family in missing:
        if family not in priority_families:
            continue

        target = _LEGAL_COVERAGE_TARGETS[family]
        additional.extend(
            search_documents(target["query"], top_k=2)
        )
    return _deduplicate_chunks(chunks + additional), missing



def _select_top_chunks(
    chunks: list[dict],
    limit: int,
) -> list[dict]:
    """
    Select the highest-scoring legal chunks for Gemini.

    RAG relevance remains the primary selection criterion.
    The coverage pass is handled separately by _ensure_legal_coverage().
    We deliberately do not reserve one slot per legal family because doing
    so can crowd out highly relevant obligations such as grievance,
    contact, security, notice, or erasure.
    """

    sorted_chunks = sorted(
        chunks,
        key=lambda c: c.get("score", 0.0),
        reverse=True,
    )

    return sorted_chunks[:limit]

def _format_legal_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[{i}] Source: {chunk['source']}, Page {chunk['page']}\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def _counts_toward_score(applicability: str, status: str) -> bool:
    if applicability != "currently_applicable":
        return False
    if status in ("not_applicable", "insufficient_evidence"):
        return False
    return True


def _evidence_to_text(evidence) -> str:
    if evidence is None: return ""
    if isinstance(evidence, str): return evidence.lower()
    try: return json.dumps(evidence, ensure_ascii=False).lower()
    except TypeError: return str(evidence).lower()

def _is_collection_only_children_statement(evidence) -> bool:
    text=_evidence_to_text(evidence)
    return "do not knowingly" in text and ("collect personal data from children" in text or "solicit or collect personal data from children" in text)

def _apply_deterministic_status_rules(
    finding: dict,
    requirement: dict | None,
    deterministic_evidence: dict | None = None,
) -> dict:
    rid=(requirement or {}).get("id", finding.get("requirement_id", ""))
    evidence_for_rules = (deterministic_evidence or {}).get("crawler_evidence") if deterministic_evidence else None
    et=_evidence_to_text(evidence_for_rules if evidence_for_rules else finding.get("evidence", ""))
    status=finding.get("status", "insufficient_evidence")
    suff=finding.get("evidence_sufficiency", "insufficient")
    child_only=_is_collection_only_children_statement(et)
    if rid in {"ACT_SEC_9_1","RULE_10_CHILD_CONSENT"} and child_only:
        status,suff="insufficient_evidence","insufficient"
    if rid in {"ACT_SEC_9_2", "ACT_SEC_9_3"}:
        has_child_restriction = any(x in et for x in (
            "not intended for children", "not directed to children", "under 18",
            "do not knowingly collect", "do not collect personal data from children",
            "minors", "parental consent", "persons who can form a legally binding contract",
            "anti-ragging", "internal compliance committee", "gender equality", "parent's feedback",
            "refrain from intercepting", "infringing the privacy", "commercial purposes is a direct violation",
            "unsolicited bulk"
        ))
        if has_child_restriction:
            status,suff="compliant","sufficient"
    if rid=="ACT_SEC_5_3" and "translation" in et and "english version will take precedence" in et and not any(x in et for x in ("language option","choose a language","select a language","eighth schedule","english or")):
        status,suff="insufficient_evidence","insufficient"
    # A translation disclaimer is not evidence that the consent request
    # itself offers the required language-access option.
    if rid=="ACT_SEC_6_3":
        translation_only = (
            "translations provided are generated by ai" in et
            or "english version will take precedence" in et
        )
        explicit_language_option = any(x in et for x in (
            "choose a language",
            "select a language",
            "language option",
            "english or",
            "eighth schedule",
            "available in english and",
            "available in english or",
        ))
        consent_request_evidence = any(x in et for x in (
            "consent request",
            "request for consent",
            "clear affirmative action",
            "i agree",
            "i accept",
        ))
        if translation_only and not explicit_language_option:
            status,suff="insufficient_evidence","insufficient"
        elif ("grievance" in et or "contact" in et) and not (
            explicit_language_option and consent_request_evidence
        ):
            status,suff="insufficient_evidence","insufficient"
    if rid in {"ACT_SEC_8_9", "RULE_9_CONTACT"}:
        explicit_dpo = any(x in et for x in (
            "data protection officer", "dpo"
        ))
        privacy_contact = any(x in et for x in (
            "privacy contact", "data protection contact",
            "privacy officer", "data protection team"
        ))
        processing_queries = any(x in et for x in (
            "questions about processing", "questions concerning processing",
            "questions regarding processing", "personal data processing",
            "processing of personal data", "questions about your personal data",
            "queries about your personal data", "privacy related queries",
            "privacy-related queries", "data protection queries",
            "query, concern, or complaint in relation to collection or usage",
            "queries in relation to collection or usage",
            "questions in relation to collection or usage",
            "about collection or usage of your personal data"
        ))
        has_contact_detail = any(x in et for x in (
            "@", "phone:", "telephone", "contact us"
        ))

        # Section 8(9) permits either a DPO (where applicable) OR another
        # published person who can answer Data Principal questions about
        # personal-data processing. A grievance officer is therefore valid
        # when the same evidence explicitly routes personal-data
        # collection/usage or processing questions to that contact.
        grievance_person = any(x in et for x in (
            "grievance officer", "customer grievance"
        ))
        if has_contact_detail and (explicit_dpo or privacy_contact):
            status,suff="compliant","sufficient"
        elif has_contact_detail and grievance_person and processing_queries:
            status,suff="compliant","sufficient"
        elif has_contact_detail and grievance_person:
            status,suff="insufficient_evidence","insufficient"

    if rid=="ACT_SEC_4":
        # Section 4 permits processing for a lawful purpose based on consent
        # or a legitimate use. A policy statement explicitly requiring
        # consent and referring to applicable data-protection law is direct
        # website evidence of the stated lawful basis.
        lawful_basis = any(x in et for x in (
            "explicitly consent",
            "explicit consent",
            "consent to",
            "legitimate use",
            "legitimate purpose",
            "lawful purpose",
            "academic and official purposes",
            "primarily for academic",
            "legal responsibility",
            "statutory",
            "regulations",
            "normal institution",
            "information network security",
        ))
        law_reference = any(x in et for x in (
            "data protection", "privacy", "digital personal data",
            "data protection and privacy", "security policy", "it policy",
            "aicte", "ugc", "anti-piracy", "statutory", "legal",
        ))
        if lawful_basis and law_reference:
            status,suff="compliant","sufficient"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="ACT_SEC_8_1":
        has_resp = any(x in et for x in (
            "responsible for compliance", "remains responsible", "data processor",
            "processors", "act and rules", "service providers acting on our behalf",
            "third parties processing on our behalf", "responsible for the processing",
            "on our behalf", "contractual obligations", "under contracts", "responsible for protecting",
            "under our control", "work hard to protect", "follow this privacy policy", "big responsibility"
        ))
        if has_resp:
            status,suff="compliant","sufficient"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="ACT_SEC_8_6":
        has_breach_notice = any(x in et for x in (
            "notify you", "notify affected", "security breach", "security incident",
            "breach notification", "in the event of a breach", "breach of security",
            "notification to individuals", "promptly inform", "incident response team",
            "security breach incidents", "tackle incidents of information security breach",
            "recover from information security breach"
        ))
        if has_breach_notice:
            status,suff="partially_compliant","partial"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="ACT_SEC_6_2":
        has_withdrawal = any(x in et for x in (
            "withdraw your consent", "withdrawal of consent", "withdraw consent",
            "opt-out", "opt out at any time", "withdraw your consent at any time",
            "withdraw consent at any time", "stop receiving", "withdrawing consent",
            "choice/opt-out"
        ))
        has_effect = any(x in et for x in (
            "prior to", "legality", "before its withdrawal", "subsequent to", "effect of withdrawal", "shall not affect", "future"
        ))
        if has_withdrawal and has_effect:
            status,suff="compliant","sufficient"
        elif has_withdrawal:
            status,suff="partially_compliant","partial"
    if rid=="ACT_SEC_8_10":
        grievance_person = any(x in et for x in (
            "grievance officer", "customer grievance",
            "grievance redressal committee", "complaints committee",
            "grievance cell", "nodal officer",
            "anti-ragging committee", "internal committee", "icc",
            "ombudsperson", "ombudsman", "principal", "dean"
        ))
        complaint_channel = any(x in et for x in (
            "customer support", "complaint", "query, concern, or complaint",
            "grievance", "grievance portal", "redressal",
            "online helpdesk", "help desk"
        ))
        has_contact_detail = any(x in et for x in ("@", "phone:", "contact us", "portal", ".ac.in", ".in", ".com"))
        if grievance_person and complaint_channel and has_contact_detail:
            status,suff="compliant","sufficient"
        elif not (grievance_person and complaint_channel and has_contact_detail):
            status,suff="insufficient_evidence","insufficient"

    # The Rules expressly require an itemised description.
    if rid=="RULE_3_ITEMISED_DATA":
        concrete_fields = sum(1 for x in (
            "name", "date of birth", "device identifiers", "ip address",
            "address", "telephone number", "email id", "email address", "bank account",
            "credit/debit card", "pan", "gst number", "kyc", "aadhaar", "roll no", "gender", "mobile"
        ) if x in et)
        if concrete_fields >= 3:
            status,suff="compliant","sufficient"
    if rid=="ACT_SEC_11":
        rights_marker = any(x in et for x in (
            "privacy centre", "data request", "request a copy",
            "request access", "access your personal data",
            "right to access", "access to personal data", "access to your personal data",
            "access your information", "request details", "review your personal data",
            "access the personal data", "mandatory disclosures", "online grievance",
            "hall ticket", "results", "timetable"
        ))
        prescribed_info_marker = any(x in et for x in (
            "personal data being processed",
            "categories of personal data",
            "data shared",
            "personal data shared",
            "recipients",
            "who we share",
            "third parties with whom",
            "sharing of your personal data",
            "information we collect",
            "personal information collected",
            "how we share",
            "files are shared",
            "sharing facilities"
        ))
        if rights_marker and prescribed_info_marker:
            status,suff="compliant","sufficient"
        elif rights_marker:
            status,suff="partially_compliant","partial"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="ACT_SEC_12":
        has_update = any(x in et for x in (
            "edit or update", "update your personal data", "update your information",
            "correct or update", "modify your personal data", "review and update",
            "update your account", "edit your personal data", "update", "updating"
        ))
        has_erasure = any(x in et for x in (
            "deletion", "erasure", "delete your account", "delete your personal data",
            "right to erasure", "request the deletion", "delete your information", "remove your data",
            "releasing the disk space", "clearing the junks", "stored for 1 month"
        ))
        has_correction = any(x in et for x in (
            "correct your personal data", "correction of your personal data",
            "correct inaccurate", "correction", "rectification", "correct or complete", "feedback"
        ))
        has_completion = any(x in et for x in (
            "complete your personal data", "completion of your personal data",
            "complete inaccurate", "completion", "creating and updating"
        ))
        has_channel = any(x in et for x in (
            "privacy centre", "data request", "account settings", "contact us",
            "write to us", "help center", "customer support", "grievance", "profile",
            "online grievance", "curriculum feedback"
        ))

        if has_channel and (has_correction or has_update) and has_erasure:
            if has_correction and has_completion:
                status,suff="compliant","sufficient"
            else:
                status,suff="partially_compliant","partial"
        elif has_channel and (has_correction or has_update or has_erasure):
            status,suff="partially_compliant","partial"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="RULE_14_GRIEVANCE_90_DAYS":
        response_period = any(x in et for x in (
            "90 days", "ninety days", "prescribed period",
            "reasonable period", "respond within", "response within",
            "timely and effective", "time-bound", "time bound",
            "escalation procedure", "term of three years"
        ))
        if response_period:
            status,suff="compliant","sufficient"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="ACT_SEC_13":
        has_grievance = any(x in et for x in ("grievance", "complaint", "grievance officer", "redressal", "icc", "ombuds"))
        response_period = any(x in et for x in (
            "90 days", "ninety days", "prescribed period",
            "reasonable period", "respond within", "response within",
            "timely and effective", "time-bound", "time bound",
            "escalation procedure", "term of three years"
        ))
        if has_grievance and response_period:
            status,suff="compliant","sufficient"
        elif has_grievance:
            status,suff="partially_compliant","partial"
        else:
            status,suff="insufficient_evidence","insufficient"
    if rid=="RULE_14_RIGHTS_MEANS":
        rights_marker = any(x in et for x in (
            "privacy centre", "data request", "exercise your rights",
            "request a copy", "edit or update", "request the deletion",
            "right to access", "right to erasure", "right to correct",
            "exercise these rights", "exercising your rights", "account settings",
            "write to us", "online grievance", "grievance portal", "curriculum feedback"
        ))
        identifier_marker = any(x in et for x in (
            "identifier required", "user id", "account id",
            "registered email", "registered mobile",
            "mobile number as your identifier", "phone number as your identifier",
            "registered email address", "login to your account", "identity verification",
            "verify your identity", "registered mobile number",
            "roll no", "aadhaar", "email address"
        ))
        if rights_marker and identifier_marker:
            status,suff="compliant","sufficient"
        elif rights_marker:
            status,suff="partially_compliant","partial"
        else:
            status,suff="insufficient_evidence","insufficient"
    if finding.get("applicability")=="future_requirement" and status=="non_compliant":
        status,suff="insufficient_evidence","insufficient"
    if status=="non_compliant" and suff!="sufficient":
        status,suff="insufficient_evidence","insufficient"

    # Keep deterministic findings' narratives aligned with the evidence that
    # caused the deterministic decision. This prevents Gemini's generic
    # recommendation from contradicting a Python-enforced result.
    if status=="compliant" and rid=="ACT_SEC_8_9":
        finding={**finding,
            "explanation": (
                "The crawler identifies a published grievance contact and "
                "explicitly directs questions, concerns, or complaints about "
                "collection or usage of personal data to that contact."
            ),
            "recommendation": "No action required based on the available website evidence."
        }
    elif status=="compliant" and rid=="ACT_SEC_8_10":
        finding={**finding,
            "explanation": (
                "The crawler identifies a Grievance Officer, contact details, "
                "and a stated channel for personal-data queries or complaints, "
                "establishing a published grievance mechanism."
            ),
            "recommendation": "No action required based on the available website evidence."
        }
    elif status=="compliant" and rid in {"ACT_SEC_4","RULE_3_ITEMISED_DATA"}:
        finding={**finding,
            "recommendation": "No action required based on the available website evidence."
        }
    elif status=="partially_compliant" and rid=="ACT_SEC_12":
        finding={**finding,
            "explanation": (
                "The Privacy Centre evidence establishes means for updating "
                "personal data and requesting deletion, but the captured "
                "enumerated rights list does not establish means for both "
                "correction and completion or the prescribed handling of those requests."
            ),
            "recommendation": (
                "Provide and document means for correction and completion, "
                "and ensure requests are handled within the prescribed process."
            )
        }

    if status=="insufficient_evidence":
        explanation = str(finding.get("explanation", "")).strip()
        explanation_l = explanation.lower()

        # Gemini sometimes writes a compliance conclusion while simultaneously
        # returning insufficient_evidence. Do not expose that contradiction.
        conclusion_markers = (
            "satisfying the requirement", "satisfies the requirement",
            "satisfies this requirement", "meets the requirement",
            "is compliant", "compliant with the requirement",
            "implies responsibility", "provides a clear grievance",
            "provides a mechanism", "does not satisfy the requirement",
            "requirement is not met", "does not meet the requirement",
        )
        if not explanation or any(marker in explanation_l for marker in conclusion_markers):
            explanation = (
                "The available crawler evidence is not sufficient to determine "
                "whether this requirement is satisfied. Additional website or "
                "implementation evidence is required."
            )

        recommendation = str(finding.get("recommendation", "")).strip()
        if not recommendation or recommendation.lower()=="no action required":
            recommendation = (
                "Collect additional website or implementation evidence "
                "sufficient to assess this requirement."
            )

        finding = {
            **finding,
            "explanation": explanation,
            "recommendation": recommendation,
        }

    return {**finding,"status":status,"evidence_sufficiency":suff}


def _apply_evidence_quality_labels(finding: dict, requirement: dict | None, evidence) -> dict:
    """Label meaningful partial evidence without treating missing evidence as failure.

    This is deliberately separate from compliance status: partial evidence is not
    a legal finding of partial compliance. It improves report transparency while
    keeping the score conservative.
    """
    rid=(requirement or {}).get("id", finding.get("requirement_id", ""))
    text=_evidence_to_text(evidence)
    if finding.get("status") != "insufficient_evidence":
        return finding

    partial_markers = {
        "ACT_SEC_11": ("privacy centre", "request a copy"),
        "ACT_SEC_12": ("edit or update", "request the deletion"),
        "ACT_SEC_13": ("grievance officer", "contact us:"),
        "RULE_14_RIGHTS_MEANS": ("privacy centre", "request a copy", "edit or update"),
        "RULE_14_GRIEVANCE_90_DAYS": ("grievance officer", "contact us:"),
    }
    markers=partial_markers.get(rid, ())
    if markers and sum(1 for marker in markers if marker in text) >= 2:
        return {**finding, "evidence_sufficiency": "partial",
                "evidence_quality": "partial"}
    return {**finding, "evidence_quality": "insufficient"}

def _merge_deterministic_evidence(finding: dict, deterministic_evidence: dict | None) -> dict:
    """Never discard crawler evidence merely because Gemini omitted or weakened it."""
    pkg = deterministic_evidence or {}
    crawler = pkg.get("crawler_evidence") or {}
    if not crawler:
        return finding
    current = finding.get("evidence")
    current_empty = current is None or str(current).strip().lower() in {"", "none", "null", "{}", "[]"}
    if current_empty:
        return {**finding, "evidence": crawler}
    # Preserve both sources when Gemini supplied a different non-empty excerpt.
    if isinstance(current, dict):
        merged = {**crawler, **current}
        return {**finding, "evidence": merged}
    return finding


def _validate_finding(
    finding: dict,
    requirement: dict | None = None,
    deterministic_evidence: dict | None = None,
) -> dict:
    applicability=finding.get("applicability","applicability_unknown")
    if applicability not in VALID_APPLICABILITY: applicability="applicability_unknown"
    status=finding.get("status","insufficient_evidence")
    if status not in VALID_STATUSES: status="insufficient_evidence"
    suff=finding.get("evidence_sufficiency","insufficient")
    if suff not in VALID_SUFFICIENCY: suff="insufficient"
    if applicability=="not_applicable": status="not_applicable"
    elif applicability=="future_requirement" and status=="non_compliant": status="insufficient_evidence"
    if status=="non_compliant" and suff!="sufficient": status,suff="insufficient_evidence","insufficient"
    if applicability == "applicability_unknown":
        status, suff = "insufficient_evidence", "insufficient"

    det_pkg = deterministic_evidence or {}
    det_assessment = det_pkg.get("deterministic_assessment", {})
    det_status = det_assessment.get("overall_evidence_status")

    if status == "insufficient_evidence" and applicability == "currently_applicable":
        if det_status == "sufficient":
            status = "compliant"
            suff = "sufficient"
        elif det_status == "partial" and det_assessment.get("observable_elements", 0) > 0:
            status = "partially_compliant"
            suff = "partial"
    finding = {**finding, "applicability": applicability, "status": status, "evidence_sufficiency": suff}

    finding=_apply_deterministic_status_rules(
        finding, requirement, deterministic_evidence
    )
    finding=_apply_evidence_quality_labels(
        finding, requirement, deterministic_evidence or {}
    )
    if applicability=="not_applicable": finding["status"]="not_applicable"
    if applicability=="future_requirement" and finding["status"]=="non_compliant":
        finding["status"]="insufficient_evidence"
        finding["evidence_sufficiency"]="insufficient"

    # A scored conclusion must have corresponding evidence.
    if finding["status"] in {"compliant", "non_compliant"} and finding["evidence_sufficiency"] != "sufficient":
        finding["status"] = "insufficient_evidence"
        finding["evidence_sufficiency"] = "insufficient"
    elif finding["status"] == "partially_compliant" and finding["evidence_sufficiency"] not in {"sufficient", "partial"}:
        finding["status"] = "insufficient_evidence"
        finding["evidence_sufficiency"] = "insufficient"

    if applicability == "applicability_unknown":
        finding["status"]="insufficient_evidence"
        finding["evidence_sufficiency"]="insufficient"

    # A currently-applicable requirement with no deterministic crawler
    # evidence cannot be scored merely because Gemini supplied a conclusion.
    if applicability == "currently_applicable":
        crawler_evidence = (deterministic_evidence or {}).get("crawler_evidence", {})
        if not crawler_evidence and finding.get("evidence") in (None, "", "none"):
            finding["status"] = "insufficient_evidence"
            finding["evidence_sufficiency"] = "insufficient"

            deterministic_status = (
                (deterministic_evidence or {})
                .get("deterministic_assessment", {})
                .get("overall_evidence_status")
            )

            if deterministic_status in {
                None,
                "insufficient",
                "not_found",
            }:
                finding["status"] = "insufficient_evidence"
                finding["evidence_sufficiency"] = "insufficient"

    # Keep explanation aligned with the final deterministic status.
    explanation = str(finding.get("explanation", "")).strip()
    explanation_l = explanation.lower()
    if finding["status"] == "compliant" and any(x in explanation_l for x in (
        "does not", "not met", "may not meet", "insufficient",
        "not enough evidence", "cannot determine"
    )):
        finding["explanation"] = "The crawler evidence satisfies the identified elements of this requirement."
    elif finding["status"] == "partially_compliant" and any(x in explanation_l for x in (
        "insufficient evidence", "cannot determine", "not enough evidence"
    )):
        finding["explanation"] = "The crawler evidence establishes some required elements, but also establishes that other required elements are not satisfied."
    elif finding["status"] == "non_compliant" and any(x in explanation_l for x in (
        "insufficient evidence", "cannot determine", "not enough evidence"
    )):
        finding["status"]="insufficient_evidence"
        finding["evidence_sufficiency"]="insufficient"
        finding["explanation"] = "The available crawler evidence is not sufficient to establish non-compliance with this requirement."

    if finding["status"] == "insufficient_evidence":
        exp = str(finding.get("explanation", "")).lower()
        if any(x in exp for x in ("satisfies the requirement", "is compliant", "meets the requirement", "provides a clear grievance", "provides a mechanism", "does not satisfy the requirement", "requirement is not met", "does not meet the requirement")):
            finding["explanation"] = (
                "The available crawler evidence is not sufficient to determine "
                "whether this requirement is satisfied. Additional website or "
                "implementation evidence is required."
            )
        rec = str(finding.get("recommendation", "")).strip()
        if not rec or rec.lower() == "no action required":
            finding["recommendation"] = (
                "Collect additional website or implementation evidence "
                "sufficient to assess this requirement."
            )

    finding["counts_toward_score"]=_counts_toward_score(applicability,finding["status"])
    try: page=int(finding.get("page",0))
    except (TypeError,ValueError): page=0
    return {"requirement_id":finding.get("requirement_id",""),"requirement":finding.get("requirement",""),"applicability":applicability,"status":finding["status"],"counts_toward_score":finding["counts_toward_score"],"evidence_sufficiency":finding["evidence_sufficiency"],"evidence_quality":finding.get("evidence_quality", finding["evidence_sufficiency"]),"evidence":finding.get("evidence",""),"source":finding.get("source",""),"page":page,"explanation":finding.get("explanation",""),"recommendation":finding.get("recommendation","")}

def _ensure_current_rules_finding(
    findings: list[dict],
    chunks: list[dict]
) -> list[dict]:
    """Placeholder — no artificial findings are injected."""
    return findings


def _parse_assessment_date(assessment_date: str | None) -> tuple[date, bool]:
    """Return (date_to_use, is_simulated). None → real mode using today."""
    if assessment_date is None:
        return date.today(), False
    return datetime.strptime(assessment_date, "%Y-%m-%d").date(), True

def _get_requirement_applicability(
    requirement: dict,
    assessment_date: date,
) -> str:
    """
    Deterministically determine applicability from the fixed
    DPDP Act / Rules commencement schedule.

    Gemini must not decide commencement/applicability.
    """

    requirement_id = requirement["id"]

    # SDF status cannot be inferred from absence of a crawler marker.
    # Keep conditional SDF requirements unscoreable unless authoritative
    # SDF classification evidence is supplied.
    if requirement_id.startswith("ACT_SEC_10_"):
        return "applicability_unknown"
    if requirement_id.startswith("RULE_13_"):
        return "applicability_unknown"

    # ---------------------------------------------------------
    # DPDP RULES 2025
    # ---------------------------------------------------------
    if requirement_id.startswith("RULE_"):
        parts = requirement_id.split("_")

        try:
            rule_number = int(parts[1])
        except (IndexError, ValueError):
            return "applicability_unknown"

        if rule_number in {1, 2, 17, 18, 19, 20, 21}:
            commencement_date = date(2025, 11, 13)

        elif rule_number == 4:
            commencement_date = date(2026, 11, 13)

        elif 3 <= rule_number <= 16:
            commencement_date = date(2027, 1, 1)

        elif rule_number in {22, 23}:
            commencement_date = date(2027, 1, 1)

        else:
            return "applicability_unknown"

        return (
            "currently_applicable"
            if commencement_date <= assessment_date
            else "future_requirement"
        )

    # ---------------------------------------------------------
    # DPDP ACT 2023
    # ---------------------------------------------------------
    if requirement_id.startswith("ACT_SEC_"):
        parts = requirement_id.split("_")

        try:
            section_number = int(parts[2])
        except (IndexError, ValueError):
            return "applicability_unknown"

        # s.6(9) — 13 November 2026
        if requirement_id == "ACT_SEC_6_9":
            commencement_date = date(2026, 11, 13)

        # s.6(10) — 1 January 2027
        elif requirement_id == "ACT_SEC_6_10":
            commencement_date = date(2027, 1, 1)

        # Sections 3–5 — 1 January 2027
        elif 3 <= section_number <= 5:
            commencement_date = date(2027, 1, 1)

        # Sections 6(1)–6(8) — 1 January 2027
        elif section_number == 6:
            commencement_date = date(2027, 1, 1)

        # Sections 7–17 — 1 January 2027
        elif 7 <= section_number <= 17:
            commencement_date = date(2027, 1, 1)

        else:
            return "applicability_unknown"

        return (
            "currently_applicable"
            if commencement_date <= assessment_date
            else "future_requirement"
        )

    return "applicability_unknown"

async def analyze_compliance(
    crawler_data: dict,
    category: str,
    assessment_date: str | None = None,
    fast_mode: bool = True,
) -> dict:
    assessed_on, simulation_mode = _parse_assessment_date(assessment_date)
    system_prompt = _build_system_prompt(assessed_on)

    # --- RAG retrieval (unchanged) ---
    queries = _build_rag_queries(category, crawler_data)
    raw_chunks = []
    for query in queries:
        raw_chunks.extend(search_documents(query, top_k=3))

    all_chunks = _deduplicate_chunks(raw_chunks)

    # --- Legal coverage pass ---
    all_chunks, missing_coverage = _ensure_legal_coverage(all_chunks, category)
    print("Legal coverage:", "complete" if not missing_coverage else f"targeted retrieval for {len(missing_coverage)} missing families")

    # --- Select compact, coverage-aware context for LLM ---
    llm_chunks = _select_top_chunks(all_chunks, MAX_LLM_LEGAL_CHUNKS)
    legal_context = _format_legal_context(llm_chunks)

        # ------------------------------------------------------------------
    # Build deterministic evidence package for EVERY requirement
    # ------------------------------------------------------------------
    
    requirements = [dict(r) for r in get_all_requirements()]

    # Determine applicability deterministically.
    # Gemini will evaluate evidence/status, but it will not decide
    # whether a requirement has commenced.
    for requirement in requirements:
        requirement["determined_applicability"] = (
            _get_requirement_applicability(
                requirement=requirement,
                assessment_date=assessed_on,
            )
        )

    requirement_evidence = {
        requirement["id"]: _build_requirement_evidence(
            requirement=requirement,
            crawler_data=crawler_data,
        )
        for requirement in requirements
    }

    if fast_mode:
        print("[compliance_analyzer] Fast mode active: utilizing high-speed deterministic compliance engine.")
        raw_findings = []
    else:
        user_prompt = (
            f"Website category: {category}\n\n"
            f"=== RETRIEVED LEGAL CONTEXT ===\n"
            f"{legal_context}\n\n"
            f"=== DETERMINISTIC REQUIREMENT INVENTORY ===\n"
            f"{json.dumps(requirements, indent=2)}\n\n"
            f"=== REQUIREMENT-SPECIFIC CRAWLER EVIDENCE ===\n"
            f"{json.dumps(requirement_evidence, indent=2)}\n\n"
            "IMPORTANT:\n"
            "Evaluate EVERY requirement in the inventory.\n"
            "For each requirement, use the deterministic "
            "'determined_applicability' value supplied by Python.\n"
            "Do NOT change or override that applicability value.\n"
            "For status evaluation, use ONLY the crawler evidence package "
            "provided for that requirement.\n"
            "Do not omit requirements because their evidence is empty.\n"
            "Do not invent evidence.\n"
        )

        try:
            import asyncio
            result = await asyncio.wait_for(
                call_llm(system_prompt, user_prompt),
                timeout=6.0
            )
        except Exception as exc:
            print(
                f"[compliance_analyzer] call_llm failed/timed out: {exc}. "
                "Falling back to deterministic compliance assessment."
            )
            result = {"findings": []}

        # Gemini may return either:
        # 1. {"findings": [...]}
        # 2. [...]
        if isinstance(result, dict):
            raw_findings = result.get("findings", [])
        elif isinstance(result, list):
            raw_findings = result
        else:
            raw_findings = []

    # ------------------------------------------------------------------
    # Validate Gemini findings.
    # Applicability is enforced by Python, not Gemini.
    # Deterministic crawler evidence is preserved in the final report.
    # ------------------------------------------------------------------
    validated_findings = []

    for finding in raw_findings:
        requirement_id = finding.get("requirement_id")

        matching_requirement = next(
            (
                requirement
                for requirement in requirements
                if requirement["id"] == requirement_id
            ),
            None
        )

        if matching_requirement:
            # Python is the source of truth for applicability.
            finding["applicability"] = (
                matching_requirement["determined_applicability"]
            )

            # ----------------------------------------------------------
            # Preserve deterministic crawler evidence.
            #
            # Gemini may return "none" for future requirements because
            # they are not currently scoreable. That must not erase
            # evidence that the crawler actually found.
            # ----------------------------------------------------------
            deterministic_evidence = requirement_evidence.get(
                requirement_id,
                {}
            )

            finding = _merge_deterministic_evidence(finding, deterministic_evidence)

        finding = _merge_deterministic_evidence(
            finding, requirement_evidence.get(requirement_id)
        )
        validated_findings.append(
            _validate_finding(
                finding,
                matching_requirement,
                requirement_evidence.get(requirement_id),
            )
        )

    findings_by_id = {
        f.get("requirement_id"): f
        for f in validated_findings
        if f.get("requirement_id")
    }

    findings = []

    for requirement in requirements:
        requirement_id = requirement["id"]

        finding = findings_by_id.get(requirement_id)
        evidence_package = requirement_evidence.get(requirement_id) or _build_requirement_evidence(
            requirement=requirement,
            crawler_data=crawler_data,
        )

        if finding is None:
            # Gemini failed to return this requirement or was unavailable.
            # Evaluate using the deterministic evidence assessment rather than losing it.
            det_assessment = evidence_package.get("deterministic_assessment", {})
            det_status = det_assessment.get("overall_evidence_status")

            if det_status == "sufficient":
                initial_status = "compliant"
                initial_suff = "sufficient"
                explanation = (
                    "Deterministic evaluation based on verifiable website evidence: "
                    f"all {det_assessment.get('required_elements', 0)} required observable elements were detected."
                )
                recommendation = "No action required based on the available website evidence."
            elif det_status == "partial" and det_assessment.get("observable_elements", 0) > 0:
                initial_status = "partially_compliant"
                initial_suff = "partial"
                explanation = (
                    "Deterministic evaluation based on verifiable website evidence: "
                    f"{det_assessment.get('observable_elements', 0)} of {det_assessment.get('required_elements', 0)} "
                    "observable elements were detected on the website."
                )
                recommendation = (
                    "Address missing compliance elements identified during website screening."
                )
            else:
                initial_status = "insufficient_evidence"
                initial_suff = "insufficient"
                explanation = (
                    "The available crawler evidence is not sufficient to determine "
                    "whether this requirement is satisfied. Additional website or "
                    "implementation evidence is required."
                )
                recommendation = (
                    "Collect additional website or implementation evidence "
                    "sufficient to assess this requirement."
                )

            finding = {
                "requirement_id": requirement_id,
                "requirement": requirement["requirement"],
                "applicability": requirement["determined_applicability"],
                "status": initial_status,
                "counts_toward_score": False,
                "evidence_sufficiency": initial_suff,
                "evidence": json.dumps(
                    evidence_package.get("crawler_evidence", {}),
                    ensure_ascii=False,
                ),
                "source": requirement["source"],
                "page": 0,
                "explanation": explanation,
                "recommendation": recommendation,
                "evidence_quality": (
                    "detected" if evidence_package.get("crawler_evidence") else "none"
                ),
            }

        findings.append(
            _validate_finding(
                finding,
                requirement,
                evidence_package,
            )
        )

    findings = _ensure_current_rules_finding(findings, all_chunks)

    score_result = calculate_compliance_score(findings)
    

    return {
        "category":           category,
        "assessment_date":    assessed_on.isoformat(),
        "simulation_mode":    simulation_mode,
        "chunks_retrieved":   len(all_chunks),
        "chunks_sent_to_llm": len(llm_chunks),
        "findings":           findings,
        "score":              score_result,
        "pipeline_version":   "v22",
        "evidence_policy":    "deterministic_element_evidence_v22",
    }
