from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///:memory:"
    JWT_SECRET_KEY: str = "this is a secret key:)))))/"
    REDIS_URL: str = "redis://redis:6379"
    SENTRY_DSN: str = "https://92b4489ec7b5748a613999eab821ccd1@sentry.hamravesh.com/9174"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
