# DPDP Guard AI Module

AI/compliance analysis module for India's Digital Personal Data Protection Act (DPDP Act 2023) and DPDP Rules 2025.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your MongoDB Atlas credentials:
   ```bash
   cp .env.example .env
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Endpoints

- `GET /health` — Health check
- `GET /api/analyze/{scan_id}` — Retrieve crawler result by scan_id

## Project Structure

```
app/
  main.py           # FastAPI app entry point
  config.py         # Environment-based settings
  database/
    mongodb.py      # MongoDB Atlas connection (Motor async)
  routes/
    analyze.py      # API route definitions
  services/
    crawler_data.py # Fetch crawler results from MongoDB
    classifier.py   # (upcoming) LLM-based website classifier
    rag.py          # (upcoming) RAG over DPDP documents
    compliance.py   # (upcoming) Rule-level compliance evaluation
    scoring.py      # (upcoming) Deterministic compliance scoring
  schemas/
    analysis.py     # Pydantic response models

knowledge_base/
  documents/        # DPDP Act 2023 & Rules 2025 source documents

vectorstore/        # Persisted vector embeddings (gitignored)

tests/              # Test suite
```
