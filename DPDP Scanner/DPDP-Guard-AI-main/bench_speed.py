import time
import httpx

def main():
    print("=== STARTING END-TO-END PIPELINE SPEED TEST ===")
    t_start = time.time()

    with httpx.Client(timeout=60.0) as client:
        # 1. Crawl
        print("Step 1: Crawling website (Playwright with in-browser extraction)...")
        t0 = time.time()
        crawl_resp = client.post("http://127.0.0.1:8001/crawl", json={"url": "https://skcet.ac.in"})
        t1 = time.time()
        if crawl_resp.status_code != 200:
            print("Crawl failed:", crawl_resp.text)
            return
        crawl_data = crawl_resp.json()
        scan_id = crawl_data["scan_id"]
        print(f"-> Crawl completed in {round(t1 - t0, 2)}s! Scan ID: {scan_id}")

        # 2. Fresh Analyze
        print("Step 2: Fresh Compliance Analysis (V22 Deterministic Engine)...")
        t2 = time.time()
        analyze_resp = client.get(f"http://127.0.0.1:8000/api/analyze/{scan_id}?assessment_date=2027-01-01")
        t3 = time.time()
        if analyze_resp.status_code != 200:
            print("Analyze failed:", analyze_resp.text)
            return
        report = analyze_resp.json()
        print(f"-> Fresh analyze completed in {round(t3 - t2, 2)}s!")
        score = report.get("compliance", {}).get("score", {})
        print("-> Compliance Score:", score.get("score_display"))
        print("-> Evidence Coverage:", score.get("evidence_coverage_display"))

        # 3. Cached reload
        print("Step 3: Instant Cached Retrieval from MongoDB...")
        t4 = time.time()
        cached_resp = client.get(f"http://127.0.0.1:8000/api/analyze/{scan_id}?assessment_date=2027-01-01")
        t5 = time.time()
        print(f"-> Cached retrieval completed in {round(t5 - t4, 3)}s!")

    total = round(time.time() - t_start, 2)
    print(f"\n=== TOTAL END-TO-END WORKFLOW TIME: {total}s ===")

if __name__ == "__main__":
    main()
