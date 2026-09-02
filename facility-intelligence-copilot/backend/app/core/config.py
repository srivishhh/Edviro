from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically locate and load .env from backend directory, project root, or parent folders
_project_root = Path(__file__).resolve().parents[2]  # facility-intelligence-copilot/
_backend_root = Path(__file__).resolve().parents[1]  # backend/

for _env_path in [
    Path.cwd() / ".env",
    _project_root / ".env",
    _backend_root / ".env",
    _project_root.parent / ".env",
]:
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://facility_user:facility_password@localhost:5432/facility_intelligence"
    kafka_bootstrap_servers: str = "localhost:9092"

    # SNS Workbench Configuration
    sns_workbench_url: str = "https://sns-workbench.example.invalid"
    sns_webhook_test_url: str | None = None
    sns_webhook_production_url: str | None = None
    sns_api_key: str | None = None
    sns_agent_id: str | None = "facility-xray-demo"
    sns_webhook_signing_secret: str | None = None

    # API Security & Authentication
    api_auth_enabled: bool = False
    api_keys: str | None = None

    # CORS Configuration
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


