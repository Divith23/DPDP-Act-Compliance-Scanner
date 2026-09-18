from pydantic_settings import BaseSettings


import os

_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "dpdp_guard"
    CRAWLER_COLLECTION: str = "crawler_results"
    REPORTS_COLLECTION: str = "compliance_reports"

    # LLM #1: semantic evidence discovery
    GEMINI_EVIDENCE_API_KEY: str
    GEMINI_EVIDENCE_MODEL: str = "gemini-3.5-flash"

    # LLM #2: legal compliance analysis
    GEMINI_ANALYSIS_API_KEY: str
    GEMINI_ANALYSIS_MODEL: str = "gemini-3.1-flash-lite"

    class Config:
        env_file = _env_path if os.path.exists(_env_path) else ".env"


settings = Settings()
