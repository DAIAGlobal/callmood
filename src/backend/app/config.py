import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        validate_default=False
    )
    
    app_name: str = "CallMood SaaS API"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    database_url: str | None = None
    redis_url: str | None = None
    storage_dir: str = "storage"
    artifacts_dir: str = "artifacts"

    def __init__(self, **data):
        super().__init__(**data)
        # Set defaults from env if provided
        if not self.database_url:
            # Fallback to SQLite if DATABASE_URL not provided
            self.database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        if not self.redis_url:
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if not self.storage_dir or self.storage_dir == "None":
            self.storage_dir = os.getenv("STORAGE_DIR", "storage")
        if not self.artifacts_dir or self.artifacts_dir == "None":
            self.artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts")


@lru_cache
def get_settings() -> Settings:
    return Settings()

