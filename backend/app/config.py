from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://sorteos:sorteos@localhost:5438/sorteos_db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    app_base_url: str = "http://localhost:5173"

    admin_username: str = "admin"
    admin_password: str = "admin123"
    jwt_secret: str = "cambia-este-secreto-en-produccion"
    jwt_expire_minutes: int = 60 * 24


settings = Settings()
