from typing import Any


def calculate_compliance_score(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate compliance score using only findings that are:
      - currently_applicable
      - supported by sufficient evidence
      - not not_applicable

    Scoring:
      compliant           = 100
      partially_compliant = 50
      non_compliant       = 0

    Insufficient evidence is NOT treated as non-compliance and therefore does
    not reduce the compliance score.

    To prevent a score such as 100% from being interpreted as "all applicable
    obligations were verified", this function also reports evidence coverage:
      score      = performance among scoreable requirements
      coverage   = percentage of currently applicable requirements that had
                   enough evidence to be scored
    """

    currently_applicable = [
        f for f in findings
        if f.get("applicability") == "currently_applicable"
    ]

    eligible_findings = []

    for finding in currently_applicable:
        status = finding.get("status")

        # Cannot score something when evidence is insufficient.
        if status in {"insufficient_evidence", "not_applicable"}:
            continue

        # Only these statuses have a defined numerical score.
        if status not in {
            "compliant",
            "partially_compliant",
            "non_compliant",
        }:
            continue

        eligible_findings.append(finding)

    current_total = len(currently_applicable)

    insufficient_current = sum(
        1
        for f in currently_applicable
        if f.get("status") == "insufficient_evidence"
    )

    total_scoreable = len(eligible_findings)

    evidence_coverage = (
        round((total_scoreable / current_total) * 100, 2)
        if current_total > 0
        else 0.0
    )

    # No scoreable requirements.
    if not eligible_findings:
        return {
            "score": None,
            "score_display": "N/A",
            "status": "not_assessable",
            "message": (
                "No currently applicable requirements have sufficient "
                "evidence for scoring. The compliance score is N/A."
            ),
            "total_currently_applicable": current_total,
            "total_scoreable": 0,
            "evidence_coverage": evidence_coverage,
            "evidence_coverage_display": f"{evidence_coverage}%",
            "fully_assessed": False,
            "compliant": 0,
            "partially_compliant": 0,
            "non_compliant": 0,
            "insufficient_evidence": insufficient_current,
        }

    compliant = sum(
        1
        for f in eligible_findings
        if f.get("status") == "compliant"
    )

    partially_compliant = sum(
        1
        for f in eligible_findings
        if f.get("status") == "partially_compliant"
    )

    non_compliant = sum(
        1
        for f in eligible_findings
        if f.get("status") == "non_compliant"
    )

    weighted_score = (
        (compliant * 100)
        + (partially_compliant * 50)
        + (non_compliant * 0)
    )

    compliance_score = (
        round(weighted_score / total_scoreable, 2)
        if total_scoreable > 0
        else None
    )

    coverage_adjusted_score = (
        round(weighted_score / current_total, 2)
        if current_total > 0
        else None
    )

    score = compliance_score

    fully_assessed = (
        current_total > 0
        and total_scoreable == current_total
        and insufficient_current == 0
    )

    if insufficient_current > 0:
        message = (
            f"Compliance score: {score}% (assessed among {total_scoreable} scoreable requirements). "
            f"Evidence coverage: {evidence_coverage}% ({total_scoreable} of {current_total} currently applicable "
            f"requirements had sufficient evidence; {insufficient_current} remain unverified)."
        )
    else:
        message = (
            "Compliance score calculated from all currently applicable "
            "requirements identified in this analysis."
        )

    return {
        "score": score,
        "score_display": f"{score}%" if score is not None else "N/A",
        "compliance_score": score,
        "coverage_adjusted_score": coverage_adjusted_score,
        "status": "assessed" if total_scoreable > 0 else "not_assessable",
        "message": message,
        "total_currently_applicable": current_total,
        "total_scoreable": total_scoreable,
        "evidence_coverage": evidence_coverage,
        "evidence_coverage_display": f"{evidence_coverage}%",
        "fully_assessed": fully_assessed,
        "compliant": compliant,
        "partially_compliant": partially_compliant,
        "non_compliant": non_compliant,
        "insufficient_evidence": insufficient_current,
    }
