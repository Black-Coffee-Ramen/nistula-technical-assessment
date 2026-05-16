from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str
    port: int = 8000
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
