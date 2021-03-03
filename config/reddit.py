from pydantic import BaseSettings


class RedditConfig(BaseSettings):
    id: str
    secret: str

    class Config:
        env_file = ".env"
        env_prefix = "reddit_"


reddit_config = RedditConfig()
