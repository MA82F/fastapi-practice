from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str
    JWT_SECRET_KEY: str = "this is a secret key:)))))/"
    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
