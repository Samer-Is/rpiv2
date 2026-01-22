"""
CHUNK 3: Explore Base Price Tables
Understand the structure of RentalRates and pricing-related tables.
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
        for row in rows[:15]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 3: Base Price Engine - Table Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. RentalRates table structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRates'
        ORDER BY ORDINAL_POSITION
    """, "RentalRates Table Structure")
    
    # 2. Sample RentalRates data
    run_query(cursor, """
        SELECT TOP 10 
            rr.Id, rr.TenantId, rr.BranchId, rr.ModelId, rr.Year,
            rr.Start, rr.[End], rr.IsActive, rr.SchemaId
        FROM Rental.RentalRates rr
        WHERE rr.TenantId = 1 AND rr.IsActive = 1
        ORDER BY rr.Id DESC
    """, "RentalRates Sample Data")
    
    # 3. Look for RentalRateDetails or similar
    run_query(cursor, """
        SELECT s.name as SchemaName, t.name as TableName
        FROM sys.tables t
        INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE t.name LIKE '%RentalRate%' OR t.name LIKE '%RateDetail%' OR t.name LIKE '%Pricing%'
        ORDER BY s.name, t.name
    """, "Find Rate/Pricing Related Tables")
    
    # 4. Check RentalRateDetails table
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRateDetails'
        ORDER BY ORDINAL_POSITION
    """, "RentalRateDetails Table Structure")
    
    # 5. Sample RentalRateDetails
    run_query(cursor, """
        SELECT TOP 15 *
        FROM Rental.RentalRateDetails
    """, "RentalRateDetails Sample Data")
    
    # 6. Join RentalRates with RentalRateDetails for a category
    run_query(cursor, """
        SELECT TOP 10
            rr.Id as RateId, rr.ModelId, rr.BranchId,
            rrd.DurationType, rrd.DurationValue, rrd.Price, rrd.CurrencyId
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRateDetails rrd ON rr.Id = rrd.RentalRateId
        WHERE rr.TenantId = 1 AND rr.IsActive = 1
        ORDER BY rr.Id DESC
    """, "RentalRates + RentalRateDetails Join")
    
    # 7. Check DurationType values (daily, weekly, monthly)
    run_query(cursor, """
        SELECT DurationType, COUNT(*) as Count
        FROM Rental.RentalRateDetails
        GROUP BY DurationType
        ORDER BY Count DESC
    """, "DurationType Distribution")
    
    # 8. Get prices for a specific category (Compact = 27)
    # Need to find how ModelId maps to CategoryId
    run_query(cursor, """
        SELECT TOP 10
            rr.Id as RateId, 
            rr.ModelId,
            cm.CarCategoryId,
            cm.CarCategoryName,
            rr.BranchId,
            rrd.DurationType,
            rrd.Price
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRateDetails rrd ON rr.Id = rrd.RentalRateId
        INNER JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND cm.CarCategoryId = 27  -- Compact
        ORDER BY rr.Id DESC
    """, "Prices for Compact Category (27)")
    
    # 9. Get prices for MVP branches (e.g., branch 122 - Riyadh Airport)
    run_query(cursor, """
        SELECT TOP 15
            rr.Id as RateId,
            rr.BranchId,
            b.Name as BranchName,
            cm.CarCategoryId,
            cm.CarCategoryName,
            rrd.DurationType,
            rrd.Price
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRateDetails rrd ON rr.Id = rrd.RentalRateId
        LEFT JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        LEFT JOIN Rental.Branches b ON rr.BranchId = b.Id
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId = 122  -- King Khalid Airport Riyadh
        ORDER BY cm.CarCategoryId, rrd.DurationType
    """, "Prices for Branch 122 (Riyadh Airport)")
    
    # 10. Check if BranchId is NULL (applies to all branches?)
    run_query(cursor, """
        SELECT 
            CASE WHEN rr.BranchId IS NULL THEN 'NULL (All Branches)' ELSE 'Specific Branch' END as BranchScope,
            COUNT(*) as RateCount
        FROM Rental.RentalRates rr
        WHERE rr.TenantId = 1 AND rr.IsActive = 1
        GROUP BY CASE WHEN rr.BranchId IS NULL THEN 'NULL (All Branches)' ELSE 'Specific Branch' END
    """, "BranchId NULL vs Specific")
    
    # 11. Get base prices for Compact category (NULL branch = default)
    run_query(cursor, """
        SELECT TOP 20
            rr.Id as RateId,
            cm.CarCategoryId,
            cm.CarCategoryName,
            cm.CarModelName,
            rrd.DurationType,
            rrd.Price as BasePrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRateDetails rrd ON rr.Id = rrd.RentalRateId
        INNER JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL  -- Default rates
          AND cm.CarCategoryId = 27  -- Compact
        ORDER BY cm.CarModelName, rrd.DurationType
    """, "Default Prices for Compact Category")
    
    # 12. Check if there's a RentalRateSchemas table
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRateSchemas'
        ORDER BY ORDINAL_POSITION
    """, "RentalRateSchemas Table Structure")
    
    # 13. Sample RentalRateSchemas
    run_query(cursor, """
        SELECT TOP 10 *
        FROM Rental.RentalRateSchemas
        WHERE TenantId = 1
    """, "RentalRateSchemas Sample")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("BASE PRICE EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
