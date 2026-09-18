import sys

# Force UTF-8 on Windows stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Fallback: override print to guarantee charmap/encoding safety across Windows terminals
_orig_print = print
def print(*args, **kwargs):
    try:
        _orig_print(*args, **kwargs)
    except (UnicodeEncodeError, Exception):
        try:
            safe_args = [
                str(arg).encode("ascii", "replace").decode("ascii")
                for arg in args
            ]
            _orig_print(*safe_args, **kwargs)
        except Exception:
            pass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from main import crawl_website

app = FastAPI(title="DPDP Guard Crawler API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CrawlRequest(BaseModel):
    url: HttpUrl


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/crawl")
def crawl(request: CrawlRequest):
    try:
        scan_id = crawl_website(str(request.url))
        if not scan_id:
            raise HTTPException(
                status_code=502,
                detail=f"Could not crawl {request.url}. The target website failed to load or refused the connection.",
            )
        return {
            "message": "Crawling completed successfully",
            "scan_id": scan_id,
            "website": str(request.url),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Crawling failed: {e}",
        )
