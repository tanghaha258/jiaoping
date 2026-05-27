"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings."""

    # Application
    APP_NAME: str = "智跨学评 API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 20

    # Guangxi JiaoTong AI agent integration placeholders.
    GJT_API_BASE_URL: str = ""
    GJT_API_KEY: str = ""
    GJT_AGENT_ID: str = ""
    GJT_API_TIMEOUT_SECONDS: int = 30

    # Domestic OpenAI-compatible AI gateways. Provider-specific agent config can
    # override these values, while secrets should remain in environment vars.
    OPENAI_COMPATIBLE_API_BASE_URL: str = ""
    OPENAI_COMPATIBLE_API_KEY: str = ""
    OPENAI_COMPATIBLE_MODEL: str = ""
    OPENAI_COMPATIBLE_TIMEOUT_SECONDS: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
