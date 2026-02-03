"""Application configuration management"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenAI Configuration
    openai_api_key: str = ""

    # Nanobanano Configuration (APIyi.com - OpenAI Images API compatible)
    nanobanano_api_key: str = ""
    nanobanano_api_url: str = "https://api.apiyi.com/v1"
    nanobanano_model: str = "dall-e-3"

    # Database Configuration
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/ai_image_hub"

    # Application Security
    api_secret_token: str = ""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # ChatGPT Prompt Settings
    chatgpt_model: str = "gpt-4"
    chatgpt_max_tokens: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
