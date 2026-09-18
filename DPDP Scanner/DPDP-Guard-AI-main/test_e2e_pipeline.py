import asyncio
from app.database.mongodb import connect, disconnect, get_db
from bson import ObjectId
from app.services.crawler_normalizer import normalize_crawler_data
from app.services.compliance_analyzer import analyze_compliance
from app.services.classifier import classify_website

async def main():
    await connect()
    db = get_db()
    scan_id = "6aa2e6f6d4f9b48dd8fed386"
    raw = await db.crawler_results.find_one({"_id": ObjectId(scan_id)})
    if not raw:
        print(f"Scan {scan_id} not found!")
        return

    print("Found crawl record for:", raw.get("website"))
    print("Total pages in record:", len(raw.get("pages", [])))
    for i, p in enumerate(raw.get("pages", [])):
        print(f"  [{i}] {p.get('name')} | {p.get('title')} | len={len(p.get('content', ''))}")

    norm = normalize_crawler_data(raw)
    classification = await classify_website(norm)
    print("\nClassification:", classification)

    report = await analyze_compliance(norm, classification["category"], assessment_date="2027-01-01")
    print("\nCategory:", report.get("category"))
    print("Assessment date:", report.get("assessment_date"))
    print("Score result:", report.get("score"))
    findings = report.get("findings", [])
    print("Total findings:", len(findings))
    statuses = {}
    for f in findings:
        statuses[f.get("status")] = statuses.get(f.get("status"), 0) + 1
    print("Status counts:", statuses)
    
    # Print compliant and partially compliant findings with reasons
    for f in findings:
        if f.get("status") in ("compliant", "partially_compliant"):
            print(f"\n[{f.get('status').upper()}] {f.get('requirement_id')}")
            ev_str = str(f.get('evidence'))[:200].encode('ascii', 'replace').decode('ascii')
            print(f"  Evidence: {ev_str}")
            exp_str = str(f.get('explanation')).encode('ascii', 'replace').decode('ascii')
            print(f"  Explanation: {exp_str}")

    await disconnect()

if __name__ == "__main__":
    asyncio.run(main())
