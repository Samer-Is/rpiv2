"""Export utilization data as of November 18th, 2025"""
import pandas as pd
import pyodbc
from datetime import datetime
import config

TARGET_DATE = datetime(2025, 11, 18)

print("="*70)
print(f"EXPORTING UTILIZATION AS OF {TARGET_DATE.strftime('%Y-%m-%d')}")
print("="*70)

conn_str = (
    f"DRIVER={config.DB_CONFIG['driver']};"
    f"SERVER={config.DB_CONFIG['server']};"
    f"DATABASE={config.DB_CONFIG['database']};"
    f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
)
conn = pyodbc.connect(conn_str)
print("[OK] Connected to database")

# Query: Get status as of Nov 18, 2025
# Get the latest status for each vehicle BEFORE or ON Nov 18
query = """
WITH LatestStatus AS (
    SELECT 
        vh.VehicleId,
        vh.BranchId,
        vh.StatusId,
        vh.OperationDateTime,
        ROW_NUMBER() OVER (PARTITION BY vh.VehicleId ORDER BY vh.OperationDateTime DESC) as rn
    FROM Fleet.VehicleHistory vh
    WHERE vh.OperationDateTime <= ?
      AND vh.OperationDateTime >= DATEADD(day, -60, ?)
)
SELECT 
    BranchId,
    COUNT(*) as total_vehicles,
    SUM(CASE WHEN StatusId IN (141, 144, 146, 147, 154, 155) THEN 1 ELSE 0 END) as rented_vehicles,
    SUM(CASE WHEN StatusId = 140 THEN 1 ELSE 0 END) as available_vehicles
FROM LatestStatus
WHERE rn = 1
GROUP BY BranchId
ORDER BY BranchId
"""

df = pd.read_sql(query, conn, params=[TARGET_DATE, TARGET_DATE])
conn.close()

# Calculate utilization percentage
df['utilization_pct'] = (df['rented_vehicles'] / df['total_vehicles'] * 100).round(1)
df['export_date'] = f"{TARGET_DATE.strftime('%Y-%m-%d')} (historical)"

# Save to CSV
output_file = 'data/vehicle_history_local.csv'
df.to_csv(output_file, index=False)

print(f"[OK] Exported {len(df)} branches")
print(f"[OK] Saved to {output_file}")

# Show dashboard branches
dashboard_branches = {
    122: 'King Khalid Airport - Riyadh',
    15: 'Olaya District - Riyadh', 
    63: 'King Fahd Airport - Dammam',
    33: 'King Abdulaziz Airport - Jeddah',
    45: 'Mecca City Center',
    89: 'Medina Downtown'
}

print(f"\nDASHBOARD BRANCHES (as of {TARGET_DATE.strftime('%Y-%m-%d')}):")
print("-"*70)
for branch_id, name in dashboard_branches.items():
    row = df[df['BranchId'] == branch_id]
    if len(row) > 0:
        r = row.iloc[0]
        print(f"{name} (ID: {branch_id})")
        print(f"  Total: {r['total_vehicles']} | Rented: {r['rented_vehicles']} | Available: {r['available_vehicles']}")
        print(f"  Utilization: {r['utilization_pct']}%")
    else:
        print(f"{name} (ID: {branch_id}): NO DATA")

print("\n" + "="*70)
print("EXPORT COMPLETE!")
print("="*70)

