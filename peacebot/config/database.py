from pydantic import BaseSettings


class DatabaseConfig(BaseSettings):
    db: str
    host: str
    password: str
    port: str
    user: str

    class Config:
        env_file = ".env"
        env_prefix = "postgres_"


db_config = DatabaseConfig()
