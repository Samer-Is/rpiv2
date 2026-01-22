"""
Application configuration - loaded from environment variables
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    APP_NAME: str = "Renty Dynamic Pricing"
    DEBUG: bool = False
    
    # Database - SQL Server
    SQL_SERVER: str = ""
    SQL_DATABASE: str = ""
    SQL_USERNAME: str = ""
    SQL_PASSWORD: str = ""
    SQL_DRIVER: str = "ODBC Driver 17 for SQL Server"
    
    # App Database (for appconfig + dynamicpricing schemas)
    APP_SQL_DATABASE: str = ""
    
    # JWT Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    
    # External APIs
    CALENDARIFIC_API_KEY: str = ""
    BOOKING_COM_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
