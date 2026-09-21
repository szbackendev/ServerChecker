from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    fastapi_server: str

    model_config = SettingsConfigDict(
        env_file="agent_settings.env",  # если другое название файла окружения, то изменить somedata.env на ваше имяфайла.env
        env_file_encoding="utf-8",
    )


settings = Settings() #type: ignore

