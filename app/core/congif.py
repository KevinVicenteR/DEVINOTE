from pydantic import Field
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    JWT_SECRET: str = Field(...,alias="JWT_SECRET")
    JWT_ALG: str = Field(default="HS256", alias="JWT_ALG")
    JWT_EXPIRES_MIN: int = Field(default=60 * 24, alias="JWT_EXPIRES_MIN")
    PROJECT_NAME: str = "Devinote"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
    )


setting = Setting()
