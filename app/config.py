from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cocivil:cocivil@localhost:5432/cocivil"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://cocivil:cocivil@localhost:5432/cocivil"
    REDIS_URL: str = "redis://localhost:6379/0"

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "cocivil-docs"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    API_V1_PREFIX: str = "/api/v1"

    AI_PROVIDER: str = "claude"
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    GOOGLE_PLACES_API_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
