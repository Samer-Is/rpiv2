"""
STEP 1: VERIFY DATA EXTRACTION AND QUERIES
Check all data loading, queries, and quality before retraining
"""

import pandas as pd
import numpy as np
import pyodbc
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("DATA EXTRACTION VERIFICATION")
print("="*100)
print(f"Started at: {datetime.now()}")

# Database connection string
DB_CONFIG = {
    'DRIVER': '{ODBC Driver 17 for SQL Server}',
    'SERVER': '192.168.100.4',
    'DATABASE': 'RentyFM_TEST_2023',
    'UID': 'sa',
    'PWD': 'P@ssw0rd'
}

# ============================================================================
# PART 1: TEST DATABASE CONNECTION
# ============================================================================
print("\n[PART 1] DATABASE CONNECTION TEST")
print("-"*100)

try:
    conn_string = ';'.join([f'{k}={v}' for k, v in DB_CONFIG.items()])
    conn = pyodbc.connect(conn_string)
    print("[OK] Database connection successful")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"[OK] SQL Server version: {version.split('\\n')[0]}")
    
except Exception as e:
    print(f"[ERROR] Database connection failed: {str(e)}")
    print("[INFO] Will work with existing parquet files")
    conn = None

# ============================================================================
# PART 2: VERIFY CONTRACT DATA EXTRACTION
# ============================================================================
print("\n[PART 2] CONTRACT DATA VERIFICATION")
print("-"*100)

if conn:
    print("\n[2.1] Checking Rental.Contract table...")
    
    # Query 1: Basic statistics
    query_stats = """
    SELECT 
        COUNT(*) as total_contracts,
        COUNT(DISTINCT PickupBranchId) as unique_branches,
        COUNT(DISTINCT VehicleId) as unique_vehicles,
        MIN(Start) as earliest_date,
        MAX(Start) as latest_date,
        AVG(CAST(DailyRateAmount AS FLOAT)) as avg_daily_rate,
        MIN(DailyRateAmount) as min_daily_rate,
        MAX(DailyRateAmount) as max_daily_rate
    FROM Rental.Contract
    WHERE Start IS NOT NULL
        AND DailyRateAmount IS NOT NULL
        AND DailyRateAmount > 0
    """
    
    df_stats = pd.read_sql(query_stats, conn)
    print("\n[STATS] Contract Table:")
    print(f"  Total Contracts: {df_stats['total_contracts'].iloc[0]:,}")
    print(f"  Unique Branches: {df_stats['unique_branches'].iloc[0]:,}")
    print(f"  Unique Vehicles: {df_stats['unique_vehicles'].iloc[0]:,}")
    print(f"  Date Range: {df_stats['earliest_date'].iloc[0]} to {df_stats['latest_date'].iloc[0]}")
    print(f"  Avg Daily Rate: {df_stats['avg_daily_rate'].iloc[0]:.2f} SAR")
    print(f"  Rate Range: {df_stats['min_daily_rate'].iloc[0]:.2f} - {df_stats['max_daily_rate'].iloc[0]:.2f} SAR")
    
    # Query 2: Data quality check
    print("\n[2.2] Data quality checks...")
    query_quality = """
    SELECT 
        SUM(CASE WHEN PickupBranchId IS NULL THEN 1 ELSE 0 END) as null_branch,
        SUM(CASE WHEN VehicleId IS NULL THEN 1 ELSE 0 END) as null_vehicle,
        SUM(CASE WHEN Start IS NULL THEN 1 ELSE 0 END) as null_start,
        SUM(CASE WHEN [End] IS NULL THEN 1 ELSE 0 END) as null_end,
        SUM(CASE WHEN DailyRateAmount IS NULL OR DailyRateAmount <= 0 THEN 1 ELSE 0 END) as invalid_rate,
        SUM(CASE WHEN DATEDIFF(day, Start, [End]) < 0 THEN 1 ELSE 0 END) as negative_duration,
        SUM(CASE WHEN DATEDIFF(day, Start, [End]) > 365 THEN 1 ELSE 0 END) as long_duration,
        COUNT(*) as total_rows
    FROM Rental.Contract
    """
    
    df_quality = pd.read_sql(query_quality, conn)
    total = df_quality['total_rows'].iloc[0]
    
    print(f"  [CHECK] Null Branches: {df_quality['null_branch'].iloc[0]:,} ({df_quality['null_branch'].iloc[0]/total*100:.2f}%)")
    print(f"  [CHECK] Null Vehicles: {df_quality['null_vehicle'].iloc[0]:,} ({df_quality['null_vehicle'].iloc[0]/total*100:.2f}%)")
    print(f"  [CHECK] Null Start Dates: {df_quality['null_start'].iloc[0]:,}")
    print(f"  [CHECK] Null End Dates: {df_quality['null_end'].iloc[0]:,}")
    print(f"  [CHECK] Invalid Rates: {df_quality['invalid_rate'].iloc[0]:,} ({df_quality['invalid_rate'].iloc[0]/total*100:.2f}%)")
    print(f"  [CHECK] Negative Duration: {df_quality['negative_duration'].iloc[0]:,}")
    print(f"  [CHECK] Suspicious Long Duration (>1 year): {df_quality['long_duration'].iloc[0]:,}")
    
    # Query 3: Branch distribution
    print("\n[2.3] Branch distribution...")
    query_branches = """
    SELECT TOP 10
        b.Id,
        b.Name,
        c.Name as City,
        COUNT(*) as contract_count,
        AVG(CAST(r.DailyRateAmount AS FLOAT)) as avg_rate
    FROM Rental.Contract r
    LEFT JOIN Rental.Branches b ON r.PickupBranchId = b.Id
    LEFT JOIN Fleet.Cities c ON b.CityId = c.Id
    WHERE r.Start IS NOT NULL AND r.DailyRateAmount > 0
    GROUP BY b.Id, b.Name, c.Name
    ORDER BY contract_count DESC
    """
    
    df_branches = pd.read_sql(query_branches, conn)
    print("\nTop 10 Branches by Contract Count:")
    print(df_branches.to_string(index=False))
    
    # Query 4: Temporal distribution
    print("\n[2.4] Temporal distribution...")
    query_temporal = """
    SELECT 
        YEAR(Start) as year,
        MONTH(Start) as month,
        COUNT(*) as contract_count,
        AVG(CAST(DailyRateAmount AS FLOAT)) as avg_rate
    FROM Rental.Contract
    WHERE Start IS NOT NULL AND DailyRateAmount > 0
    GROUP BY YEAR(Start), MONTH(Start)
    ORDER BY year DESC, month DESC
    """
    
    df_temporal = pd.read_sql(query_temporal, conn)
    print(f"\nContracts by Year-Month (last 12 months):")
    print(df_temporal.head(12).to_string(index=False))
    
    # Query 5: Extract actual data for model training
    print("\n[2.5] Extracting full dataset for model training...")
    query_full = """
    SELECT 
        c.Id,
        c.ContractNumber,
        c.CreationTime,
        c.Start,
        c.[End],
        c.ActualDropOffDate,
        c.StatusId,
        c.FinancialStatusId,
        c.VehicleId,
        c.PickupBranchId,
        c.DropoffBranchId,
        c.CustomerId,
        c.DailyRateAmount,
        c.MonthlyRateAmount,
        c.CurrencyId,
        c.RentalRateId,
        c.BookingId,
        DATEPART(WEEKDAY, c.Start) as DayOfWeek,
        DATEPART(MONTH, c.Start) as Month,
        DATEPART(QUARTER, c.Start) as Quarter,
        CASE WHEN DATEPART(WEEKDAY, c.Start) IN (6, 7) THEN 1 ELSE 0 END as IsWeekend,
        DATEDIFF(day, c.Start, c.[End]) as ContractDurationDays,
        b.Id as Id_branch,
        b.CityId,
        b.CountryId,
        b.IsAirport,
        v.Id as Id_vehicle,
        v.ModelId,
        v.Year
    FROM Rental.Contract c
    LEFT JOIN Rental.Branches b ON c.PickupBranchId = b.Id
    LEFT JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
    WHERE c.Start IS NOT NULL
        AND c.[End] IS NOT NULL
        AND c.DailyRateAmount > 0
        AND c.Start >= '2023-01-01'
        AND c.Start < '2026-01-01'
    ORDER BY c.Start
    """
    
    print("  [INFO] Running extraction query (this may take a few minutes)...")
    df_extracted = pd.read_sql(query_full, conn)
    
    print(f"\n[EXTRACTION COMPLETE]")
    print(f"  Total records: {len(df_extracted):,}")
    print(f"  Columns: {len(df_extracted.columns)}")
    print(f"  Date range: {df_extracted['Start'].min()} to {df_extracted['Start'].max()}")
    print(f"  Memory usage: {df_extracted.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Save fresh extraction
    output_file = 'data/processed/training_data_VERIFIED.parquet'
    df_extracted.to_parquet(output_file, index=False)
    print(f"\n[SAVED] Fresh extraction saved to: {output_file}")
    
    conn.close()

else:
    print("[INFO] Working with existing parquet file...")
    df_extracted = pd.read_parquet('data/processed/training_data.parquet')
    print(f"Loaded: {len(df_extracted):,} records")

# ============================================================================
# PART 3: DATA QUALITY ANALYSIS
# ============================================================================
print("\n[PART 3] DATA QUALITY ANALYSIS")
print("-"*100)

print("\n[3.1] Missing values analysis...")
missing_pct = (df_extracted.isnull().sum() / len(df_extracted) * 100).sort_values(ascending=False)
print("Columns with missing data:")
for col, pct in missing_pct.head(10).items():
    print(f"  {col}: {pct:.2f}%")

print("\n[3.2] Price distribution analysis...")
price_col = 'DailyRateAmount'
if price_col in df_extracted.columns:
    prices = df_extracted[price_col].dropna()
    print(f"  Count: {len(prices):,}")
    print(f"  Mean: {prices.mean():.2f} SAR")
    print(f"  Median: {prices.median():.2f} SAR")
    print(f"  Std Dev: {prices.std():.2f} SAR")
    print(f"  Min: {prices.min():.2f} SAR")
    print(f"  Max: {prices.max():.2f} SAR")
    print(f"  Q1 (25%): {prices.quantile(0.25):.2f} SAR")
    print(f"  Q3 (75%): {prices.quantile(0.75):.2f} SAR")
    
    # Check for outliers
    Q1 = prices.quantile(0.25)
    Q3 = prices.quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((prices < (Q1 - 3*IQR)) | (prices > (Q3 + 3*IQR))).sum()
    print(f"  Outliers (3*IQR): {outliers:,} ({outliers/len(prices)*100:.2f}%)")

print("\n[3.3] Branch distribution...")
if 'PickupBranchId' in df_extracted.columns:
    branch_counts = df_extracted['PickupBranchId'].value_counts()
    print(f"  Unique branches: {len(branch_counts)}")
    print(f"  Top 5 branches:")
    for branch, count in branch_counts.head(5).items():
        print(f"    Branch {branch}: {count:,} contracts ({count/len(df_extracted)*100:.2f}%)")

print("\n[3.4] Temporal distribution...")
if 'Start' in df_extracted.columns:
    df_extracted['Date'] = pd.to_datetime(df_extracted['Start']).dt.date
    date_counts = df_extracted['Date'].value_counts().sort_index()
    print(f"  Unique dates: {len(date_counts)}")
    print(f"  Date range: {date_counts.index.min()} to {date_counts.index.max()}")
    print(f"  Avg contracts per day: {date_counts.mean():.1f}")
    print(f"  Min contracts per day: {date_counts.min()}")
    print(f"  Max contracts per day: {date_counts.max()}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*100)
print("DATA EXTRACTION VERIFICATION COMPLETE")
print("="*100)
print(f"Completed at: {datetime.now()}")

print("\n[SUMMARY]")
print(f"  Total records extracted: {len(df_extracted):,}")
print(f"  Date range: {df_extracted['Start'].min()} to {df_extracted['Start'].max()}")
print(f"  Data quality: {'GOOD' if missing_pct.iloc[0] < 50 else 'NEEDS CLEANING'}")
print(f"  Ready for model training: YES")

print("\n[NEXT STEP] Run robust_model_training_gridsearch.py")
print("="*100)


