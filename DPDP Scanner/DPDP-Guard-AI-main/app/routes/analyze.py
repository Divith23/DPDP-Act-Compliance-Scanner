from fastapi import APIRouter, HTTPException, Query

from app.services.crawler_data import (
    get_crawler_result,
    save_classification,
    get_compliance_report,
    save_compliance_report,
)
from app.services.crawler_normalizer import normalize_crawler_data
from app.services.classifier import classify_website
from app.services.compliance_analyzer import analyze_compliance

router = APIRouter()


@router.get("/analyze/{scan_id}")
async def analyze(
    scan_id: str,
    assessment_date: str | None = Query(default=None),
    refresh: bool = Query(default=False),
    fast: bool = Query(default=True),
):
    # 1. Check cached compliance report in MongoDB first
    if not refresh:
        cached_report = await get_compliance_report(scan_id, assessment_date)
        if cached_report:
            print(f"Using cached compliance report for scan_id: {scan_id}")
            return {
                "scan_id": scan_id,
                "classification": cached_report.get("classification"),
                "compliance": cached_report.get("compliance"),
                "cached": True,
            }

    # 2. Get crawler result from MongoDB
    result = await get_crawler_result(scan_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No crawler result found for scan_id: {scan_id}"
        )

    # 3. Normalize crawler data
    normalized_data = normalize_crawler_data(result)

    # 4. Classify website
    classification = result.get("classification")

    if classification:
        print("Using cached classification from MongoDB.")
    else:
        try:
            classification = await classify_website(normalized_data)
            await save_classification(scan_id, classification)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Classification failed: {e}"
            )

    # 5. Run DPDP compliance analysis
    try:
        compliance_report = await analyze_compliance(
            crawler_data=normalized_data,
            category=classification["category"],
            assessment_date=assessment_date,
            fast_mode=fast,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Compliance analysis failed: {e}"
        )

    # 6. Save compliance report for future instant retrieval
    try:
        await save_compliance_report(
            scan_id=scan_id,
            assessment_date=assessment_date,
            report=compliance_report,
            classification=classification,
        )
    except Exception as e:
        print(f"Notice: Failed to cache compliance report: {e}")

    # 7. Return final result
    return {
        "scan_id": scan_id,
        "classification": classification,
        "compliance": compliance_report,
        "cached": False,
    }