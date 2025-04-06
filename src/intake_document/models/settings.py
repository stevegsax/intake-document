"""Settings models for the application."""

from typing import Optional

from pydantic import BaseModel, Field


class MistralConfig(BaseModel):
    """Configuration for Mistral.ai API."""

    api_key: Optional[str] = None
    batch_size: int = Field(default=5, ge=1, le=20)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=60, ge=10, le=300)


class AppConfig(BaseModel):
    """Application-specific configuration."""

    output_dir: str = "./output"
    log_level: str = "ERROR"


class Settings(BaseModel):
    """Main settings model containing all configuration sections."""

    mistral: MistralConfig = Field(default_factory=MistralConfig)
    app: AppConfig = Field(default_factory=AppConfig)
