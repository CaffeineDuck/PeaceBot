from pydantic import BaseSettings


class Misc(BaseSettings):
    log_webhook_url: str

    class Config:
        env_file = ".env"


misc_settings = Misc()
