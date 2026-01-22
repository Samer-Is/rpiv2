"""
CHUNK 4: Deep Exploration of Fleet and Lookup Tables
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
    print("CHUNK 4: Deep Table Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. dbo.Lookups structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Lookups'
        ORDER BY ORDINAL_POSITION
    """, "dbo.Lookups Table Structure")
    
    # 2. Get Car Status lookups using TypeId
    run_query(cursor, """
        SELECT l.Id, l.Name, l.TypeId, lt.Name as TypeName
        FROM dbo.Lookups l
        INNER JOIN dbo.LookupsTypes lt ON l.TypeId = lt.Id
        WHERE lt.Id = 9  -- Car Status type
        ORDER BY l.Id
    """, "Car Status Lookups (TypeId=9)")
    
    # 3. Fleet.CarModels structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Fleet' AND TABLE_NAME = 'CarModels'
        ORDER BY ORDINAL_POSITION
    """, "Fleet.CarModels Structure")
    
    # 4. Sample Fleet.CarModels
    run_query(cursor, """
        SELECT TOP 10 *
        FROM Fleet.CarModels
        WHERE TenantId = 1
    """, "Fleet.CarModels Sample")
    
    # 5. Fleet.Vehicles key columns
    run_query(cursor, """
        SELECT TOP 10
            v.Id, v.TenantId, v.VehicleBranchId as BranchId, v.ModelId, v.StatusId,
            v.PlateNo, v.Year, v.IsDeleted
        FROM Fleet.Vehicles v
        WHERE v.TenantId = 1
        ORDER BY v.Id DESC
    """, "Fleet.Vehicles Key Columns")
    
    # 6. Vehicle Status names
    run_query(cursor, """
        SELECT 
            v.StatusId,
            l.Name as StatusName,
            COUNT(*) as VehicleCount
        FROM Fleet.Vehicles v
        LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id
        WHERE v.TenantId = 1 AND v.IsDeleted = 0
        GROUP BY v.StatusId, l.Name
        ORDER BY VehicleCount DESC
    """, "Vehicle Status Names and Counts")
    
    # 7. Find the Contracts table schema
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%Contract%'
        ORDER BY s.name, t.name
    """, "Find Contracts Table")
    
    # 8. Individual.Contracts structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Individual' AND TABLE_NAME = 'Contracts'
        ORDER BY ORDINAL_POSITION
    """, "Individual.Contracts Structure")
    
    # 9. Sample Contracts
    run_query(cursor, """
        SELECT TOP 10
            c.Id, c.VehicleId, c.StatusId,
            c.StartDate, c.EndDate, c.ActualReturnDate,
            c.BranchId, c.ReturnBranchId, c.Discriminator
        FROM Individual.Contracts c
        WHERE c.TenantId = 1 AND c.Discriminator = 'Contract'
        ORDER BY c.Id DESC
    """, "Individual.Contracts Sample")
    
    # 10. Contract Status distribution
    run_query(cursor, """
        SELECT 
            c.StatusId,
            l.Name as StatusName,
            COUNT(*) as ContractCount
        FROM Individual.Contracts c
        LEFT JOIN dbo.Lookups l ON c.StatusId = l.Id
        WHERE c.TenantId = 1 AND c.Discriminator = 'Contract'
        GROUP BY c.StatusId, l.Name
        ORDER BY ContractCount DESC
    """, "Contract Status Distribution")
    
    # 11. Fleet.CarCategories check
    run_query(cursor, """
        SELECT *
        FROM Fleet.CarCategories
        WHERE TenantId = 1
        ORDER BY Id
    """, "Fleet.CarCategories")
    
    # 12. Get CategoryId from CarModels
    run_query(cursor, """
        SELECT TOP 20
            cm.Id as ModelId,
            cm.Name as ModelName,
            cm.CategoryId,
            cc.Name as CategoryName
        FROM Fleet.CarModels cm
        INNER JOIN Fleet.CarCategories cc ON cm.CategoryId = cc.Id
        WHERE cm.TenantId = 1
        ORDER BY cm.CategoryId, cm.Id
    """, "CarModels with Categories")
    
    # 13. Check branches table schema
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%Branch%'
        ORDER BY s.name, t.name
    """, "Find Branches Table")
    
    # 14. Individual.Branches sample
    run_query(cursor, """
        SELECT TOP 10 Id, Name, CityId, TenantId, IsActive, IsDeleted
        FROM Individual.Branches
        WHERE TenantId = 1
        ORDER BY Id
    """, "Individual.Branches Sample")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("DEEP EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
