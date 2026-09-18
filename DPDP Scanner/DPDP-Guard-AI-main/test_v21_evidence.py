import asyncio

from app.services.crawler_data import get_crawler_result
from app.services.crawler_normalizer import normalize_crawler_data
from app.services.evidence_engine import assess_requirement


SCAN_ID = "6aa28c3a58e533dc0dd4e602"

async def main():
    result = await get_crawler_result(SCAN_ID)
    data = normalize_crawler_data(result)

    requirement_ids = [
        "ACT_SEC_6_1",
        "ACT_SEC_8_5",
        "ACT_SEC_8_10",
        "RULE_9_CONTACT",
    ]

    for rid in requirement_ids:
        assessment = assess_requirement(rid, data)

        print("\n" + "=" * 80)
        print(rid)
        print("STATUS:", assessment["overall_evidence_status"])
        print("FIELDS:", assessment["evidence_fields_available"])

        for element in assessment["elements"]:
            print("\nELEMENT:", element["element"])
            print("STATUS:", element["status"])
            print("FIELDS:", element["matched_fields"])
            print("EVIDENCE:", element["evidence"])

asyncio.run(main())
