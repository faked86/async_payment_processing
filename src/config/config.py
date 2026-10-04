from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_database_name: str

    rabbit_user: str
    rabbit_password: str
    rabbit_host: str
    rabbit_port: int

    api_key: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


settings = Settings()  # type: ignore[call-arg]
