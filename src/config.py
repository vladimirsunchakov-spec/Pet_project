from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    postgres_url: PostgresDsn
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


