"""
Application configuration - loaded from environment variables

Database Connection:
- Uses Windows Authentication (Trusted_Connection=yes) for local development
- Source DBs: eJarDbSTGLite, eJarDbReports
- App schemas: dynamicpricing (existing), appconfig (to create) in eJarDbSTGLite
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    APP_NAME: str = "Renty Dynamic Pricing"
    DEBUG: bool = False
    
    # Database - SQL Server
    # YELO Tenant ID is 1
    SQL_SERVER: str = "localhost"
    SQL_DATABASE: str = "eJarDbSTGLite"  # Main source DB
    SQL_DATABASE_REPORTS: str = "eJarDbReports"  # Reports DB
    SQL_USERNAME: str = ""  # Empty for Windows Auth
    SQL_PASSWORD: str = ""  # Empty for Windows Auth
    SQL_DRIVER: str = "ODBC Driver 17 for SQL Server"
    SQL_USE_WINDOWS_AUTH: bool = True  # Use Trusted_Connection=yes
    
    # YELO Tenant Configuration
    MVP_TENANT_ID: int = 1  # YELO tenant ID
    MVP_TENANT_NAME: str = "Yelo"
    
    # JWT Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    
    # External APIs
    CALENDARIFIC_API_KEY: str = ""
    BOOKING_COM_API_KEY: str = ""
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    
    # Simulation Date (for development/testing)
    # Today is 2025-05-31, validation period starts 2025-06-01
    SIMULATION_TODAY: str = "2025-05-31"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_connection_string(self, database: str = None) -> str:
        """Build SQL Server connection string"""
        db = database or self.SQL_DATABASE
        if self.SQL_USE_WINDOWS_AUTH:
            return (
                f"Driver={{{self.SQL_DRIVER}}};"
                f"Server={self.SQL_SERVER};"
                f"Database={db};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"Driver={{{self.SQL_DRIVER}}};"
                f"Server={self.SQL_SERVER};"
                f"Database={db};"
                f"UID={self.SQL_USERNAME};"
                f"PWD={self.SQL_PASSWORD};"
            )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance for convenience
settings = get_settings()
