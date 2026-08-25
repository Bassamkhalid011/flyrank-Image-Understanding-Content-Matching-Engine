from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = ""
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/image_relevance"

    SIMILARITY_THRESHOLD: float = 0.75
    CONFIDENCE_THRESHOLD: float = 0.80

    VISION_MODEL: str = "models/gemini-3.6-flash"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"


settings = Settings()
