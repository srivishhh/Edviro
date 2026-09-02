from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://facility_user:facility_password@localhost:5432/facility_intelligence"
    kafka_bootstrap_servers: str = "localhost:9092"
    sns_workbench_url: str = "https://sns-workbench.example.invalid"
    sns_api_key: str = "demo-api-key"
    sns_agent_id: str = "facility-xray-demo"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
