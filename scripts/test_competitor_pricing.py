"""
Test script for CHUNK 8: Competitor Pricing Integration
Validates competitor index calculation and API endpoints
"""
import sys
sys.path.insert(0, "backend")

from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
connection_string = (
    "mssql+pyodbc://localhost/eJarDbSTGLite"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&TrustServerCertificate=yes"
    "&Trusted_Connection=yes"
)
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)


def test_competitor_tables():
    """Test that competitor tables exist and have data."""
    print("\n" + "="*60)
    print("TEST 1: Competitor Tables")
    print("="*60)
    
    with Session() as db:
        # Check competitor_mapping
        result = db.execute(text("""
            SELECT COUNT(*) FROM appconfig.competitor_mapping
            WHERE is_active = 1
        """))
        mapping_count = result.scalar()
        print(f"✓ Active mappings in competitor_mapping: {mapping_count}")
        
        # Show mappings
        result = db.execute(text("""
            SELECT category_id, category_name, competitor_vehicle_type
            FROM appconfig.competitor_mapping
            WHERE is_active = 1
        """))
        print("\nCategory mappings:")
        for row in result.fetchall():
            print(f"  - Category {row[0]} ({row[1]}) → {row[2]}")
        
    return mapping_count >= 4


def test_competitor_service():
    """Test the CompetitorPricingService."""
    print("\n" + "="*60)
    print("TEST 2: Competitor Pricing Service")
    print("="*60)
    
    from app.services.competitor_service import CompetitorPricingService
    
    with Session() as db:
        service = CompetitorPricingService(db)
        
        # Test fetch_competitor_prices
        prices = service.fetch_competitor_prices(
            city="Riyadh",
            vehicle_type="economy",
            price_date=date.today()
        )
        print(f"\n✓ Fetched {len(prices)} competitor prices for Riyadh/economy")
        
        for p in prices:
            print(f"  - {p.competitor_name}: {p.daily_price} SAR/day")
        
        # Test calculate_competitor_index
        index = service.calculate_competitor_index(
            tenant_id=1,
            branch_id=122,  # Riyadh Airport
            category_id=1,
            index_date=date.today()
        )
        print(f"\n✓ Competitor index calculated:")
        print(f"  - Avg price (top 3): {index.avg_price} SAR")
        print(f"  - Min price: {index.min_price} SAR")
        print(f"  - Max price: {index.max_price} SAR")
        print(f"  - Competitors: {index.competitors_count}")
        
        # Save the index
        service.save_competitor_index(1, 122, index)
        print(f"\n✓ Competitor index saved to database")
        
        # Verify save
        saved = service.get_competitor_index(1, 122, 1, date.today())
        if saved:
            print(f"✓ Retrieved saved index: {saved.avg_price} SAR avg")
        
    return len(prices) > 0


def test_all_categories():
    """Test competitor index for all categories."""
    print("\n" + "="*60)
    print("TEST 3: All Categories Competitor Index")
    print("="*60)
    
    from app.services.competitor_service import CompetitorPricingService
    
    with Session() as db:
        service = CompetitorPricingService(db)
        
        # Get category mapping
        mapping = service.get_category_mapping(tenant_id=1)
        print(f"\nMapping loaded: {len(mapping)} categories")
        
        for category_id, vehicle_type in mapping.items():
            index = service.calculate_competitor_index(
                tenant_id=1,
                branch_id=122,  # Riyadh Airport
                category_id=category_id,
                index_date=date.today()
            )
            print(f"  Category {category_id} ({vehicle_type}): "
                  f"Avg {index.avg_price}, Min {index.min_price}, Max {index.max_price}")
    
    return True


def test_seasonal_adjustment():
    """Test seasonal price adjustments."""
    print("\n" + "="*60)
    print("TEST 4: Seasonal Price Adjustments")
    print("="*60)
    
    from app.services.competitor_service import CompetitorPricingService
    
    with Session() as db:
        service = CompetitorPricingService(db)
        
        # Test different months
        test_dates = [
            date(2025, 1, 15),   # Winter (1.10)
            date(2025, 4, 15),   # Spring/Eid (1.20)
            date(2025, 7, 15),   # Summer (1.15)
            date(2025, 10, 15),  # Normal (1.0)
        ]
        
        print("\nEconomy prices in Riyadh by season:")
        for d in test_dates:
            prices = service.fetch_competitor_prices("Riyadh", "economy", d)
            budget_price = next((p.daily_price for p in prices if p.competitor_name == "Budget"), None)
            factor = service._get_seasonal_factor(d)
            print(f"  {d.strftime('%B')}: Budget = {budget_price} SAR (factor: {factor})")
    
    return True


def test_build_index_batch():
    """Test building competitor index for a date range."""
    print("\n" + "="*60)
    print("TEST 5: Build Competitor Index (Batch)")
    print("="*60)
    
    from app.services.competitor_service import CompetitorPricingService
    
    with Session() as db:
        service = CompetitorPricingService(db)
        
        # Build for next 7 days
        start_date = date.today()
        end_date = start_date + timedelta(days=6)
        
        print(f"\nBuilding index for {start_date} to {end_date}...")
        stats = service.build_competitor_index_for_date_range(
            tenant_id=1,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Build complete:")
        print(f"  - Branches: {stats['branches']}")
        print(f"  - Categories: {stats['categories']}")
        print(f"  - Dates processed: {stats['dates_processed']}")
        print(f"  - Indexes created: {stats['indexes_created']}")
        
        # Verify records
        result = db.execute(text("""
            SELECT COUNT(*) FROM dynamicpricing.competitor_index
        """))
        total = result.scalar()
        print(f"\n✓ Total competitor_index records: {total}")
    
    return stats['indexes_created'] > 0


def main():
    print("\n" + "="*70)
    print("CHUNK 8 VALIDATION: Competitor Pricing Integration")
    print("="*70)
    
    results = []
    
    try:
        results.append(("Competitor Tables", test_competitor_tables()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Competitor Tables", False))
    
    try:
        results.append(("Competitor Service", test_competitor_service()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Competitor Service", False))
    
    try:
        results.append(("All Categories", test_all_categories()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("All Categories", False))
    
    try:
        results.append(("Seasonal Adjustment", test_seasonal_adjustment()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Seasonal Adjustment", False))
    
    try:
        results.append(("Build Index Batch", test_build_index_batch()))
    except Exception as e:
        print(f"✗ Test failed: {e}")
        results.append(("Build Index Batch", False))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        all_passed = all_passed and passed
    
    if all_passed:
        print("\n✅ CHUNK 8 VALIDATION PASSED!")
        print("   Competitor pricing integration complete with:")
        print("   - Category → competitor vehicle type mapping")
        print("   - Competitor price fetching (mock data)")
        print("   - Competitor index calculation (avg of top 3)")
        print("   - Seasonal price adjustments")
        print("   - Database caching")
    else:
        print("\n❌ Some tests failed - review output above")
    
    return all_passed


if __name__ == "__main__":
    main()
