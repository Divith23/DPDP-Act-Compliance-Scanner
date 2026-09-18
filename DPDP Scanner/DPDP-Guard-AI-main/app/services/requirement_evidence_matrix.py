"""Requirement-to-evidence matrix for the DPDP compliance scanner.

This module is intentionally separate from the crawler, normalizer and LLM.
It defines *what must be evidenced* for each inventory requirement. The
elements below are derived from the wording already present in
``app.services.requirement_inventory.REQUIREMENT_INVENTORY``; they are not an
LLM-generated legal checklist.

Design goal:
    requirement -> assessment elements -> evidence sources -> evidence state

The matrix is the backbone for targeted crawling, evidence extraction,
requirement-level retrieval, deterministic validation and LLM reasoning.
"""

from copy import deepcopy
from app.services.requirement_inventory import get_all_requirements


# Evidence source priority is a routing hint, not proof of compliance.
SOURCE_PRIORITY = {
    "policy": ["privacy_policy", "terms_of_use"],
    "ui": ["consent_ui_evidence", "rights_ui_evidence", "grievance_ui_evidence", "language_ui_evidence", "ui_information"],
    "security": ["security_policy", "breach_information"],
    "contact": ["contact_information", "grievance_information"],
    "operations": ["retention_information", "page_text", "privacy_policy"],
}


ELEMENTS = {

    'ACT_SEC_4': ['lawful purpose', 'consent or legitimate use'],
    'ACT_SEC_5': ['personal data proposed to be processed', 'purpose of processing', 'means to exercise rights', 'means to make a complaint to the Board'],
    'ACT_SEC_5_2': ['pre-Act consent exists or is applicable', 'required notice provided as soon as reasonably practicable'],
    'ACT_SEC_5_3': ['notice accessible in English', 'notice accessible in an Eighth Schedule language'],
    'ACT_SEC_6_1': ['free consent', 'specific consent', 'informed consent', 'unconditional consent', 'unambiguous consent', 'clear affirmative action', 'specified purpose', 'data limited to what is necessary'],
    'ACT_SEC_6_2': ['withdrawal or invalidity conditions are not inconsistent with Section 6(2)'],
    'ACT_SEC_6_3': ['consent request is clear', 'consent request is plain', 'consent request is standalone from unrelated purposes'],
    'ACT_SEC_6_4': ['means to withdraw consent', 'withdrawal mechanism is as easy as giving consent'],
    'ACT_SEC_6_6': ['processing ceases after withdrawal', 'retention after withdrawal is addressed where legally required'],
    'ACT_SEC_6_10': ['proof of notice', 'proof of consent'],
    'ACT_SEC_8_1': ['data fiduciary remains responsible for processing'],
    'ACT_SEC_8_2': ['processor contract exists where processing is delegated', 'contract addresses required obligations'],
    'ACT_SEC_8_3': ['reasonable accuracy', 'completeness', 'consistency where relevant'],
    'ACT_SEC_8_4': ['technical measures', 'organisational measures'],
    'ACT_SEC_8_5': ['reasonable security safeguards'],
    'ACT_SEC_8_6': ['breach intimation to affected data principals', 'breach intimation to Board where required'],
    'ACT_SEC_8_7': ['erasure after withdrawal', 'erasure after purpose completion', 'lawful retention exception'],
    'ACT_SEC_8_9': ['processing contact information is published'],
    'ACT_SEC_8_10': ['grievance mechanism', 'means to raise grievances', 'response to grievances'],
    'ACT_SEC_9_1': ['verifiable parental consent', 'parental consent before processing children data'],
    'ACT_SEC_9_2': ['no processing likely to cause detrimental effect on child well-being'],
    'ACT_SEC_9_3': ['no child tracking', 'no child behavioural monitoring', 'no targeted advertising directed at children'],
    'ACT_SEC_10_DPO': ['DPO appointed', 'DPO based in India', 'DPO responsible to Board or governing body', 'DPO represents SDF', 'DPO is grievance contact'],
    'ACT_SEC_10_AUDITOR': ['independent data auditor appointed', 'data audit carried out'],
    'ACT_SEC_10_DPIA': ['periodic DPIA undertaken'],
    'ACT_SEC_10_AUDIT': ['periodic compliance audit undertaken'],
    'ACT_SEC_11': ['prescribed personal-data information can be obtained', 'relevant sharing information can be obtained'],
    'ACT_SEC_12': ['means for correction', 'means for completion', 'means for updating', 'means for erasure', 'requests acted on as prescribed'],
    'ACT_SEC_13': ['readily available grievance means', 'grievance response within prescribed period'],
    'RULE_3': ['notice is standalone', 'notice is independently understandable'],
    'RULE_3_ITEMISED_DATA': ['itemised personal data description'],
    'RULE_3_PURPOSE': ['specified processing purpose', 'specific description of goods/services/uses enabled'],
    'RULE_3_LINKS': ['communication link', 'means to withdraw consent', 'means to exercise rights', 'means to complain to Board'],
    'RULE_6_ENCRYPTION': ['encryption or appropriate equivalent protection', 'obfuscation/masking/virtual tokens where appropriate'],
    'RULE_6_ACCESS': ['access control for computer resources'],
    'RULE_6_LOGGING': ['access logs', 'monitoring', 'review', 'detect unauthorised access', 'investigate unauthorised access', 'remediate unauthorised access'],
    'RULE_6_BACKUPS': ['business continuity', 'appropriate backups'],
    'RULE_6_LOG_RETENTION': ['security log retention for one year', 'processing/personal-data retention for one year', 'exception for applicable law'],
    'RULE_6_PROCESSOR_CONTRACT': ['processor contract security safeguards where applicable'],
    'RULE_6_TECH_ORG': ['technical security measures', 'organisational security measures'],
    'RULE_7_PRINCIPAL_BREACH': ['notice to affected Data Principals without delay', 'breach consequences', 'mitigation measures', 'safety measures', 'business contact information', 'clear/plain language'],
    'RULE_7_BOARD_BREACH': ['notice to Board without delay', 'prescribed detailed information', '72-hour period or permitted extension'],
    'RULE_8_ERASURE': ['applicable Third Schedule class/purpose', 'specified erasure period', 'erasure when principal neither approaches nor exercises rights', 'lawful retention exception'],
    'RULE_8_48_HOURS': ['48-hour pre-erasure notice', 'notice explains upcoming erasure', 'login/contact/rights exception'],
    'RULE_8_ONE_YEAR': ['Seventh Schedule applicability', 'personal data retention one year', 'traffic data retention one year', 'processing log retention one year'],
    'RULE_9_CONTACT': ['prominent business contact information', 'DPO contact if applicable or processing-questions contact'],
    'RULE_10_CHILD_CONSENT': ['verifiable parental consent', 'technical and organisational measures', 'parent identified as identifiable adult'],
    'RULE_11_GUARDIAN': ['lawful guardian consent applies', 'due diligence verification', 'guardian appointed by lawful authority'],
    'RULE_13_DPIA': ['annual DPIA', 'annual audit'],
    'RULE_13_BOARD_REPORT': ['DPIA/audit report', 'significant observations', 'report furnished to Board'],
    'RULE_13_ALGORITHMIC_RISK': ['due diligence on technical measures', 'algorithmic software risk assessment', 'risk to Data Principal rights'],
    'RULE_13_LOCALISATION': ['government-specified localisation restriction applies', 'specified personal/traffic data not transferred contrary to restriction'],
    'RULE_14_RIGHTS_MEANS': ['prominently published rights-exercise means', 'required identifier information'],
    'RULE_14_GRIEVANCE_90_DAYS': ['published grievance redressal system', 'technical and organisational measures', 'response within reasonable period', 'period not exceeding 90 days'],
    'RULE_15_CROSS_BORDER': ['government cross-border restriction applies', 'compliance with applicable restriction'],
}


# Topic hints allow a future targeted crawler/evidence retriever to search
# for high-signal phrases without asking Gemini to discover them.
TOPIC_HINTS = {
    "consent": ["consent", "agree", "accept", "continue", "withdraw", "permission"],
    "notice": ["privacy policy", "privacy notice", "personal data", "purpose", "rights", "complaint"],
    "rights": ["privacy centre", "privacy center", "access", "copy", "correct", "update", "delete", "erase", "withdraw"],
    "grievance": ["grievance", "complaint", "grievance officer", "redressal", "raise a concern", "contact"],
    "security": ["encryption", "masking", "obfuscation", "access control", "logging", "monitoring", "backup", "incident", "breach", "security"],
    "children": ["child", "children", "minor", "under 18", "parent", "guardian", "age", "tracking", "behavioural", "behavioral", "targeted advertising"],
    "retention": ["retain", "retention", "erase", "deletion", "one year", "48 hours"],
    "contact": ["email", "phone", "DPO", "data protection officer", "contact us"],
}


def _topics_for_requirement(requirement_id: str) -> list[str]:
    rid = requirement_id.upper()
    topics = []
    if "5" in rid or "6" in rid or "CONSENT" in rid:
        topics.append("consent")
    if rid.startswith("RULE_3") or rid == "ACT_SEC_4":
        topics.append("notice")
    if rid in {"ACT_SEC_11", "ACT_SEC_12", "ACT_SEC_13", "RULE_14_RIGHTS_MEANS", "RULE_14_GRIEVANCE_90_DAYS", "RULE_3_LINKS"}:
        topics.extend(["rights", "grievance"])
    if "GRIEVANCE" in rid or rid in {"ACT_SEC_13", "ACT_SEC_8_10", "RULE_9_CONTACT"}:
        topics.append("grievance")
    if "SECURITY" in rid or rid.startswith("RULE_6") or "BREACH" in rid:
        topics.append("security")
    if "CHILD" in rid or "GUARDIAN" in rid or rid.startswith("ACT_SEC_9"):
        topics.append("children")
    if "RETENTION" in rid or "ERASURE" in rid or "ONE_YEAR" in rid or "48_HOURS" in rid:
        topics.append("retention")
    if "CONTACT" in rid or "DPO" in rid:
        topics.append("contact")
    return list(dict.fromkeys(topics))


def build_requirement_matrix() -> list[dict]:
    """Return the inventory enriched with deterministic assessment metadata."""
    requirements = deepcopy(get_all_requirements())
    matrix = []
    for requirement in requirements:
        rid = requirement["id"]
        elements = ELEMENTS.get(rid, [])
        matrix.append({
            **requirement,
            "assessment_elements": list(elements),
            "topic_hints": _topics_for_requirement(rid),
            "evidence_strategy": {
                "inventory_fields": list(requirement.get("evidence_fields", [])),
                "source_priority": [
                    field
                    for group in _topics_for_requirement(rid)
                    for field in SOURCE_PRIORITY.get(group, [])
                ],
            },
        })
    return matrix


def get_requirement_matrix(requirement_id: str | None = None):
    """Get all matrix entries, or one entry by requirement ID."""
    matrix = build_requirement_matrix()
    if requirement_id is None:
        return matrix
    return next((r for r in matrix if r["id"] == requirement_id), None)


def get_assessment_elements(requirement_id: str) -> list[str]:
    """Return the atomic assessment elements for one requirement."""
    return list(ELEMENTS.get(requirement_id, []))


def validate_matrix() -> dict:
    """Validate that the matrix covers the complete deterministic inventory."""
    inventory_ids = {r["id"] for r in get_all_requirements()}
    matrix_ids = set(ELEMENTS)
    missing = sorted(inventory_ids - matrix_ids)
    extra = sorted(matrix_ids - inventory_ids)
    return {
        "inventory_count": len(inventory_ids),
        "matrix_count": len(matrix_ids),
        "missing": missing,
        "extra": extra,
        "valid": not missing and not extra,
    }
