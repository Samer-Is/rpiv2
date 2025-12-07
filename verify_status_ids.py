"""Verify StatusIds used in utilization calculation"""
import pyodbc
import config

conn_str = (
    f"DRIVER={config.DB_CONFIG['driver']};"
    f"SERVER={config.DB_CONFIG['server']};"
    f"DATABASE={config.DB_CONFIG['database']};"
    f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
)
conn = pyodbc.connect(conn_str)

print("="*70)
print("VERIFYING STATUS IDs IN Fleet.VehicleHistory")
print("="*70)

# Check what StatusIds exist and their counts
query1 = """
SELECT StatusId, COUNT(*) as count
FROM Fleet.VehicleHistory
WHERE OperationDateTime >= DATEADD(day, -60, GETDATE())
GROUP BY StatusId
ORDER BY count DESC
"""

print("\n1. STATUS ID DISTRIBUTION (last 60 days):")
print("-"*70)
cursor = conn.cursor()
cursor.execute(query1)
for row in cursor.fetchall():
    status_id, count = row
    # Mark our classification
    if status_id == 140:
        classification = "AVAILABLE"
    elif status_id in (141, 144, 146, 147, 154, 155):
        classification = "RENTED"
    else:
        classification = "OTHER (not counted)"
    print(f"  StatusId {status_id}: {count:,} records - {classification}")

# Check the lookup table for status names if it exists
print("\n2. LOOKING FOR STATUS NAMES...")
print("-"*70)
try:
    query2 = """
    SELECT DISTINCT l.Id, l.Name, l.NameAr
    FROM Lookups.LookupDetails l
    WHERE l.Id IN (140, 141, 144, 146, 147, 154, 155)
    ORDER BY l.Id
    """
    cursor.execute(query2)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]}: {row[1]} ({row[2]})")
    else:
        print("  No lookup data found")
except Exception as e:
    print(f"  Could not query lookups: {e}")

# Verify for a specific branch
print("\n3. SAMPLE: Branch 122 (King Khalid Airport) DETAILED BREAKDOWN:")
print("-"*70)
query3 = """
WITH LatestStatus AS (
    SELECT VehicleId, BranchId, StatusId,
           ROW_NUMBER() OVER (PARTITION BY VehicleId ORDER BY OperationDateTime DESC) as rn
    FROM Fleet.VehicleHistory
    WHERE OperationDateTime >= DATEADD(day, -60, GETDATE())
      AND BranchId = 122
)
SELECT StatusId, COUNT(*) as count
FROM LatestStatus
WHERE rn = 1
GROUP BY StatusId
ORDER BY count DESC
"""
cursor.execute(query3)
total = 0
rented = 0
available = 0
for row in cursor.fetchall():
    status_id, count = row
    total += count
    if status_id == 140:
        classification = "AVAILABLE"
        available += count
    elif status_id in (141, 144, 146, 147, 154, 155):
        classification = "RENTED"
        rented += count
    else:
        classification = "OTHER"
    print(f"  StatusId {status_id}: {count} vehicles - {classification}")

print(f"\n  SUMMARY for Branch 122:")
print(f"    Total vehicles: {total}")
print(f"    Rented (141,144,146,147,154,155): {rented}")
print(f"    Available (140): {available}")
print(f"    Other statuses: {total - rented - available}")
print(f"    Utilization: {rented/total*100:.1f}%")

conn.close()
print("\n" + "="*70)

