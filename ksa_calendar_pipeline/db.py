"""
KSA Calendar Pipeline - Database Module
Handles SQL Server connection and table operations.
"""
import pyodbc
import pandas as pd
from datetime import datetime
import logging
from typing import Optional

from .config import SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD, DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)


def get_connection_string() -> str:
    """Build SQL Server connection string"""
    if SQL_USERNAME and SQL_PASSWORD:
        # SQL Server Authentication
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={SQL_SERVER};"
            f"Database={SQL_DATABASE};"
            f"UID={SQL_USERNAME};"
            f"PWD={SQL_PASSWORD};"
        )
    else:
        # Windows Authentication
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={SQL_SERVER};"
            f"Database={SQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )


def get_connection():
    """Get database connection"""
    return pyodbc.connect(get_connection_string())


def create_tables_if_not_exist():
    """
    Create ksa_holidays and ksa_daily_event_signal tables if they don't exist.
    Tables are created in the dynamicpricing schema.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create ksa_holidays table
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dynamicpricing' AND TABLE_NAME = 'ksa_holidays'
            )
            BEGIN
                CREATE TABLE dynamicpricing.ksa_holidays (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    tenant_id INT NOT NULL DEFAULT 1,
                    holiday_date DATE NOT NULL,
                    holiday_name NVARCHAR(200) NOT NULL,
                    holiday_name_ar NVARCHAR(200),
                    holiday_type NVARCHAR(50),  -- 'National', 'Religious', 'Observance', etc.
                    is_public_holiday BIT DEFAULT 1,
                    source NVARCHAR(50) DEFAULT 'calendarific',
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE(),
                    CONSTRAINT UQ_ksa_holidays_date UNIQUE (tenant_id, holiday_date, holiday_name)
                );
                
                CREATE INDEX IX_ksa_holidays_date 
                ON dynamicpricing.ksa_holidays (tenant_id, holiday_date);
                
                PRINT 'Created dynamicpricing.ksa_holidays table';
            END
        """)
        
        # Create ksa_daily_event_signal table
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dynamicpricing' AND TABLE_NAME = 'ksa_daily_event_signal'
            )
            BEGIN
                CREATE TABLE dynamicpricing.ksa_daily_event_signal (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    tenant_id INT NOT NULL DEFAULT 1,
                    event_date DATE NOT NULL,
                    city_name NVARCHAR(100) NOT NULL,
                    gdelt_volume INT DEFAULT 0,
                    gdelt_score DECIMAL(8, 4) DEFAULT 0,  -- log(1 + volume)
                    source NVARCHAR(50) DEFAULT 'gdelt',
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE(),
                    CONSTRAINT UQ_ksa_events_date_city UNIQUE (tenant_id, event_date, city_name)
                );
                
                CREATE INDEX IX_ksa_events_date_city 
                ON dynamicpricing.ksa_daily_event_signal (tenant_id, event_date, city_name);
                
                PRINT 'Created dynamicpricing.ksa_daily_event_signal table';
            END
        """)
        
        conn.commit()
        logger.info("KSA calendar tables created/verified")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def upsert_holidays(df: pd.DataFrame, tenant_id: int = DEFAULT_TENANT_ID):
    """
    Upsert holidays data into ksa_holidays table.
    
    Expected DataFrame columns:
    - date: Date of holiday
    - holiday_name: Name in English
    - holiday_type: Type of holiday
    - holiday_name_ar: Name in Arabic (optional)
    - is_public_holiday: Boolean (optional)
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to upsert_holidays")
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        for _, row in df.iterrows():
            holiday_date = row['date']
            holiday_name = row['holiday_name']
            holiday_type = row.get('holiday_type', 'Unknown')
            holiday_name_ar = row.get('holiday_name_ar', None)
            is_public = row.get('is_public_holiday', True)
            
            cursor.execute("""
                MERGE INTO dynamicpricing.ksa_holidays AS target
                USING (SELECT ? as tenant_id, ? as holiday_date, ? as holiday_name) AS source
                ON target.tenant_id = source.tenant_id 
                   AND target.holiday_date = source.holiday_date 
                   AND target.holiday_name = source.holiday_name
                WHEN MATCHED THEN
                    UPDATE SET
                        holiday_type = ?,
                        holiday_name_ar = ?,
                        is_public_holiday = ?,
                        updated_at = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (tenant_id, holiday_date, holiday_name, holiday_type, 
                            holiday_name_ar, is_public_holiday)
                    VALUES (?, ?, ?, ?, ?, ?);
            """, [
                tenant_id, holiday_date, holiday_name,
                holiday_type, holiday_name_ar, is_public,
                tenant_id, holiday_date, holiday_name, holiday_type, 
                holiday_name_ar, is_public
            ])
            count += 1
        
        conn.commit()
        logger.info(f"Upserted {count} holidays")
        return count
        
    except Exception as e:
        logger.error(f"Error upserting holidays: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


def upsert_event_signal(df: pd.DataFrame, tenant_id: int = DEFAULT_TENANT_ID):
    """
    Upsert event signal data into ksa_daily_event_signal table.
    
    Expected DataFrame columns:
    - date: Event date
    - city_name: City name
    - gdelt_volume: Raw article count
    - gdelt_score: log(1 + volume)
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to upsert_event_signal")
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    count = 0
    
    try:
        for _, row in df.iterrows():
            event_date = row['date']
            city_name = row['city_name']
            gdelt_volume = row.get('gdelt_volume', 0)
            gdelt_score = row.get('gdelt_score', 0)
            
            cursor.execute("""
                MERGE INTO dynamicpricing.ksa_daily_event_signal AS target
                USING (SELECT ? as tenant_id, ? as event_date, ? as city_name) AS source
                ON target.tenant_id = source.tenant_id 
                   AND target.event_date = source.event_date 
                   AND target.city_name = source.city_name
                WHEN MATCHED THEN
                    UPDATE SET
                        gdelt_volume = ?,
                        gdelt_score = ?,
                        updated_at = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (tenant_id, event_date, city_name, gdelt_volume, gdelt_score)
                    VALUES (?, ?, ?, ?, ?);
            """, [
                tenant_id, event_date, city_name,
                gdelt_volume, gdelt_score,
                tenant_id, event_date, city_name, gdelt_volume, gdelt_score
            ])
            count += 1
        
        conn.commit()
        logger.info(f"Upserted {count} event signals")
        return count
        
    except Exception as e:
        logger.error(f"Error upserting event signals: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()


def get_holidays_count(tenant_id: int = DEFAULT_TENANT_ID) -> dict:
    """Get holiday count statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(holiday_date) as min_date,
                MAX(holiday_date) as max_date,
                COUNT(DISTINCT YEAR(holiday_date)) as years
            FROM dynamicpricing.ksa_holidays
            WHERE tenant_id = ?
        """, [tenant_id])
        
        row = cursor.fetchone()
        return {
            "total": row[0],
            "min_date": row[1].isoformat() if row[1] else None,
            "max_date": row[2].isoformat() if row[2] else None,
            "years": row[3]
        }
    except Exception as e:
        logger.error(f"Error getting holiday count: {e}")
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_events_count(tenant_id: int = DEFAULT_TENANT_ID) -> dict:
    """Get event signal count statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MIN(event_date) as min_date,
                MAX(event_date) as max_date,
                COUNT(DISTINCT city_name) as cities
            FROM dynamicpricing.ksa_daily_event_signal
            WHERE tenant_id = ?
        """, [tenant_id])
        
        row = cursor.fetchone()
        return {
            "total": row[0],
            "min_date": row[1].isoformat() if row[1] else None,
            "max_date": row[2].isoformat() if row[2] else None,
            "cities": row[3]
        }
    except Exception as e:
        logger.error(f"Error getting events count: {e}")
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()
