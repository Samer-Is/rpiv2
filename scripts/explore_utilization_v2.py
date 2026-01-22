"""
CHUNK 4: Corrected Utilization Data Exploration
Tables are in Fleet schema, not Rental schema.
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
        for row in rows[:25]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 4: Corrected Utilization Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fleet.Vehicles table structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Fleet' AND TABLE_NAME = 'Vehicles'
        ORDER BY ORDINAL_POSITION
    """, "Fleet.Vehicles Table Structure")
    
    # 2. Sample Vehicles data
    run_query(cursor, """
        SELECT TOP 10
            v.Id, v.TenantId, v.BranchId, v.ModelId, v.StatusId,
            v.PlateNumber, v.Year, v.IsActive, v.IsDeleted
        FROM Fleet.Vehicles v
        WHERE v.TenantId = 1
        ORDER BY v.Id DESC
    """, "Vehicles Sample Data")
    
    # 3. Check StatusId values distribution
    run_query(cursor, """
        SELECT 
            v.StatusId,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
        GROUP BY v.StatusId
        ORDER BY VehicleCount DESC
    """, "Vehicle Status Distribution")
    
    # 4. Check dbo.Lookups for status names
    run_query(cursor, """
        SELECT TOP 30 Id, Name, Type, Value, IsActive
        FROM dbo.Lookups
        WHERE Type LIKE '%Status%' OR Type LIKE '%Vehicle%'
        ORDER BY Type, Id
    """, "dbo.Lookups Status Types")
    
    # 5. Check LookupsTypes table
    run_query(cursor, """
        SELECT *
        FROM dbo.LookupsTypes
        WHERE Name LIKE '%Status%' OR Name LIKE '%Vehicle%'
        ORDER BY Id
    """, "LookupsTypes - Status Related")
    
    # 6. Find the exact lookup type for vehicle statuses
    run_query(cursor, """
        SELECT DISTINCT Type, COUNT(*) as Count
        FROM dbo.Lookups
        GROUP BY Type
        ORDER BY Type
    """, "All Lookup Types")
    
    # 7. Get CarStatus lookups
    run_query(cursor, """
        SELECT Id, Name, Type, Value, IsActive
        FROM dbo.Lookups
        WHERE Type = 'CarStatus'
        ORDER BY Id
    """, "CarStatus Lookups")
    
    # 8. Count vehicles by branch and status for MVP branches
    run_query(cursor, """
        SELECT 
            v.BranchId,
            LEFT(b.Name, 50) as BranchName,
            v.StatusId,
            l.Name as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        LEFT JOIN Reservation.Branches b ON v.BranchId = b.Id
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id AND l.Type = 'CarStatus'
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
          AND v.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
        GROUP BY v.BranchId, b.Name, v.StatusId, l.Name
        ORDER BY v.BranchId, VehicleCount DESC
    """, "MVP Branch Vehicle Counts by Status")
    
    # 9. Count vehicles by category and status for MVP categories
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            LEFT(cm.CarCategoryName, 40) as CategoryName,
            v.StatusId,
            l.Name as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id AND l.Type = 'CarStatus'
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
          AND cm.CarCategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
        GROUP BY cm.CarCategoryId, cm.CarCategoryName, v.StatusId, l.Name
        ORDER BY cm.CarCategoryId, VehicleCount DESC
    """, "MVP Category Vehicle Counts by Status")
    
    # 10. Check Reservation.Contracts for rental data
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Reservation' AND TABLE_NAME = 'Contracts'
        ORDER BY ORDINAL_POSITION
    """, "Reservation.Contracts Table Structure")
    
    # 11. Sample Contract data
    run_query(cursor, """
        SELECT TOP 10
            c.Id, c.VehicleId, c.StatusId,
            c.StartDate, c.EndDate, c.ActualReturnDate,
            c.BranchId, c.ReturnBranchId, c.Discriminator
        FROM Reservation.Contracts c
        WHERE c.TenantId = 1 AND c.Discriminator = 'Contract'
        ORDER BY c.Id DESC
    """, "Contract Sample Data")
    
    # 12. Define which statuses count as "rented" vs "available"
    # Status 211 = Contract confirmed/active
    run_query(cursor, """
        SELECT DISTINCT c.StatusId, l.Name as StatusName, COUNT(*) as ContractCount
        FROM Reservation.Contracts c
        LEFT JOIN dbo.Lookups l ON c.StatusId = l.Id
        WHERE c.TenantId = 1 AND c.Discriminator = 'Contract'
        GROUP BY c.StatusId, l.Name
        ORDER BY ContractCount DESC
    """, "Contract Status Distribution")
    
    # 13. Calculate current utilization (vehicles on active contracts)
    run_query(cursor, """
        WITH FleetCount AS (
            SELECT 
                v.BranchId,
                cm.CarCategoryId,
                COUNT(DISTINCT v.Id) as TotalVehicles
            FROM Fleet.Vehicles v
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
            WHERE v.TenantId = 1 
              AND v.IsDeleted = 0
              AND v.StatusId NOT IN (104)  -- Exclude sold/removed
              AND v.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
              AND cm.CarCategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
            GROUP BY v.BranchId, cm.CarCategoryId
        ),
        RentedCount AS (
            SELECT 
                c.BranchId,
                cm.CarCategoryId,
                COUNT(DISTINCT c.VehicleId) as RentedVehicles
            FROM Reservation.Contracts c
            INNER JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
            WHERE c.TenantId = 1 
              AND c.Discriminator = 'Contract'
              AND c.StatusId = 211  -- Active rental
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
            ROUND(CAST(COALESCE(r.RentedVehicles, 0) AS FLOAT) / CAST(f.TotalVehicles AS FLOAT), 3) as Utilization
        FROM FleetCount f
        LEFT JOIN RentedCount r ON f.BranchId = r.BranchId AND f.CarCategoryId = r.CarCategoryId
        WHERE f.TotalVehicles > 0
        ORDER BY f.BranchId, f.CarCategoryId
    """, "Utilization Calculation for 2025-05-31")
    
    # 14. Get vehicle statuses that mean "rented" (from actual data)
    run_query(cursor, """
        SELECT 
            v.StatusId,
            l.Name as StatusName,
            COUNT(*) as VehicleCount,
            COUNT(CASE WHEN c.Id IS NOT NULL THEN 1 END) as WithActiveContract
        FROM Fleet.Vehicles v
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id AND l.Type = 'CarStatus'
        LEFT JOIN Reservation.Contracts c ON v.Id = c.VehicleId 
            AND c.Discriminator = 'Contract'
            AND c.StatusId = 211
            AND c.StartDate <= GETDATE()
            AND (c.ActualReturnDate IS NULL OR c.ActualReturnDate >= GETDATE())
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
        GROUP BY v.StatusId, l.Name
        ORDER BY VehicleCount DESC
    """, "Vehicle Status vs Active Contracts")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("UTILIZATION EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
