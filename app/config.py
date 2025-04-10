# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "dev"
    MONGODB_URI: str
    OPENAI_API_KEY: str
    QDRANT_COLLECTION_NAME: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str

    class Config:
        env_file = ".env"


settings = Settings()
