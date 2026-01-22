"""
CHUNK 4: Final Utilization Exploration
With correct column names: LookupTypeId, Text
"""
import pyodbc
from datetime import datetime

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
        for row in rows[:30]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 4: Final Utilization Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Get Car Status lookups (LookupTypeId = 9)
    run_query(cursor, """
        SELECT l.Id, l.Text as StatusName, l.LookupTypeId, l.IsActive
        FROM dbo.Lookups l
        WHERE l.LookupTypeId = 9  -- Car Status
        ORDER BY l.Id
    """, "Car Status Lookups (LookupTypeId=9)")
    
    # 2. Vehicle Status distribution with names
    run_query(cursor, """
        SELECT 
            v.StatusId,
            l.Text as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
        GROUP BY v.StatusId, l.Text
        ORDER BY VehicleCount DESC
    """, "Vehicle Status Names and Counts")
    
    # 3. MVP Branch Vehicle Counts by Status
    run_query(cursor, """
        SELECT 
            v.VehicleBranchId as BranchId,
            LEFT(b.Name, 50) as BranchName,
            v.StatusId,
            LEFT(l.Text, 30) as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        INNER JOIN Rental.Branches b ON v.VehicleBranchId = b.Id
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
          AND v.VehicleBranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
        GROUP BY v.VehicleBranchId, b.Name, v.StatusId, l.Text
        ORDER BY v.VehicleBranchId, VehicleCount DESC
    """, "MVP Branch Vehicle Counts by Status")
    
    # 4. MVP Category Vehicle Counts by Status  
    run_query(cursor, """
        SELECT 
            cm.CategoryId,
            LEFT(cc.Name, 40) as CategoryName,
            v.StatusId,
            LEFT(l.Text, 30) as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
        INNER JOIN Fleet.CarCategories cc ON cm.CategoryId = cc.Id
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
          AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
        GROUP BY cm.CategoryId, cc.Name, v.StatusId, l.Text
        ORDER BY cm.CategoryId, VehicleCount DESC
    """, "MVP Category Vehicle Counts by Status")
    
    # 5. Individual.Contracts from actual schema
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name = 'Contracts'
        ORDER BY s.name
    """, "Find Contracts Tables by Schema")
    
    # 6. Check Corporate.Contracts structure (likely for all contracts)
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Corporate' AND TABLE_NAME = 'Contracts'
        ORDER BY ORDINAL_POSITION
    """, "Corporate.Contracts Structure")
    
    # 7. Check dynamicpricing.TrainingData for rental counts
    run_query(cursor, """
        SELECT TOP 20 *
        FROM dynamicpricing.TrainingData
        ORDER BY rental_date DESC
    """, "dynamicpricing.TrainingData Sample")
    
    # 8. Calculate fleet size per branch x category
    run_query(cursor, """
        SELECT 
            v.VehicleBranchId as BranchId,
            cm.CategoryId,
            COUNT(DISTINCT v.Id) as FleetSize
        FROM Fleet.Vehicles v
        INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
        WHERE v.TenantId = 1 
          AND v.IsDeleted = 0
          AND v.VehicleBranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
          AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
        GROUP BY v.VehicleBranchId, cm.CategoryId
        ORDER BY v.VehicleBranchId, cm.CategoryId
    """, "Fleet Size per Branch x Category")
    
    # 9. Determine which statuses mean "rented out"
    # Status 143 = Available, others indicate different states
    run_query(cursor, """
        SELECT 
            l.Id as StatusId,
            l.Text as StatusName,
            CASE 
                WHEN l.Id IN (141, 149) THEN 'RENTED'  -- Rented/On Trip
                WHEN l.Id = 143 THEN 'AVAILABLE'
                WHEN l.Id IN (140, 144, 145, 147, 148, 150) THEN 'UNAVAILABLE'  -- Maintenance, Reserved, etc.
                ELSE 'OTHER'
            END as UtilizationType,
            COUNT(v.Id) as VehicleCount
        FROM dbo.Lookups l
        LEFT JOIN Fleet.Vehicles v ON l.Id = v.StatusId AND v.TenantId = 1 AND v.IsDeleted = 0
        WHERE l.LookupTypeId = 9
        GROUP BY l.Id, l.Text
        ORDER BY l.Id
    """, "Status Classification for Utilization")
    
    # 10. Calculate utilization based on vehicle status
    # Utilization = Rented / (Rented + Available)
    run_query(cursor, """
        WITH VehicleCounts AS (
            SELECT 
                v.VehicleBranchId as BranchId,
                cm.CategoryId,
                SUM(CASE WHEN v.StatusId IN (141, 149) THEN 1 ELSE 0 END) as RentedCount,
                SUM(CASE WHEN v.StatusId = 143 THEN 1 ELSE 0 END) as AvailableCount,
                COUNT(DISTINCT v.Id) as TotalFleet
            FROM Fleet.Vehicles v
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
            WHERE v.TenantId = 1 
              AND v.IsDeleted = 0
              AND v.VehicleBranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
              AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
            GROUP BY v.VehicleBranchId, cm.CategoryId
        )
        SELECT 
            vc.BranchId,
            vc.CategoryId,
            vc.RentedCount,
            vc.AvailableCount,
            vc.TotalFleet,
            CASE 
                WHEN (vc.RentedCount + vc.AvailableCount) > 0 
                THEN ROUND(CAST(vc.RentedCount AS FLOAT) / (vc.RentedCount + vc.AvailableCount), 3)
                ELSE 0 
            END as Utilization
        FROM VehicleCounts vc
        ORDER BY vc.BranchId, vc.CategoryId
    """, "Current Utilization by Branch x Category")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("FINAL UTILIZATION EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
