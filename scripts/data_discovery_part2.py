"""
Data Discovery Part 2 - Top Branches and Models for MVP
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
    print(f"\n{'='*60}")
    print(f"QUERY: {description}")
    print(f"{'='*60}")
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
    print("DYNAMIC PRICING DATA DISCOVERY - PART 2 (MVP Scope)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Top 10 branches by individual rental contract count (YELO TenantId=1)
    # Filter: Discriminator = 'Contract' (individual rentals), StatusId = 211 (Delivered)
    run_query(cursor, """
        SELECT TOP 15 
            c.PickupBranchId as BranchId,
            b.Name as BranchName,
            COUNT(*) as ContractCount
        FROM Rental.Contract c
        INNER JOIN Rental.Branches b ON c.PickupBranchId = b.Id
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211  -- Delivered
          AND c.Start >= '2022-01-01'
        GROUP BY c.PickupBranchId, b.Name
        ORDER BY ContractCount DESC
    """, "Top 15 Branches by Individual Rental Volume (YELO, 2022+)")
    
    # 2. Top car models by rental count (individual rentals)
    # Need to join with vehicles to get model info
    run_query(cursor, """
        SELECT TOP 15
            cm.Id as ModelId,
            cm.CarModelName,
            cm.CarCategoryName,
            COUNT(*) as RentalCount
        FROM Rental.Contract c
        INNER JOIN Rental.Vehicles v ON c.VehicleId = v.Id
        INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2022-01-01'
        GROUP BY cm.Id, cm.CarModelName, cm.CarCategoryName
        ORDER BY RentalCount DESC
    """, "Top 15 Car Models by Individual Rental Volume (YELO, 2022+)")
    
    # 3. Check Rental.Vehicles table structure
    run_query(cursor, """
        SELECT TOP 5 v.Id, v.ModelId, v.PlateNo, v.TenantId, v.StatusId
        FROM Rental.Vehicles v
        WHERE v.TenantId = 1
    """, "Vehicles Table Sample")
    
    # 4. Contract to Base Price join - find "Trip Days" price (ItemTypeId = 1)
    run_query(cursor, """
        SELECT TOP 10
            c.Id as ContractId,
            c.Start,
            c.[End],
            c.PickupBranchId,
            c.DailyRateAmount,
            cpid.UnitPrice as TripDaysUnitPrice,
            cpid.TotalPrice as TripDaysTotalPrice,
            cpid.Quantity as TripDaysQuantity
        FROM Rental.Contract c
        INNER JOIN Rental.ContractsPaymentsItemsDetails cpid ON c.Id = cpid.ContractId
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND cpid.ItemTypeId = 1  -- Trip Days
          AND c.Start >= '2023-01-01'
        ORDER BY c.Start DESC
    """, "Contract with Trip Days Base Price")
    
    # 5. Check what data exists in dynamicpricing schema tables
    run_query(cursor, """
        SELECT COUNT(*) as RowCount FROM dynamicpricing.TrainingData
    """, "TrainingData Row Count")
    
    run_query(cursor, """
        SELECT COUNT(*) as RowCount FROM dynamicpricing.ValidationData
    """, "ValidationData Row Count")
    
    run_query(cursor, """
        SELECT * FROM dynamicpricing.TopBranches
    """, "TopBranches Content")
    
    run_query(cursor, """
        SELECT * FROM dynamicpricing.TopCategories
    """, "TopCategories Content")
    
    # 6. Find Vehicles table in correct schema
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%Vehicle%'
        ORDER BY s.name, t.name
    """, "Find Vehicles Tables")
    
    # 7. Check Fleet schema for VehiclesUtilization
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'Fleet'
        ORDER BY t.name
    """, "Fleet Schema Tables")
    
    # 8. Total branches count
    run_query(cursor, """
        SELECT COUNT(*) as TotalBranches 
        FROM Rental.Branches 
        WHERE TenantId = 1 AND IsActive = 1
    """, "Total Active Branches for YELO")
    
    # 9. Total car models count
    run_query(cursor, """
        SELECT COUNT(*) as TotalModels 
        FROM Rental.CarModels 
        WHERE TenantId = 1
    """, "Total Car Models for YELO")
    
    # 10. Contract date distribution by month (last 2 years)
    run_query(cursor, """
        SELECT 
            YEAR(c.Start) as Year,
            MONTH(c.Start) as Month,
            COUNT(*) as ContractCount
        FROM Rental.Contract c
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2023-01-01'
        GROUP BY YEAR(c.Start), MONTH(c.Start)
        ORDER BY Year DESC, Month DESC
    """, "Monthly Individual Rental Distribution (2023+)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("DATA DISCOVERY PART 2 COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
