from bson import ObjectId
from app.database.mongodb import get_db
from app.config import settings


async def get_crawler_result(scan_id: str) -> dict | None:
    db = get_db()
    try:
        query = {"_id": ObjectId(scan_id)}
    except Exception:
        query = {"scan_id": scan_id}

    doc = await db[settings.CRAWLER_COLLECTION].find_one(query)
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

async def save_classification(scan_id: str, classification: dict) -> None:
    db = get_db()

    try:
        query = {"_id": ObjectId(scan_id)}
    except Exception:
        query = {"scan_id": scan_id}

    await db[settings.CRAWLER_COLLECTION].update_one(
        query,
        {"$set": {"classification": classification}}
    )


async def get_compliance_report(scan_id: str, assessment_date: str | None = None) -> dict | None:
    db = get_db()
    query = {"scan_id": scan_id}
    if assessment_date:
        query["assessment_date"] = assessment_date

    doc = await db[settings.REPORTS_COLLECTION].find_one(query)
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def save_compliance_report(
    scan_id: str,
    assessment_date: str | None,
    report: dict,
    classification: dict,
) -> None:
    db = get_db()
    data_to_save = {
        "scan_id": scan_id,
        "assessment_date": assessment_date or report.get("assessment_date"),
        "classification": classification,
        "compliance": report,
    }

    await db[settings.REPORTS_COLLECTION].update_one(
        {
            "scan_id": scan_id,
            "assessment_date": assessment_date or report.get("assessment_date"),
        },
        {"$set": data_to_save},
        upsert=True,
    )