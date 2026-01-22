"""
Health check router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_app_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "dynamic-pricing-api", "version": "0.1.0"}


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_app_db)):
    """Health check with database connectivity verification."""
    try:
        # Test connection with simple query
        result = db.execute(text("SELECT 1 as test, GETUTCDATE() as server_time")).fetchone()
        
        # Check appconfig schema exists
        schema_check = db.execute(text("""
            SELECT COUNT(*) as table_count 
            FROM sys.tables t 
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id 
            WHERE s.name = 'appconfig'
        """)).fetchone()
        
        return {
            "status": "healthy",
            "service": "dynamic-pricing-api",
            "version": "0.1.0",
            "database": {
                "connected": True,
                "server_time": str(result.server_time),
                "appconfig_tables": schema_check.table_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "dynamic-pricing-api",
            "version": "0.1.0",
            "database": {
                "connected": False,
                "error": str(e)
            }
        }
