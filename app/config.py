# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "dev"
    MONGODB_URI: str
    OPENAI_API_KEY: str
    QDRANT_COLLECTION_NAME: str

    class Config:
        env_file = ".env"


settings = Settings()
