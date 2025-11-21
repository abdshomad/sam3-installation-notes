from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application configuration, loaded from env vars or .env."""

    app_name: str = "Labeler"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{(BASE_DIR / 'storage' / 'labeler.db').as_posix()}"
    storage_root: Path = BASE_DIR / "storage"
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def upload_dir(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def export_dir(self) -> Path:
        return self.storage_root / "exports"

    @property
    def tmp_dir(self) -> Path:
        return self.storage_root / "tmp"


settings = Settings()

