# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    MONGODB_URI: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
