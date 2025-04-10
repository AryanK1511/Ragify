# app/config.py

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    PYTHON_ENV: str = "dev"
    PYTHON_ENV: str = "dev"
    MONGODB_URI: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    QDRANT_COLLECTION_NAME: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    LANGSMITH_TRACING: str
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    class Config:
        env_file = ".env"


settings = Settings()

# Set environment variables for Langsmith
os.environ["LANGCHAIN_TRACING"] = settings.LANGSMITH_TRACING
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
