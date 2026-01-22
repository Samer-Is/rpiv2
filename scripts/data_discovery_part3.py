"""
Data Discovery Part 3 - Final Details
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
    print("DYNAMIC PRICING DATA DISCOVERY - PART 3 (Final)")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Fleet.Vehicles table structure
    run_query(cursor, """
        SELECT TOP 5 v.Id, v.ModelId, v.PlateNo, v.TenantId, v.StatusId, v.BranchId, v.CategoryId
        FROM Fleet.Vehicles v
        WHERE v.TenantId = 1
    """, "Fleet.Vehicles Table Sample")
    
    # 2. Top Car Models by rental volume using Fleet.Vehicles
    run_query(cursor, """
        SELECT TOP 15
            cm.CarCategoryId as CategoryId,
            cm.CarCategoryName,
            COUNT(*) as RentalCount
        FROM Rental.Contract c
        INNER JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
        INNER JOIN Rental.CarModels cm ON v.ModelId = cm.ModelId AND v.TenantId = cm.TenantId
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2022-01-01'
        GROUP BY cm.CarCategoryId, cm.CarCategoryName
        ORDER BY RentalCount DESC
    """, "Top 15 Categories by Rental Volume (YELO, 2022+)")
    
    # 3. Check Fleet.CarModels
    run_query(cursor, """
        SELECT TOP 10 Id, CarModelName, CarCategoryName, TenantId, CarCategoryId
        FROM Fleet.CarModels
        WHERE TenantId = 1
    """, "Fleet.CarModels Sample")
    
    # 4. Get contract with Trip Days price (avoiding datetimeoffset issue)
    run_query(cursor, """
        SELECT TOP 10
            c.Id as ContractId,
            CONVERT(DATE, c.Start) as StartDate,
            CONVERT(DATE, c.[End]) as EndDate,
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
          AND cpid.ItemTypeId = 1
          AND c.Start >= '2023-01-01'
        ORDER BY c.Id DESC
    """, "Contract with Trip Days Base Price (fixed)")
    
    # 5. Verify dynamicpricing schema tables structure
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dynamicpricing' AND TABLE_NAME = 'TrainingData'
        ORDER BY ORDINAL_POSITION
    """, "TrainingData Table Structure")
    
    run_query(cursor, """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dynamicpricing' AND TABLE_NAME = 'ValidationData'
        ORDER BY ORDINAL_POSITION
    """, "ValidationData Table Structure")
    
    # 6. Check if any records exist in dynamicpricing tables
    run_query(cursor, """
        SELECT 'TrainingData' as TableName, COUNT(*) as RecordCount FROM dynamicpricing.TrainingData
        UNION ALL
        SELECT 'ValidationData', COUNT(*) FROM dynamicpricing.ValidationData
    """, "DynamicPricing Tables Record Count")
    
    # 7. Check Cities table
    run_query(cursor, """
        SELECT TOP 10 c.Id, c.Name, c.CountryId
        FROM Rental.Cities c
        ORDER BY c.Id
    """, "Cities Table Sample")
    
    # 8. Branch to City mapping
    run_query(cursor, """
        SELECT TOP 10 b.Id, b.Name, b.CityId, c.Name as CityName, b.IsAirport
        FROM Rental.Branches b
        LEFT JOIN Rental.Cities c ON b.CityId = c.Id
        WHERE b.TenantId = 1 AND b.IsActive = 1
        ORDER BY b.Id
    """, "Branch-City Mapping Sample")
    
    # 9. Data completeness check - contracts with DailyRateAmount
    run_query(cursor, """
        SELECT 
            CASE WHEN c.DailyRateAmount IS NOT NULL AND c.DailyRateAmount > 0 THEN 'Has Rate' ELSE 'No Rate' END as HasRate,
            COUNT(*) as ContractCount
        FROM Rental.Contract c
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2022-01-01'
        GROUP BY CASE WHEN c.DailyRateAmount IS NOT NULL AND c.DailyRateAmount > 0 THEN 'Has Rate' ELSE 'No Rate' END
    """, "Contracts with DailyRateAmount (Data Completeness)")
    
    # 10. DailyRateAmount distribution
    run_query(cursor, """
        SELECT 
            MIN(c.DailyRateAmount) as MinRate,
            MAX(c.DailyRateAmount) as MaxRate,
            AVG(c.DailyRateAmount) as AvgRate,
            COUNT(*) as TotalContracts
        FROM Rental.Contract c
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2022-01-01'
          AND c.DailyRateAmount IS NOT NULL
          AND c.DailyRateAmount > 0
    """, "DailyRateAmount Statistics")
    
    # 11. Check RentalRateId usage in contracts
    run_query(cursor, """
        SELECT 
            CASE WHEN c.RentalRateId IS NOT NULL THEN 'Has RentalRateId' ELSE 'No RentalRateId' END as HasRateId,
            COUNT(*) as ContractCount
        FROM Rental.Contract c
        WHERE c.TenantId = 1
          AND c.Discriminator = 'Contract'
          AND c.StatusId = 211
          AND c.Start >= '2022-01-01'
        GROUP BY CASE WHEN c.RentalRateId IS NOT NULL THEN 'Has RentalRateId' ELSE 'No RentalRateId' END
    """, "Contracts with RentalRateId")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("DATA DISCOVERY PART 3 COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
