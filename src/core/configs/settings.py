from datetime import timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: str | None = None
    model_config = SettingsConfigDict(
        env_file='envs/.env',
        extra='ignore'
    )


class GlobalConfig(BaseConfig):
    SECRET_KEY: str
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_URL: str = 'sqlite+aiosqlite:///db.sqlite3'
    ALEMBIC_DATABASE_URL: str
    REDIS_URL: str = 'redis://localhost:6379/0'
    REDIS_MAX_CONNECTIONS: int
    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'
    EMAIL_HOSTNAME: str
    EMAIL_PORT: int
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USERNAME: str
    EMAIL_HOST_PASSWORD: str
    TIMEZONE: str
    OTP_EXPIRATION_TIME: timedelta = timedelta(minutes=2)
    OTP_MAX_ATTEMPTS: int = 5
    UNUSABLE_PASSWORD_MARKER: str = "!UNUSABLE"
    CLIENT_ID: str
    CLIENT_SECRET: str
    AUTH_URI: str
    TOKEN_URI: str


class DevConfig(GlobalConfig):
    DEBUG: bool = True
    model_config = SettingsConfigDict(env_file='envs/.dev.env', env_prefix='DEV_')


class TestConfig(GlobalConfig):
    SECRET_KEY: str = "test-secret"
    DATABASE_POOL_SIZE: int = 1
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_URL: str = 'sqlite+aiosqlite:///db.sqlite3'
    ALEMBIC_DATABASE_URL: str = "sqlite:///db.sqlite3"
    REDIS_URL: str = 'redis://localhost:6379/0'
    REDIS_MAX_CONNECTIONS: int = 1
    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'
    EMAIL_HOSTNAME: str = ""
    EMAIL_PORT: int = 0
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USERNAME: str = ""
    EMAIL_HOST_PASSWORD: str = ""
    TIMEZONE: str = "Asia/Tehran"
    OTP_EXPIRATION_TIME: timedelta = timedelta(minutes=2)
    OTP_MAX_ATTEMPTS: int = 5
    UNUSABLE_PASSWORD_MARKER: str = "!UNUSABLE"
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    AUTH_URI: str = ""
    TOKEN_URI: str = ""
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file="envs/.test.env", env_prefix="TEST_")


class ProdConfig(GlobalConfig):
    DEBUG: bool = False
    model_config = SettingsConfigDict(env_file='envs/.prod.env', env_prefix='PROD_')


@lru_cache()
def get_configs(state: str | None) -> GlobalConfig:
    if state is None:
        return DevConfig(ENV_STATE="development")

    match state.casefold():
        case "production" | "prod":
            return ProdConfig(ENV_STATE="production")
        case "development" | "dev":
            return DevConfig(ENV_STATE="development")
        case "test":
            return TestConfig(ENV_STATE="test")
        case _:
            return DevConfig(ENV_STATE="develpment")


configs = get_configs(BaseConfig().ENV_STATE)
