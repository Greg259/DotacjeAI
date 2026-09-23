from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_version: str = Field(default="0.3.0", validation_alias="APP_VERSION")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    source_storage_root: Path = Field(
        default=Path("/data/source-snapshots"), validation_alias="SOURCE_STORAGE_ROOT"
    )
    crawler_user_agent: str = Field(
        default="DotacjeAI/0.3 (+https://dotacjeai.eu)",
        validation_alias="CRAWLER_USER_AGENT",
    )
    crawler_timeout_seconds: float = Field(
        default=30.0, gt=0, validation_alias="CRAWLER_TIMEOUT_SECONDS"
    )
    crawler_retries: int = Field(default=3, ge=1, le=10, validation_alias="CRAWLER_RETRIES")
    crawler_max_response_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1024,
        validation_alias="CRAWLER_MAX_RESPONSE_BYTES",
    )

    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="dotacje", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="dotacje", validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr("dotacje"), validation_alias="POSTGRES_PASSWORD"
    )
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")

    llm_provider: str = Field(default="openrouter", validation_alias="LLM_PROVIDER")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", validation_alias="OPENROUTER_BASE_URL"
    )
    openrouter_api_key: SecretStr = Field(
        default=SecretStr(""), validation_alias="OPENROUTER_API_KEY"
    )
    llm_monthly_budget_usd: Decimal = Field(
        default=Decimal("10"), validation_alias="LLM_MONTHLY_BUDGET_USD"
    )
    llm_warning_budget_usd: Decimal = Field(
        default=Decimal("5"), validation_alias="LLM_WARNING_BUDGET_USD"
    )
    llm_critical_budget_usd: Decimal = Field(
        default=Decimal("8"), validation_alias="LLM_CRITICAL_BUDGET_USD"
    )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password.get_secret_value())
        database = quote_plus(self.postgres_db)
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{database}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
