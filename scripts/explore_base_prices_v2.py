"""
CHUNK 3: Corrected Base Price Exploration
Using correct column names: RentalRatesSchemaId, From, To, Rate
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
        for row in rows[:25]:
            print(row)
        return rows
    except Exception as e:
        print(f"ERROR: {e}")
        return []

def main():
    print("=" * 80)
    print("CHUNK 3: Corrected Base Price Exploration")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Full RentalRates structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'Rental' AND TABLE_NAME = 'RentalRates'
        ORDER BY ORDINAL_POSITION
    """, "Full RentalRates Columns")
    
    # 2. Full price join with correct columns
    # RentalRates.SchemaId -> RentalRatesSchemaPeriods.RentalRatesSchemaId
    # RentalRatesSchemaPeriods.From/To -> MinDays/MaxDays
    # RentalRatesSchemaPeriodsDetails.Rate -> Price
    run_query(cursor, """
        SELECT TOP 20
            rr.Id as RateId,
            rr.ModelId,
            rr.BranchId,
            rr.SchemaId,
            sp.Id as SchemaPeriodId,
            sp.Name as PeriodName,
            sp.[From] as MinDays,
            sp.[To] as MaxDays,
            spd.Rate as DailyPrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp 
            ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
            ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
        WHERE rr.TenantId = 1 AND rr.IsActive = 1
        ORDER BY rr.Id DESC
    """, "Full Price Join (Corrected)")
    
    # 3. Get Schema definitions
    run_query(cursor, """
        SELECT sp.RentalRatesSchemaId as SchemaId, 
               sp.Id as PeriodId, 
               sp.Name, 
               sp.[From] as MinDays, 
               sp.[To] as MaxDays,
               sp.IsDefault
        FROM Rental.RentalRatesSchemaPeriods sp
        WHERE sp.TenantId = 1
        ORDER BY sp.RentalRatesSchemaId, sp.[From]
    """, "Schema Periods Definition")
    
    # 4. Get prices for Compact category (27) - Default (NULL branch)
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            cm.CarCategoryName,
            cm.CarModelName,
            sp.Name as PeriodName,
            sp.[From] as MinDays,
            sp.[To] as MaxDays,
            spd.Rate as DailyPrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp 
            ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
            ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm 
            ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL  -- Default prices
          AND cm.CarCategoryId = 27  -- Compact
        ORDER BY cm.CarModelName, sp.[From]
    """, "Compact Category (27) Default Prices")
    
    # 5. Get prices for Economy category (1)
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            cm.CarCategoryName,
            cm.CarModelName,
            sp.Name as PeriodName,
            sp.[From] as MinDays,
            sp.[To] as MaxDays,
            spd.Rate as DailyPrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp 
            ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
            ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm 
            ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL
          AND cm.CarCategoryId = 1  -- Economy
        ORDER BY cm.CarModelName, sp.[From]
    """, "Economy Category (1) Default Prices")
    
    # 6. Get prices valid on simulation date (2025-05-31)
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            cm.CarCategoryName,
            cm.CarModelName,
            sp.Name as PeriodName,
            sp.[From] as MinDays,
            sp.[To] as MaxDays,
            spd.Rate as DailyPrice,
            rr.Start as EffectiveFrom,
            rr.[End] as EffectiveUntil
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp 
            ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
            ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm 
            ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        INNER JOIN dynamicpricing.TopCategories tc 
            ON cm.CarCategoryId = tc.CategoryId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL
          AND rr.Start <= '2025-05-31'
          AND (rr.[End] IS NULL OR rr.[End] >= '2025-05-31')
        ORDER BY cm.CarCategoryId, cm.CarModelName, sp.[From]
    """, "MVP Category Prices Valid on 2025-05-31")
    
    # 7. Get average prices by category and period type
    run_query(cursor, """
        SELECT 
            cm.CarCategoryId,
            cm.CarCategoryName,
            sp.[From] as MinDays,
            sp.[To] as MaxDays,
            COUNT(*) as ModelCount,
            AVG(spd.Rate) as AvgPrice,
            MIN(spd.Rate) as MinPrice,
            MAX(spd.Rate) as MaxPrice
        FROM Rental.RentalRates rr
        INNER JOIN Rental.RentalRatesSchemaPeriods sp 
            ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
        INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
            ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
        INNER JOIN Rental.CarModels cm 
            ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
        INNER JOIN dynamicpricing.TopCategories tc 
            ON cm.CarCategoryId = tc.CategoryId
        WHERE rr.TenantId = 1 
          AND rr.IsActive = 1
          AND rr.BranchId IS NULL
          AND rr.Start <= '2025-05-31'
          AND (rr.[End] IS NULL OR rr.[End] >= '2025-05-31')
        GROUP BY cm.CarCategoryId, cm.CarCategoryName, sp.[From], sp.[To]
        ORDER BY cm.CarCategoryId, sp.[From]
    """, "Average Prices by Category and Duration")
    
    # 8. Check if there are branch-specific prices for MVP branches
    run_query(cursor, """
        SELECT 
            b.Id as BranchId,
            LEFT(b.Name, 50) as BranchName,
            COUNT(DISTINCT rr.Id) as SpecificRates
        FROM Rental.Branches b
        LEFT JOIN Rental.RentalRates rr 
            ON rr.BranchId = b.Id AND rr.TenantId = 1 AND rr.IsActive = 1
        WHERE b.Id IN (SELECT BranchId FROM dynamicpricing.TopBranches)
        GROUP BY b.Id, b.Name
        ORDER BY b.Id
    """, "MVP Branches Specific Rates")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("BASE PRICE EXPLORATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
