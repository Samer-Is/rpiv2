"""
Database session management - SQL Server connections

Supports:
- Windows Authentication (Trusted_Connection=yes) for local development
- SQL Authentication for production deployments
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import urllib
import pyodbc

from app.core.config import get_settings

settings = get_settings()


def get_sqlalchemy_connection_string(database: str = None) -> str:
    """Build SQLAlchemy SQL Server connection string"""
    db = database or settings.SQL_DATABASE
    
    if settings.SQL_USE_WINDOWS_AUTH:
        params = urllib.parse.quote_plus(
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={db};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )
    else:
        params = urllib.parse.quote_plus(
            f"DRIVER={{{settings.SQL_DRIVER}}};"
            f"SERVER={settings.SQL_SERVER};"
            f"DATABASE={db};"
            f"UID={settings.SQL_USERNAME};"
            f"PWD={settings.SQL_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
    return f"mssql+pyodbc:///?odbc_connect={params}"


def get_pyodbc_connection(database: str = None) -> pyodbc.Connection:
    """Get direct pyodbc connection for raw SQL queries"""
    conn_str = settings.get_connection_string(database)
    return pyodbc.connect(conn_str)


# Source database engine (eJarDbSTGLite / eJarDbReports - read only)
def get_source_engine(database: str = None):
    """Get engine for source databases (read-only)"""
    db = database or settings.SQL_DATABASE
    return create_engine(get_sqlalchemy_connection_string(db), echo=False)


# App database engine (eJarDbSTGLite with dynamicpricing and appconfig schemas)
def get_app_engine():
    """Get engine for application database"""
    return create_engine(get_sqlalchemy_connection_string(settings.SQL_DATABASE), echo=False)


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


def get_source_db(database: str = None) -> Session:
    """Get session for source database"""
    engine = get_source_engine(database)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
