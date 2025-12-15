from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Animerch"
    # UPDATED: Using animerch_user instead of root
    DATABASE_URL: str = "mysql+mysqlconnector://animerch_user:yourpassword@localhost/animerch_db"
    SECRET_KEY: str = "your_super_secret_key_change_this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
