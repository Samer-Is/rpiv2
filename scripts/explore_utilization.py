"""
CHUNK 4: Explore Utilization Data Structure
Understand how vehicle utilization is calculated from the rental data.
"""
import pyodbc
from datetime import datetime, date

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)

def get_connection():
    return pyodbc.connect(CONN_STR)

def run_query(cursor, query, description=""):
    print(f"\n{'='*70}")
    print(f"QUERY: {description}")
    print(f"{'='*70}")
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        print(f"Columns: {columns}")
        print(f"Row count: {len(rows)}")
        for row in rows[:20]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 4: Utilization Data Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Find vehicle/asset related tables
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%Vehicle%' OR t.name LIKE '%Asset%' OR t.name LIKE '%Car%' OR t.name LIKE '%Fleet%'
        ORDER BY s.name, t.name
    """, "Find Vehicle/Asset Tables")
    
    # 2. Check Rental.Vehicles table structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'Vehicles'
        ORDER BY ORDINAL_POSITION
    """, "Rental.Vehicles Table Structure")
    
    # 3. Sample Vehicles data
    run_query(cursor, """
        SELECT TOP 10
            v.Id, v.TenantId, v.BranchId, v.ModelId, v.StatusId,
            v.PlateNumber, v.Year, v.IsActive, v.IsDeleted
        FROM Rental.Vehicles v
        WHERE v.TenantId = 1
        ORDER BY v.Id DESC
    """, "Vehicles Sample Data")
    
    # 4. Check StatusId values distribution
    run_query(cursor, """
        SELECT 
            v.StatusId,
            COUNT(*) as VehicleCount
        FROM Rental.Vehicles v
        WHERE v.TenantId = 1 AND v.IsActive = 1 AND v.IsDeleted = 0
        GROUP BY v.StatusId
        ORDER BY VehicleCount DESC
    """, "Vehicle Status Distribution")
    
    # 5. Find status lookup table
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%Status%' OR t.name LIKE '%Enum%' OR t.name LIKE '%Lookup%'
        ORDER BY s.name, t.name
    """, "Find Status/Lookup Tables")
    
    # 6. Check VehicleStatuses table
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'VehicleStatuses'
        ORDER BY ORDINAL_POSITION
    """, "VehicleStatuses Table Structure")
    
    # 7. Get all vehicle statuses
    run_query(cursor, """
        SELECT *
        FROM Rental.VehicleStatuses
        WHERE TenantId = 1
        ORDER BY Id
    """, "All Vehicle Statuses")
    
    # 8. Check the appconfig utilization_status_config we created
    run_query(cursor, """
        SELECT *
        FROM appconfig.utilization_status_config
        ORDER BY status_id
    """, "Current Utilization Status Config")
    
    # 9. Count vehicles by branch and status
    run_query(cursor, """
        SELECT 
            v.BranchId,
            b.Name as BranchName,
            v.StatusId,
            COUNT(*) as VehicleCount
        FROM Rental.Vehicles v
        INNER JOIN Rental.Branches b ON v.BranchId = b.Id
        INNER JOIN dynamicpricing.TopBranches tb ON v.BranchId = tb.BranchId
        WHERE v.TenantId = 1 AND v.IsActive = 1 AND v.IsDeleted = 0
        GROUP BY v.BranchId, b.Name, v.StatusId
        ORDER BY v.BranchId, v.StatusId
    """, "MVP Branch Vehicle Counts by Status")
    
    # 10. Count vehicles by category and status
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            cm.CarCategoryName,
            v.StatusId,
            COUNT(*) as VehicleCount
        FROM Rental.Vehicles v
        INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
        INNER JOIN dynamicpricing.TopCategories tc ON cm.CarCategoryId = tc.CategoryId
        WHERE v.TenantId = 1 AND v.IsActive = 1 AND v.IsDeleted = 0
        GROUP BY cm.CarCategoryId, cm.CarCategoryName, v.StatusId
        ORDER BY cm.CarCategoryId, v.StatusId
    """, "MVP Category Vehicle Counts by Status")
    
    # 11. Check for historical vehicle status tracking
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%VehicleStatus%' OR t.name LIKE '%StatusHistory%' OR t.name LIKE '%StatusLog%'
        ORDER BY s.name, t.name
    """, "Find Vehicle Status History Tables")
    
    # 12. Check Contract table for rental dates
    run_query(cursor, """
        SELECT TOP 10
            c.Id, c.VehicleId, c.StatusId,
            c.StartDate, c.EndDate, c.ActualReturnDate,
            c.BranchId, c.ReturnBranchId
        FROM Rental.Contracts c
        WHERE c.TenantId = 1 AND c.Discriminator = 'Contract'
        ORDER BY c.Id DESC
    """, "Contract Sample (for date ranges)")
    
    # 13. Calculate utilization for a specific date (2025-05-31)
    # Vehicles rented out / Total available vehicles
    run_query(cursor, """
        WITH FleetCount AS (
            SELECT 
                v.BranchId,
                cm.CarCategoryId,
                COUNT(DISTINCT v.Id) as TotalVehicles
            FROM Rental.Vehicles v
            INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
            WHERE v.TenantId = 1 
              AND v.IsActive = 1 
              AND v.IsDeleted = 0
              AND v.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
              AND cm.CarCategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
            GROUP BY v.BranchId, cm.CarCategoryId
        ),
        RentedCount AS (
            SELECT 
                c.BranchId,
                cm.CarCategoryId,
                COUNT(DISTINCT c.VehicleId) as RentedVehicles
            FROM Rental.Contracts c
            INNER JOIN Rental.Vehicles v ON c.VehicleId = v.Id
            INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
            WHERE c.TenantId = 1 
              AND c.Discriminator = 'Contract'
              AND c.StatusId = 211  -- Active/Completed
              AND c.StartDate <= '2025-05-31'
              AND (c.ActualReturnDate IS NULL OR c.ActualReturnDate >= '2025-05-31')
              AND c.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
              AND cm.CarCategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
            GROUP BY c.BranchId, cm.CarCategoryId
        )
        SELECT 
            f.BranchId,
            f.CarCategoryId,
            f.TotalVehicles,
            COALESCE(r.RentedVehicles, 0) as RentedVehicles,
            CAST(COALESCE(r.RentedVehicles, 0) AS FLOAT) / CAST(f.TotalVehicles AS FLOAT) as Utilization
        FROM FleetCount f
        LEFT JOIN RentedCount r ON f.BranchId = r.BranchId AND f.CarCategoryId = r.CarCategoryId
        ORDER BY f.BranchId, f.CarCategoryId
    """, "Utilization Calculation for 2025-05-31")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("UTILIZATION EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
