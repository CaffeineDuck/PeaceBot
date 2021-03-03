from config import common

database_uri = common.common.database_uri

tortoise_config = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "database": database_uri.path[1:],
                "host": database_uri.host,
                "password": database_uri.password,
                "port": database_uri.port or 5432,
                "user": database_uri.user,
            },
        }
    },
    "apps": {
        "main": {"models": ["models", "aerich.models"], "default_connection": "default"}
    },
}
