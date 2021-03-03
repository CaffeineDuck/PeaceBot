from pydantic import BaseSettings


class PersonalGuild(BaseSettings):
    id: int

    class Config:
        env_file = ".env"
        env_prefix = "personal_guild_"


personal_guild = PersonalGuild()
