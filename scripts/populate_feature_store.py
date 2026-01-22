"""
Populate Feature Store - CHUNK 6
Build the fact_daily_demand table with all features
"""
import sys
sys.path.insert(0, "backend")

from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Connection string
CONN_STR = (
    "mssql+pyodbc://localhost/eJarDbSTGLite"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

engine = create_engine(CONN_STR)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 70)
print("CHUNK 6: Feature Store Builder - Populating fact_daily_demand")
print("=" * 70)

# Import the service
from app.services.feature_store_service import FeatureStoreService

service = FeatureStoreService(db)

# Build the feature store
print("\nBuilding feature store for YELO (tenant_id=1)...")
print("Date range: 2023-01-01 to today")
print("-" * 70)

result = service.build_feature_store(
    tenant_id=1,
    start_date=date(2023, 1, 1),
    end_date=None  # Today
)

print("\n=== BUILD RESULTS ===")
print(f"Tenant ID: {result['tenant_id']}")
print(f"Date Range: {result['date_range']}")
print(f"Rows Inserted: {result['rows_inserted']:,}")
print(f"Weather Updated: {result['weather_updated']:,}")
print(f"Calendar Updated: {result['calendar_updated']:,}")
print(f"Events Updated: {result['events_updated']:,}")
print(f"Lag Features Updated: {result['lags_updated']:,}")
print(f"\nSplit Stats:")
print(f"  TRAIN: {result['split_stats'].get('train_count', 0):,}")
print(f"  VALIDATION: {result['split_stats'].get('validation_count', 0):,}")

print("\n=== FINAL STATISTICS ===")
stats = result['final_stats']
print(f"Total Rows: {stats['total_rows']:,}")
print(f"Date Range: {stats['date_range']['min']} to {stats['date_range']['max']}")
print(f"\nSplit Distribution:")
for split, count in stats['split_distribution'].items():
    print(f"  {split}: {count:,}")

print(f"\nTarget Variable (executed_rentals_count):")
print(f"  Mean: {stats['target_stats']['avg']:.2f}")
print(f"  Min: {stats['target_stats']['min']}")
print(f"  Max: {stats['target_stats']['max']}")
print(f"  Std: {stats['target_stats']['std']:.2f}")

print(f"\nFeature Completeness:")
for feature, pct in stats['feature_completeness'].items():
    print(f"  {feature}: {pct:.1f}%")

print(f"\nCoverage:")
print(f"  Branches: {stats['coverage']['branches']}")
print(f"  Categories: {stats['coverage']['categories']}")

# Validate the feature store
print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

validation = service.validate_feature_store(tenant_id=1)
print(f"\nOverall Passed: {'✅ YES' if validation['passed'] else '❌ NO'}")
print("\nValidation Checks:")
for check in validation['checks']:
    status = '✅' if check['passed'] else '❌'
    print(f"  {status} {check['name']}: {check['value']}")
    if 'threshold' in check and check['threshold'] is not None:
        print(f"     (threshold: {check['threshold']})")

db.close()
print("\n" + "=" * 70)
print("Feature store build complete!")
print("=" * 70)
