"""
Database session management - SQL Server connections
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import urllib

from app.core.config import get_settings

settings = get_settings()

def get_connection_string(database: str = None) -> str:
    """Build SQL Server connection string"""
    db = database or settings.SQL_DATABASE
    params = urllib.parse.quote_plus(
        f"DRIVER={{{settings.SQL_DRIVER}}};"
        f"SERVER={settings.SQL_SERVER};"
        f"DATABASE={db};"
        f"UID={settings.SQL_USERNAME};"
        f"PWD={settings.SQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    return f"mssql+pyodbc:///?odbc_connect={params}"


# Source database engine (eJarDbSTGLite / eJarDbReports - read only)
def get_source_engine(database: str):
    """Get engine for source databases (read-only)"""
    return create_engine(get_connection_string(database), echo=False)


# App database engine (RentyDynamicPricing or eJarDbSTGLite with app schemas)
def get_app_engine():
    """Get engine for application database"""
    db = settings.APP_SQL_DATABASE or settings.SQL_DATABASE
    return create_engine(get_connection_string(db), echo=False)


# Session factories
AppSessionLocal = sessionmaker(autocommit=False, autoflush=False)
Base = declarative_base()


def get_app_db() -> Session:
    """Dependency for app database session"""
    engine = get_app_engine()
    AppSessionLocal.configure(bind=engine)
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_source_db(database: str) -> Session:
    """Get session for source database"""
    engine = get_source_engine(database)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
