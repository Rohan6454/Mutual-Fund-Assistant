import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration loaded from environment variables."""

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini")  # "gemini" or "local"
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    GEMINI_EMBEDDING_DIMENSION: int = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "768"))

    # Qdrant (use QDRANT_URL for Qdrant Cloud; otherwise host/port)
    QDRANT_URL: str | None = os.getenv("QDRANT_URL") or None
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "mutual_fund_faq")

    # Retrieval
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_THRESHOLD: float = float(os.getenv("RETRIEVAL_THRESHOLD", "0.65"))
    RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", "3"))
    MMR_LAMBDA: float = float(os.getenv("MMR_LAMBDA", "0.7"))

    # Response
    MAX_RESPONSE_SENTENCES: int = int(os.getenv("MAX_RESPONSE_SENTENCES", "3"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_TOP_P: float = float(os.getenv("LLM_TOP_P", "0.95"))
    LLM_MAX_OUTPUT_TOKENS: int = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "256"))

    # Rate limiting
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "10/minute")

    # Scheduler (daily corpus refresh)
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_CRON_HOUR: int = int(os.getenv("SCHEDULER_CRON_HOUR", "9"))
    SCHEDULER_CRON_MINUTE: int = int(os.getenv("SCHEDULER_CRON_MINUTE", "15"))
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Kolkata")

    # Scraping
    SCRAPE_DELAY_SECONDS: float = float(os.getenv("SCRAPE_DELAY_SECONDS", "2.0"))
    SCRAPE_MAX_PDFS_PER_PAGE: int = int(os.getenv("SCRAPE_MAX_PDFS_PER_PAGE", "30"))
    SCRAPE_REQUEST_TIMEOUT: int = int(os.getenv("SCRAPE_REQUEST_TIMEOUT", "60"))

    # Embedding ingest
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
