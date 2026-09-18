# Knowledge Base — Legal Source Documents

This directory stores the authoritative legal and regulatory documents used by the DPDP Guard RAG pipeline.

## Documents to be placed here

| File | Source |
|------|--------|
| `dpdp_act_2023.pdf` | Digital Personal Data Protection Act, 2023 — Ministry of Law and Justice, Government of India |
| `dpdp_rules_2025.pdf` | Digital Personal Data Protection Rules, 2025 — Ministry of Electronics and Information Technology (MeitY) |

## Rules

- Only place **official, unmodified** copies of legal/regulatory documents here.
- Do **not** place summaries, interpretations, or third-party analyses.
- Documents must be sourced directly from:
  - [India Code](https://www.indiacode.nic.in)
  - [MeitY](https://www.meity.gov.in)
  - The official Gazette of India
- Do **not** commit these files to version control — add them manually to this directory on each deployment.

## Usage

These documents will be chunked, embedded, and stored in the vector store during the RAG ingestion pipeline (not yet implemented).
