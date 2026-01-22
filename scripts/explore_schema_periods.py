"""
CHUNK 3: Explore RentalRatesSchemas and Period Details
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
        for row in rows[:20]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 3: Schema Periods Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. RentalRatesSchemaPeriods structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRatesSchemaPeriods'
        ORDER BY ORDINAL_POSITION
    """, "RentalRatesSchemaPeriods Table Structure")
    
    # 2. Sample RentalRatesSchemaPeriods
    run_query(cursor, """
        SELECT TOP 15 *
        FROM Rental.RentalRatesSchemaPeriods
        WHERE TenantId = 1
    """, "RentalRatesSchemaPeriods Sample")
    
    # 3. RentalRatesSchemaPeriodsDetails structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRatesSchemaPeriodsDetails'
        ORDER BY ORDINAL_POSITION
    """, "RentalRatesSchemaPeriodsDetails Table Structure")
    
    # 4. Sample RentalRatesSchemaPeriodsDetails
    run_query(cursor, """
        SELECT TOP 15 *
        FROM Rental.RentalRatesSchemaPeriodsDetails
    """, "RentalRatesSchemaPeriodsDetails Sample")
    
    # 5. Full price lookup - join all tables
    run_query(cursor, """
        SELECT TOP 20
            rr.Id as RateId,
            rr.ModelId,
            rr.BranchId,
            rr.SchemaId,
            sp.Id as SchemaPeriodId,
            sp.Name as PeriodName,
            sp.MinDays,
            sp.MaxDays,
            spd.Price
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp ON rr.SchemaId = sp.SchemaId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd ON sp.Id = spd.SchemaPeriodId AND rr.Id = spd.RentalRateId
        WHERE rr.TenantId = 1 AND rr.IsActive = 1
        ORDER BY rr.Id DESC
    """, "Full Price Join (RentalRates -> SchemaPeriods -> Details)")
    
    # 6. Get distinct SchemaIds
    run_query(cursor, """
        SELECT DISTINCT SchemaId, COUNT(*) as RateCount
        FROM Rental.RentalRates
        WHERE TenantId = 1 AND IsActive = 1
        GROUP BY SchemaId
        ORDER BY SchemaId
    """, "Distinct SchemaIds in Use")
    
    # 7. Get Schema Periods for common schemas
    run_query(cursor, """
        SELECT sp.SchemaId, sp.Id as PeriodId, sp.Name, sp.MinDays, sp.MaxDays
        FROM Rental.RentalRatesSchemaPeriods sp
        WHERE sp.TenantId = 1
        ORDER BY sp.SchemaId, sp.MinDays
    """, "Schema Periods for All Schemas")
    
    # 8. Get prices for specific Model (join to get category)
    run_query(cursor, """
        SELECT TOP 20
            rr.ModelId,
            cm.CarModelName,
            cm.CarCategoryId,
            cm.CarCategoryName,
            sp.Name as PeriodName,
            sp.MinDays,
            sp.MaxDays,
            spd.Price as DailyPrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp ON rr.SchemaId = sp.SchemaId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd ON sp.Id = spd.SchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL  -- Default prices
          AND cm.CarCategoryId = 27  -- Compact
        ORDER BY cm.CarModelName, sp.MinDays
    """, "Prices for Compact Category (27) - Default")
    
    # 9. Get all prices for a specific model to understand structure
    run_query(cursor, """
        SELECT 
            rr.Id as RateId,
            rr.ModelId,
            cm.CarModelName,
            rr.Year,
            sp.Name as PeriodName,
            sp.MinDays,
            sp.MaxDays,
            spd.Price as DailyPrice,
            rr.Start as EffectiveStart,
            rr.[End] as EffectiveEnd
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp ON rr.SchemaId = sp.SchemaId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd ON sp.Id = spd.SchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND cm.CarModelName = 'Kia Cerato'
        ORDER BY sp.MinDays
    """, "All Prices for Kia Cerato")
    
    # 10. Check MVP Branches and their prices
    run_query(cursor, """
        SELECT 
            b.Id as BranchId,
            b.Name as BranchName,
            COUNT(DISTINCT rr.Id) as RateCount
        FROM dynamicpricing.TopBranches tb
        INNER JOIN Rental.Branches b ON tb.BranchId = b.Id
        LEFT JOIN Rental.RentalRates rr ON rr.BranchId = b.Id AND rr.TenantId = 1 AND rr.IsActive = 1
        GROUP BY b.Id, b.Name
        ORDER BY b.Id
    """, "MVP Branches Rate Counts")
    
    # 11. Check MVP Categories and their prices
    run_query(cursor, """
        SELECT 
            tc.CategoryId,
            tc.CategoryName,
            COUNT(DISTINCT rr.Id) as RateCount
        FROM dynamicpricing.TopCategories tc
        LEFT JOIN Rental.CarModels cm ON cm.CarCategoryId = tc.CategoryId AND cm.TenantId = 1
        LEFT JOIN Rental.RentalRates rr ON rr.ModelId = cm.ModelId AND rr.TenantId = 1 AND rr.IsActive = 1
        GROUP BY tc.CategoryId, tc.CategoryName
        ORDER BY tc.CategoryId
    """, "MVP Categories Rate Counts")
    
    # 12. Get actual pricing for simulation date (2025-05-31)
    run_query(cursor, """
        SELECT TOP 30
            cm.CarCategoryId,
            cm.CarCategoryName,
            cm.CarModelName,
            sp.Name as PeriodName,
            sp.MinDays,
            sp.MaxDays,
            spd.Price as DailyPrice,
            rr.Start as EffectiveFrom
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp ON rr.SchemaId = sp.SchemaId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd ON sp.Id = spd.SchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        INNER JOIN dynamicpricing.TopCategories tc ON cm.CarCategoryId = tc.CategoryId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL
          AND rr.Start <= '2025-05-31'
          AND (rr.[End] IS NULL OR rr.[End] >= '2025-05-31')
        ORDER BY cm.CarCategoryId, cm.CarModelName, sp.MinDays
    """, "Prices Valid on Simulation Date (2025-05-31)")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("SCHEMA PERIODS EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
