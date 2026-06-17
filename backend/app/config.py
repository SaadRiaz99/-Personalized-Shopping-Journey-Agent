import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")


class Settings:
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_endpoint: str = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    jwt_refresh_expire_days: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/rag_app.db")

    max_file_size_mb: int = 50
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_retrieval_docs: int = 5
    max_conversation_history: int = 20


settings = Settings()
