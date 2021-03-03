import ssl

from pydantic import BaseSettings, PostgresDsn

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class Settings(BaseSettings):

    database_url: PostgresDsn
    secret: str

    class Config:
        env_file = ".env"
        fields = {"database_uri": {"env": ["database_uri", "database_url", "database"]}}


common = Settings()
