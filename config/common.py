from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):

    database_uri: PostgresDsn

    class Config:
        env_file = ".env"
        fields = {"database_uri": {"env": ["database_uri", "database_url", "database"]}}


config = Settings()
