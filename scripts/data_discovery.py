"""
Data Discovery Script for Dynamic Pricing Tool - CHUNK 1
Connects to SQL Server and explores the database structure for YELO tenant.
"""
import pyodbc
import json
from datetime import datetime

# Connection string for Windows Authentication
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)

def get_connection():
    """Establish SQL Server connection with Windows Auth."""
    return pyodbc.connect(CONN_STR)

def run_query(cursor, query, description=""):
    """Execute query and print results."""
    print(f"\n{'='*60}")
    print(f"QUERY: {description}")
    print(f"{'='*60}")
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        print(f"Columns: {columns}")
        print(f"Row count: {len(rows)}")
        for row in rows[:20]:  # Limit to first 20 rows
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("DYNAMIC PRICING DATA DISCOVERY - CHUNK 1")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Find YELO tenant_id
    run_query(cursor, """
        SELECT Id, Name, TenancyName, IsActive, IsDeleted 
        FROM dbo.AbpTenants 
        WHERE Name LIKE '%YELO%' OR TenancyName LIKE '%YELO%'
    """, "Find YELO Tenant")
    
    # 2. List all active tenants
    run_query(cursor, """
        SELECT TOP 20 Id, Name, TenancyName, IsActive 
        FROM dbo.AbpTenants 
        WHERE IsDeleted = 0 AND IsActive = 1
        ORDER BY Name
    """, "List Active Tenants (first 20)")
    
    # 3. Count contracts per tenant (using Rental.Contract)
    run_query(cursor, """
        SELECT TOP 10 c.TenantId, t.Name as TenantName, COUNT(*) as ContractCount
        FROM Rental.Contract c
        LEFT JOIN dbo.AbpTenants t ON c.TenantId = t.Id
        GROUP BY c.TenantId, t.Name
        ORDER BY ContractCount DESC
    """, "Contract Count by Tenant (Top 10)")
    
    # 4. Find YELO contracts date range (assuming TenantId will be discovered)
    # We'll run a generic query first to understand the data
    run_query(cursor, """
        SELECT 
            MIN(CAST(Start AS DATE)) as MinStartDate,
            MAX(CAST(Start AS DATE)) as MaxStartDate,
            MIN(CAST([End] AS DATE)) as MinEndDate,
            MAX(CAST([End] AS DATE)) as MaxEndDate,
            COUNT(*) as TotalContracts
        FROM Rental.Contract
        WHERE Start >= '2022-01-01'
    """, "Contract Date Ranges (2022+)")
    
    # 5. Check Discriminator values (for individual vs corporate filtering)
    run_query(cursor, """
        SELECT Discriminator, COUNT(*) as Count
        FROM Rental.Contract
        WHERE Start >= '2022-01-01'
        GROUP BY Discriminator
        ORDER BY Count DESC
    """, "Discriminator Values (Contract Types)")
    
    # 6. Check Contract Status values
    run_query(cursor, """
        SELECT c.StatusId, l.Text as StatusName, COUNT(*) as Count
        FROM Rental.Contract c
        LEFT JOIN dbo.Lookups l ON c.StatusId = l.Id
        WHERE c.Start >= '2022-01-01'
        GROUP BY c.StatusId, l.Text
        ORDER BY Count DESC
    """, "Contract Status Distribution")
    
    # 7. Check Branches per tenant - find YELO branches
    run_query(cursor, """
        SELECT TOP 20 b.Id, b.Name, b.TenantId, t.Name as TenantName, b.CityId, b.IsActive
        FROM Rental.Branches b
        LEFT JOIN dbo.AbpTenants t ON b.TenantId = t.Id
        WHERE b.IsActive = 1
        ORDER BY b.TenantId, b.Name
    """, "Active Branches (first 20)")
    
    # 8. Check CarModels per tenant
    run_query(cursor, """
        SELECT TOP 20 cm.Id, cm.CarModelName, cm.CarCategoryName, cm.TenantId, t.Name as TenantName
        FROM Rental.CarModels cm
        LEFT JOIN dbo.AbpTenants t ON cm.TenantId = t.Id
        ORDER BY cm.TenantId, cm.CarModelName
    """, "Car Models (first 20)")
    
    # 9. Check ContractsPaymentsItemsDetails - for base price
    run_query(cursor, """
        SELECT TOP 10 
            cpid.Id, cpid.ContractId, cpid.ItemName, cpid.ItemTypeId,
            cpid.Quantity, cpid.UnitPrice, cpid.TotalPrice, cpid.DiscountPct
        FROM Rental.ContractsPaymentsItemsDetails cpid
    """, "ContractsPaymentsItemsDetails Sample")
    
    # 10. ItemTypeId distribution - to identify rental rate items
    run_query(cursor, """
        SELECT ItemTypeId, ItemName, COUNT(*) as Count
        FROM Rental.ContractsPaymentsItemsDetails
        GROUP BY ItemTypeId, ItemName
        ORDER BY Count DESC
    """, "ItemTypeId Distribution (for base price identification)")
    
    # 11. Check RentalRates table
    run_query(cursor, """
        SELECT TOP 10 
            rr.Id, rr.TenantId, rr.BranchId, rr.ModelId, rr.Year,
            rr.Start, rr.[End], rr.IsActive
        FROM Rental.RentalRates rr
        ORDER BY rr.Id DESC
    """, "RentalRates Sample")
    
    # 12. Check VehiclesUtilization table (dbo schema)
    run_query(cursor, """
        SELECT TOP 10 *
        FROM dbo.VehiclesUtilization
        ORDER BY ReportDatetime DESC
    """, "VehiclesUtilization Sample")
    
    # 13. Look for dynamicpricing schema
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = 'dynamicpricing'
        ORDER BY t.name
    """, "DynamicPricing Schema Tables")
    
    # 14. List all schemas
    run_query(cursor, """
        SELECT name FROM sys.schemas ORDER BY name
    """, "All Database Schemas")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("DATA DISCOVERY COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
