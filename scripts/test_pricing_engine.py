"""
Test script for CHUNK 9 - Pricing Engine
Tests the pricing recommendation generation with real data
"""
import sys
from pathlib import Path
from datetime import date, timedelta

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import pyodbc

# Connection string
CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=eJarDbSTGLite;"
    "Trusted_Connection=yes;"
)


def test_pricing_engine():
    """Test the pricing engine service directly"""
    print("=" * 70)
    print(" CHUNK 9 - PRICING ENGINE TEST")
    print("=" * 70)
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create SQLAlchemy engine
    engine = create_engine(
        "mssql+pyodbc://localhost/eJarDbSTGLite?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )
    Session = sessionmaker(bind=engine)
    db = Session()
    
    from app.services.pricing_engine import PricingEngineService, SignalWeights, Guardrails
    
    print("\n1. Testing Signal Weights...")
    service = PricingEngineService(db)
    weights = service.get_signal_weights(tenant_id=1)
    print(f"   Weights: utilization={weights.utilization}, forecast={weights.forecast}")
    print(f"            competitor={weights.competitor}, weather={weights.weather}")
    print(f"            holiday={weights.holiday}")
    print(f"   Valid (sum=1): {weights.validate()}")
    
    print("\n2. Testing Guardrails...")
    for cat_id in [1, 2, 3, 4]:
        guard = service.get_guardrails(tenant_id=1, category_id=cat_id)
        print(f"   Category {cat_id}: min={guard.min_price}, max_disc={guard.max_discount_pct}%, max_prem={guard.max_premium_pct}%")
    
    print("\n3. Testing Base Rates...")
    # Use MVP branches
    test_branches = [122, 15, 26]  # Airports
    test_categories = [1, 3, 4]  # Economy, Standard, SUV
    
    for branch_id in test_branches[:1]:
        for cat_id in test_categories[:1]:
            rates = service.get_base_rates(tenant_id=1, branch_id=branch_id, category_id=cat_id)
            print(f"   B{branch_id}/C{cat_id}: daily={rates['daily']}, weekly={rates['weekly']}, monthly={rates['monthly']}")
    
    print("\n4. Testing Signal Calculations...")
    target_date = date.today() + timedelta(days=7)
    branch_id = 122
    category_id = 1
    
    util = service.get_utilization_signal(1, branch_id, category_id, target_date)
    print(f"   Utilization signal: {util}")
    
    fcst = service.get_forecast_signal(1, branch_id, category_id, target_date)
    print(f"   Forecast signal: {fcst}")
    
    base_rates = service.get_base_rates(1, branch_id, category_id)
    comp = service.get_competitor_signal(1, branch_id, category_id, target_date, base_rates['daily'])
    print(f"   Competitor signal: {comp}")
    
    wthr = service.get_weather_signal(branch_id, target_date)
    print(f"   Weather signal: {wthr}")
    
    hldy = service.get_holiday_signal(target_date)
    print(f"   Holiday signal: {hldy}")
    
    print("\n5. Testing Adjustment Calculation...")
    raw_adj = service.calculate_adjustment(weights, util, fcst, comp, wthr, hldy)
    print(f"   Raw adjustment: {raw_adj}%")
    
    print("\n6. Generating Sample Recommendations...")
    start_date = date.today()
    
    print(f"   Branch: {branch_id}, Category: {category_id}")
    print(f"   Start date: {start_date}")
    print(f"   Generating 7 days of recommendations...")
    
    recommendations = service.generate_recommendations(
        tenant_id=1,
        branch_id=branch_id,
        category_id=category_id,
        start_date=start_date,
        horizon_days=7
    )
    
    print(f"\n   Generated {len(recommendations)} recommendations:")
    print("-" * 90)
    print(f"   {'Date':<12} {'Base':<8} {'Rec':<8} {'Adj%':<8} {'Util':<6} {'Fcst':<6} {'Comp':<6} {'Guard':<6}")
    print("-" * 90)
    
    for rec in recommendations:
        print(f"   {rec.forecast_date} {rec.base_daily:<8.2f} {rec.rec_daily:<8.2f} "
              f"{rec.premium_discount_pct:>+7.2f}% "
              f"{float(rec.utilization_signal):<6.2f} {float(rec.forecast_signal):<6.2f} "
              f"{float(rec.competitor_signal):<6.2f} {'YES' if rec.guardrail_applied else 'NO':<6}")
    
    print("\n   Sample explanation:")
    print(f"   {recommendations[0].explanation_text}")
    
    print("\n7. Saving Recommendations to Database...")
    saved = service.save_recommendations(
        tenant_id=1,
        branch_id=branch_id,
        category_id=category_id,
        recommendations=recommendations
    )
    print(f"   Saved {saved} recommendations to database")
    
    # Verify in database
    from sqlalchemy import text
    result = db.execute(text("""
        SELECT COUNT(*), MIN(forecast_date), MAX(forecast_date)
        FROM dynamicpricing.recommendations_30d
        WHERE tenant_id = 1 AND branch_id = :branch_id AND category_id = :category_id
    """), {"branch_id": branch_id, "category_id": category_id})
    row = result.fetchone()
    print(f"   Database verification: {row[0]} records, dates {row[1]} to {row[2]}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print(" CHUNK 9 TEST COMPLETE ✓")
    print("=" * 70)


def test_full_pipeline():
    """Test generating recommendations for all branches/categories"""
    print("\n" + "=" * 70)
    print(" FULL PIPELINE TEST")
    print("=" * 70)
    
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(
        "mssql+pyodbc://localhost/eJarDbSTGLite?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )
    Session = sessionmaker(bind=engine)
    db = Session()
    
    from app.services.pricing_engine import PricingEngineService
    
    service = PricingEngineService(db)
    
    print("\nRunning full pipeline for all MVP branches and categories...")
    print("(This may take a few minutes)\n")
    
    stats = service.run_full_pipeline(
        tenant_id=1,
        start_date=date.today(),
        horizon_days=30
    )
    
    print("Pipeline Results:")
    print(f"  - Branches processed: {stats['branches_processed']}")
    print(f"  - Categories processed: {stats['categories_processed']}")
    print(f"  - Recommendations generated: {stats['recommendations_generated']}")
    print(f"  - Recommendations saved: {stats['recommendations_saved']}")
    
    if stats['errors']:
        print(f"  - Errors: {len(stats['errors'])}")
        for err in stats['errors'][:5]:
            print(f"    * {err}")
    
    db.close()
    
    print("\n" + "=" * 70)
    print(" FULL PIPELINE TEST COMPLETE ✓")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" DYNAMIC PRICING ENGINE - CHUNK 9 TEST SUITE")
    print("=" * 70 + "\n")
    
    # Run basic test
    test_pricing_engine()
    
    # Ask before running full pipeline
    print("\n" + "-" * 70)
    proceed = input("\nRun full pipeline for all branches/categories? (y/n): ")
    
    if proceed.lower() == 'y':
        test_full_pipeline()
    else:
        print("Skipping full pipeline test")
    
    print("\n" + "=" * 70)
    print(" ALL TESTS COMPLETE")
    print("=" * 70 + "\n")
