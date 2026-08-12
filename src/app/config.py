from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = True
    
    DATABASE_URL: str
    
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    APPLE_CLIENT_ID: str
    APPLE_TEAM_ID: str
    APPLE_KEY_ID: str
    
    IP_API_KEY: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
settings = Settings()