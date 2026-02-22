from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    webhook_url: str = ""
    bot_mode: str = "polling"  # "polling" or "webhook"
    database_url: str = "sqlite:///data/db/shortgame.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
