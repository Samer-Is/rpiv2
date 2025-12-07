"""
Real-time Fleet Utilization Query

Loads Fleet.VehicleHistory from LOCAL FILE or database.
For production deployment, use local CSV file to avoid database connection.
"""

import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local data file path - use absolute path relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
LOCAL_VEHICLE_HISTORY_FILE = SCRIPT_DIR / 'data' / 'vehicle_history_local.csv'

# Try to import database dependencies (optional)
try:
    import pyodbc
    import config
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.info("Database modules not available - using local data only")


def get_utilization_from_local_file(branch_id: int = None) -> dict:
    """
    Load utilization from local CSV file (NO database connection needed).
    
    Expected CSV columns: BranchId, total_vehicles, rented_vehicles, available_vehicles
    """
    try:
        if not LOCAL_VEHICLE_HISTORY_FILE.exists():
            logger.warning(f"Local file not found: {LOCAL_VEHICLE_HISTORY_FILE}")
            return None
        
        df = pd.read_csv(LOCAL_VEHICLE_HISTORY_FILE)
        
        if branch_id:
            branch_data = df[df['BranchId'] == branch_id]
            if len(branch_data) == 0:
                logger.warning(f"No data for branch {branch_id} in local file")
                return None
            
            row = branch_data.iloc[0]
            total = int(row['total_vehicles'])
            rented = int(row['rented_vehicles'])
            available = int(row['available_vehicles'])
            utilization_pct = (rented / total * 100) if total > 0 else 0
            
            logger.info(f"✓ Local data: Branch {branch_id} = {utilization_pct:.1f}% ({rented}/{total})")
            
            return {
                'total_vehicles': total,
                'rented_vehicles': rented,
                'available_vehicles': available,
                'utilization_pct': round(utilization_pct, 1),
                'source': 'local_file'
            }
        else:
            # Return all branches
            return df.to_dict('records')
            
    except Exception as e:
        logger.error(f"Error reading local file: {e}")
        return None


def get_current_utilization(branch_id: int = None, date = None) -> dict:
    """
    Get current utilization - tries LOCAL FILE first, then database.
    
    For production: Use local CSV file (no database needed)
    For development: Can fallback to database
    
    Args:
        branch_id: Branch ID (optional, if None returns all branches)
        date: Target date (datetime or date object, default: today)
        
    Returns:
        dict with total_vehicles, rented_vehicles, available_vehicles, utilization_pct
    """
    if date is None:
        date = datetime.now()
    
    # FIRST: Try local file (for production - no DB needed)
    local_result = get_utilization_from_local_file(branch_id)
    if local_result is not None:
        return local_result
    
    # FALLBACK: Try database if available
    if not DB_AVAILABLE:
        logger.warning(f"No local data and no database - using defaults for branch {branch_id}")
        return {
            'total_vehicles': 100,
            'rented_vehicles': 50,
            'available_vehicles': 50,
            'utilization_pct': 50.0,
            'source': 'default'
        }
    
    # Convert datetime.date to datetime if needed (for SQL query compatibility)
    if hasattr(date, 'hour'):  # It's already a datetime
        pass
    else:  # It's a date object, convert to datetime at start of day
        from datetime import date as date_type
        if isinstance(date, date_type):
            date = datetime.combine(date, datetime.min.time())
    
    try:
        # Connect to database
        conn_str = (
            f"DRIVER={config.DB_CONFIG['driver']};"
            f"SERVER={config.DB_CONFIG['server']};"
            f"DATABASE={config.DB_CONFIG['database']};"
            f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
        )
        conn = pyodbc.connect(conn_str)
        
        # Query: Get latest status per vehicle in branch
        # Note: StatusIds in data are 140-155 range
        # 140 = most common (likely "Available")
        # 141, 144, 154, etc = rented/reserved/maintenance states
        query = """
        WITH LatestStatus AS (
            SELECT 
                vh.VehicleId,
                vh.BranchId,
                vh.StatusId,
                vh.OperationDateTime,
                ROW_NUMBER() OVER (PARTITION BY vh.VehicleId ORDER BY vh.OperationDateTime DESC) as rn
            FROM Fleet.VehicleHistory vh
            WHERE vh.OperationDateTime >= ?
                AND vh.OperationDateTime <= ?
        """
        
        params = [date - timedelta(days=60), date]  # Last 60 days for recent status
        
        if branch_id:
            query += " AND vh.BranchId = ?"
            params.append(branch_id)
        
        query += """
        )
        SELECT 
            BranchId,
            COUNT(*) as total_vehicles,
            SUM(CASE WHEN StatusId IN (141, 144, 146, 147, 154, 155) THEN 1 ELSE 0 END) as rented_vehicles,
            SUM(CASE WHEN StatusId = 140 THEN 1 ELSE 0 END) as available_vehicles
        FROM LatestStatus
        WHERE rn = 1
        """
        
        # CRITICAL: Filter by branch AFTER getting latest status
        if branch_id:
            query += f" AND BranchId = {branch_id}"
        
        query += " GROUP BY BranchId"
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        
        if len(df) == 0:
            logger.warning(f"No utilization data for branch {branch_id}")
            return {
                'total_vehicles': 100,
                'rented_vehicles': 50,
                'available_vehicles': 50,
                'utilization_pct': 50.0,
                'source': 'default'
            }
        
        # Get first row (should be only one if branch_id specified)
        row = df.iloc[0]
        total = int(row['total_vehicles'])
        rented = int(row['rented_vehicles'])
        available = int(row['available_vehicles'])
        
        utilization_pct = (rented / total * 100) if total > 0 else 0
        
        logger.info(f"✓ Utilization for branch {branch_id}: {utilization_pct:.1f}% ({rented}/{total})")
        
        return {
            'total_vehicles': total,
            'rented_vehicles': rented,
            'available_vehicles': available,
            'utilization_pct': round(utilization_pct, 1),
            'source': 'database',
            'query_date': date.date()
        }
        
    except Exception as e:
        logger.error(f"✗ Error querying utilization: {e}")
        logger.info("  Returning default values")
        return {
            'total_vehicles': 100,
            'rented_vehicles': 50,
            'available_vehicles': 50,
            'utilization_pct': 50.0,
            'source': 'error',
            'error': str(e)
        }


def get_all_branches_utilization(date: datetime = None) -> pd.DataFrame:
    """
    Get utilization for all branches.
    
    Args:
        date: Target date (default: today)
        
    Returns:
        DataFrame with columns: BranchId, total_vehicles, rented_vehicles, 
                                available_vehicles, utilization_pct
    """
    if date is None:
        date = datetime.now()
    
    try:
        conn_str = (
            f"DRIVER={config.DB_CONFIG['driver']};"
            f"SERVER={config.DB_CONFIG['server']};"
            f"DATABASE={config.DB_CONFIG['database']};"
            f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
        )
        conn = pyodbc.connect(conn_str)
        
        # StatusIds: 140=Available, 141/144/154=Rented/Reserved
        query = """
        WITH LatestStatus AS (
            SELECT 
                vh.VehicleId,
                vh.BranchId,
                vh.StatusId,
                vh.OperationDateTime,
                ROW_NUMBER() OVER (PARTITION BY vh.VehicleId ORDER BY vh.OperationDateTime DESC) as rn
            FROM Fleet.VehicleHistory vh
            WHERE vh.OperationDateTime >= ?
                AND vh.OperationDateTime <= ?
        )
        SELECT 
            BranchId,
            COUNT(*) as total_vehicles,
            SUM(CASE WHEN StatusId IN (141, 144, 146, 147, 154, 155) THEN 1 ELSE 0 END) as rented_vehicles,
            SUM(CASE WHEN StatusId = 140 THEN 1 ELSE 0 END) as available_vehicles
        FROM LatestStatus
        WHERE rn = 1
        GROUP BY BranchId
        ORDER BY BranchId
        """
        
        df = pd.read_sql(query, conn, params=[date - timedelta(days=60), date])
        conn.close()
        
        df['utilization_pct'] = (df['rented_vehicles'] / df['total_vehicles'] * 100).round(1)
        
        logger.info(f"✓ Retrieved utilization for {len(df)} branches")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ Error querying all branches utilization: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    logger.info("="*80)
    logger.info("FLEET UTILIZATION QUERY - TEST")
    logger.info("="*80)
    
    # Test single branch
    logger.info("\n1. Testing single branch (122)...")
    util = get_current_utilization(branch_id=122)
    logger.info(f"   Total vehicles: {util['total_vehicles']}")
    logger.info(f"   Rented: {util['rented_vehicles']}")
    logger.info(f"   Available: {util['available_vehicles']}")
    logger.info(f"   Utilization: {util['utilization_pct']}%")
    logger.info(f"   Source: {util['source']}")
    
    # Test all branches
    logger.info("\n2. Testing all branches...")
    df = get_all_branches_utilization()
    if len(df) > 0:
        logger.info(f"   Retrieved {len(df)} branches")
        logger.info("\n   Top 5 branches by utilization:")
        top5 = df.nlargest(5, 'utilization_pct')
        for _, row in top5.iterrows():
            logger.info(f"     Branch {row['BranchId']}: {row['utilization_pct']}% "
                       f"({row['rented_vehicles']}/{row['total_vehicles']})")
    
    logger.info("\n" + "="*80)
    logger.info("TEST COMPLETE")
    logger.info("="*80)

