from pydantic import BaseSettings

class DbConfig(BaseSettings):
    user: str
    password: str
    db: str
    port: int
    host: str

    class Config:
        env_file = ".env"
        env_prefix = "postgres_"


db_config = DbConfig()
