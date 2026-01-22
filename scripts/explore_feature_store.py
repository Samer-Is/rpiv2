"""
Explore contract data for feature store building
"""
import pyodbc

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# Check contract data structure
print("=== Contract Table Sample ===")
cursor.execute("""
SELECT TOP 5 
    c.Id, c.TenantId, c.BranchId, 
    CAST(c.[Start] AS DATE) as StartDate, 
    CAST(c.[End] AS DATE) as EndDate, 
    c.DailyRateAmount, c.StatusId, c.Discriminator,
    v.ModelId
FROM Rental.Contract c
LEFT JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
WHERE c.TenantId = 1 AND c.Discriminator = 'Contract' AND c.StatusId = 211
ORDER BY c.[Start] DESC
""")
for row in cursor.fetchall():
    print(row)

# Check date ranges
print("\n=== Date Range for Contracts (2023+) ===")
cursor.execute("""
SELECT 
    MIN(CAST([Start] AS DATE)) as MinStart,
    MAX(CAST([Start] AS DATE)) as MaxStart,
    COUNT(*) as TotalContracts
FROM Rental.Contract
WHERE TenantId = 1 AND Discriminator = 'Contract' AND StatusId = 211
  AND [Start] >= '2023-01-01'
""")
row = cursor.fetchone()
print(f"Start: {row[0]}, End: {row[1]}, Total: {row[2]}")

# Check daily demand for MVP branches and categories
print("\n=== Sample Daily Demand (MVP Scope) ===")
cursor.execute("""
SELECT TOP 10
    CAST(c.[Start] AS DATE) as demand_date,
    c.BranchId,
    cm.CategoryId,
    COUNT(*) as rentals_count,
    AVG(c.DailyRateAmount) as avg_daily_rate
FROM Rental.Contract c
JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
WHERE c.TenantId = 1 
  AND c.Discriminator = 'Contract' 
  AND c.StatusId = 211
  AND c.[Start] >= '2024-01-01'
  AND c.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
  AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
GROUP BY CAST(c.[Start] AS DATE), c.BranchId, cm.CategoryId
ORDER BY demand_date DESC
""")
print("Date        | Branch | Cat | Rentals | AvgRate")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]:6} | {row[2]:3} | {row[3]:7} | {row[4]:.2f}")

# Check total combinations
print("\n=== Total Data Points Available ===")
cursor.execute("""
SELECT COUNT(*) FROM (
    SELECT DISTINCT
        CAST(c.[Start] AS DATE) as demand_date,
        c.BranchId,
        cm.CategoryId
    FROM Rental.Contract c
    JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
    JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
    WHERE c.TenantId = 1 
      AND c.Discriminator = 'Contract' 
      AND c.StatusId = 211
      AND c.[Start] >= '2023-01-01'
      AND c.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
      AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
) x
""")
print(f"Total date×branch×category combinations: {cursor.fetchone()[0]}")

# Check MVP branches
print("\n=== MVP Branches ===")
cursor.execute("SELECT BranchId FROM dynamicpricing.TopBranches")
branches = [row[0] for row in cursor.fetchall()]
print(f"Branches: {branches}")

# Check MVP categories  
print("\n=== MVP Categories ===")
cursor.execute("SELECT CategoryId FROM dynamicpricing.TopCategories")
categories = [row[0] for row in cursor.fetchall()]
print(f"Categories: {categories}")

conn.close()
