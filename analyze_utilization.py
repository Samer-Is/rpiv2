"""Analyze utilization data from local CSV"""
import pandas as pd

df = pd.read_csv('data/vehicle_history_local.csv')
print('='*70)
print('UTILIZATION DATA ANALYSIS')
print('='*70)

# Dashboard branches
dashboard_branches = {
    122: 'King Khalid Airport - Riyadh',
    15: 'Olaya District - Riyadh', 
    63: 'King Fahd Airport - Dammam',
    33: 'King Abdulaziz Airport - Jeddah',
    45: 'Mecca City Center',
    89: 'Medina Downtown'
}

print('\nDASHBOARD BRANCHES:')
print('-'*70)
for branch_id, name in dashboard_branches.items():
    row = df[df['BranchId'] == branch_id]
    if len(row) > 0:
        r = row.iloc[0]
        total = r['total_vehicles']
        rented = r['rented_vehicles']
        available = r['available_vehicles']
        util = r['utilization_pct']
        print(f'{name} (ID: {branch_id})')
        print(f'  Total: {total} | Rented: {rented} | Available: {available}')
        print(f'  Utilization: {util}%')
        # Verify calculation
        calc_util = (rented / total * 100) if total > 0 else 0
        print(f'  Calculated: {calc_util:.1f}% (should match)')
        print()

print('\nUTILIZATION DISTRIBUTION:')
print('-'*70)
print(f'Min utilization: {df["utilization_pct"].min()}%')
print(f'Max utilization: {df["utilization_pct"].max()}%')
print(f'Mean utilization: {df["utilization_pct"].mean():.1f}%')
print(f'Median utilization: {df["utilization_pct"].median():.1f}%')

print('\nBRANCHES WITH LOW UTILIZATION (<30%):')
low = df[df['utilization_pct'] < 30]
print(f'Count: {len(low)}')
for _, r in low.iterrows():
    print(f'  Branch {r["BranchId"]}: {r["utilization_pct"]}% ({r["rented_vehicles"]}/{r["total_vehicles"]})')

print('\n' + '='*70)
print('EXPORT DATE:', df['export_date'].iloc[0] if 'export_date' in df.columns else 'Unknown')
print('='*70)

