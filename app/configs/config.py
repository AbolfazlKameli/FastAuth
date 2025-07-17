from functools import lru_cache

from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    ENV_STATE: str | None = None
    model_config = SettingsConfigDict(
        env_file='app/.env',
        extra='ignore'
    )


class GlobalConfig(BaseConfig):
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_URL: str = 'sqlite+aiosqlite:///db.sqlite3'
    REDIS_URL: RedisDsn = 'redis://localhost:6379/0'
    CELERY_BROKER_URL: str = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND: str = 'redis://localhost:6379/2'
    EMAIL_HOSTNAME: str
    EMAIL_PORT: int
    EMAIL_USE_TLS: bool = True
    EMAIL_HOST_USERNAME: str
    EMAIL_HOST_PASSWORD: str
    TIMEZONE: str


class DevConfig(GlobalConfig):
    DEBUG: bool = True
    model_config = SettingsConfigDict(env_prefix='DEV_')


class ProdConfig(GlobalConfig):
    DEBUG: bool = False
    model_config = SettingsConfigDict(env_prefix='PROD_')


@lru_cache()
def get_configs(state: str | None) -> GlobalConfig:
    try:
        match state.casefold():
            case 'production' | 'prod':
                return ProdConfig(ENV_STATE='production')
            case 'development' | 'dev':
                return DevConfig(ENV_STATE='development')
    except AttributeError:
        return DevConfig(ENV_STATE='development')


configs = get_configs(BaseConfig().ENV_STATE)
