import pandas as pd

df = pd.read_csv('data/vehicle_history_local.csv')
dashboard_branches = [122, 15, 63, 33, 45, 89]

print("=" * 50)
print("CHECKING IF DASHBOARD BRANCHES EXIST IN LOCAL CSV")
print("=" * 50)
print()

for b in dashboard_branches:
    if b in df['BranchId'].values:
        row = df[df['BranchId'] == b].iloc[0]
        print(f"Branch {b}: YES - {row['total_vehicles']} vehicles, {row['utilization_pct']}% utilization")
    else:
        print(f"Branch {b}: NO - MISSING FROM CSV!")

print()
print(f"Total branches in CSV: {len(df)}")

