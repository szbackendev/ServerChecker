from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TESTMESSAGE: str
    private_key: str
    public_key: str
    algorithm: str
    access_key: str
    admin_panel_url: str
    USERS_DB_NAME: str

    model_config = SettingsConfigDict(
        env_file="somedata.env",  # если другое название файла окружения, то изменить somedata.env на ваше имяфайла.env
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore
