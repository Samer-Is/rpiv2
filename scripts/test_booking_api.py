"""
Test script for Booking.com API Integration with Brand/Model Extraction
Tests the new features added in CHUNK 8 modifications
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.booking_com_api import (
    BookingComCarRentalAPI, 
    get_booking_api,
    extract_brand_and_model,
    get_correct_category,
    KNOWN_BRANDS,
    CAR_MODEL_MAPPING
)

def test_brand_extraction():
    """Test the brand and model extraction function"""
    print("=" * 60)
    print("TESTING BRAND/MODEL EXTRACTION")
    print("=" * 60)
    
    test_vehicles = [
        "Toyota Camry or similar",
        "Hyundai Tucson",
        "Mercedes-Benz E-Class",
        "BMW X5 2024",
        "Nissan Patrol V8",
        "Unknown Vehicle",
        "Ford Mustang GT",
        "Kia Sorento 2023 Model",
        "Chevrolet Tahoe LTZ",
        "Lexus RX 350",
        "Range Rover Sport",
        "Porsche Cayenne",
        "Mini Cooper S",
        "Ferrari 488 Spider"
    ]
    
    print(f"\nKnown Brands Count: {len(KNOWN_BRANDS)}")
    print(f"Car Model Mappings Count: {len(CAR_MODEL_MAPPING)}")
    print()
    
    for vehicle in test_vehicles:
        brand, model = extract_brand_and_model(vehicle)
        category = get_correct_category(vehicle, "")
        print(f"Vehicle: '{vehicle}'")
        print(f"  -> Brand: {brand}, Model: {model}, Category: {category}")
        print()


def test_live_api():
    """Test live API call to Booking.com"""
    print("=" * 60)
    print("TESTING LIVE BOOKING.COM API")
    print("=" * 60)
    
    api = get_booking_api()
    
    # Test dates
    pickup = datetime.now() + timedelta(days=7)
    dropoff = pickup + timedelta(days=3)
    
    print(f"\nTest Parameters:")
    print(f"  City: Riyadh")
    print(f"  Pickup: {pickup.strftime('%Y-%m-%d')}")
    print(f"  Dropoff: {dropoff.strftime('%Y-%m-%d')}")
    print()
    
    # Test raw vehicle fetch
    print("Fetching all vehicles...")
    vehicles = api.get_all_vehicles_raw("Riyadh", pickup, dropoff)
    
    if not vehicles:
        print("WARNING: No vehicles returned from API")
        print("This could mean:")
        print("  - API rate limit reached")
        print("  - No availability for these dates")
        print("  - Location not found")
        return
    
    print(f"\nTotal Vehicles Found: {len(vehicles)}")
    print()
    
    # Analyze brands
    brands = {}
    categories = {}
    for v in vehicles:
        brand = v.get('brand', 'Unknown')
        category = v.get('category', 'Unknown')
        
        brands[brand] = brands.get(brand, 0) + 1
        categories[category] = categories.get(category, 0) + 1
    
    print("BRANDS AVAILABLE:")
    print("-" * 40)
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
        print(f"  {brand}: {count} vehicles")
    
    print()
    print("CATEGORIES AVAILABLE:")
    print("-" * 40)
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} vehicles")
    
    print()
    print("SAMPLE VEHICLES (First 10):")
    print("-" * 40)
    for v in vehicles[:10]:
        print(f"  {v.get('brand', 'Unknown')} {v.get('model', 'Unknown')}")
        print(f"    Full Name: {v.get('full_name', 'N/A')}")
        print(f"    Category: {v.get('category', 'N/A')}")
        print(f"    Price/Day: ${v.get('daily_price', 0):.2f}")
        print(f"    Supplier: {v.get('supplier', 'N/A')}")
        print()


def test_competitor_prices_by_date():
    """Test getting competitor prices organized by category"""
    print("=" * 60)
    print("TESTING COMPETITOR PRICES BY DATE")
    print("=" * 60)
    
    api = get_booking_api()
    
    pickup = datetime.now() + timedelta(days=7)
    
    print(f"\nFetching prices for Riyadh on {pickup.strftime('%Y-%m-%d')}...")
    
    prices = api.get_competitor_prices_for_date("Riyadh", pickup)
    
    if not prices:
        print("WARNING: No prices returned")
        return
    
    print(f"\nCategories with prices: {len(prices)}")
    print()
    
    for category, data in prices.items():
        print(f"CATEGORY: {category}")
        print(f"  Vehicle Count: {data.get('vehicle_count', 0)}")
        avg_price = data.get('avg_price')
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        print(f"  Avg Price: ${avg_price:.2f}" if avg_price else "  Avg Price: N/A")
        print(f"  Min Price: ${min_price:.2f}" if min_price else "  Min Price: N/A")
        print(f"  Max Price: ${max_price:.2f}" if max_price else "  Max Price: N/A")
        
        if data.get('brands_available'):
            print(f"  Brands: {', '.join(data['brands_available'][:5])}...")
        if data.get('models_available'):
            print(f"  Models: {', '.join(data['models_available'][:5])}...")
        
        print(f"  Competitors: {len(data.get('competitors', []))}")
        for comp in data.get('competitors', [])[:3]:
            print(f"    - {comp.get('supplier', 'N/A')}: {comp.get('vehicle', 'N/A')} @ ${comp.get('price', 0):.2f}")
            print(f"      Brand: {comp.get('brand', 'Unknown')}, Model: {comp.get('model', 'Unknown')}")
        print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" BOOKING.COM API TEST - Brand/Model Extraction")
    print("=" * 70 + "\n")
    
    # Test extraction logic first (no API call)
    test_brand_extraction()
    print("\n")
    
    # Ask user before making API calls
    print("=" * 60)
    print("Ready to test LIVE API")
    print("This will make real API calls to Booking.com")
    print("=" * 60)
    
    proceed = input("\nProceed with live API test? (y/n): ")
    
    if proceed.lower() == 'y':
        test_live_api()
        print("\n")
        test_competitor_prices_by_date()
    else:
        print("Skipping live API tests")
    
    print("\n" + "=" * 70)
    print(" TEST COMPLETE")
    print("=" * 70 + "\n")
