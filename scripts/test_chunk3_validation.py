"""
CHUNK 3 Validation Test
Validates base price engine functionality per instructions.txt requirements:
- Verify prices exist for 5 random branch × category cases
- Validate effective period logic
"""
import sys
from datetime import date, datetime
from decimal import Decimal

# Add backend to path
sys.path.insert(0, 'c:\\Users\\s.ismail\\OneDrive - Al-Manzumah Al-Muttahidah For IT Systems\\Desktop\\DYNAMIC_PRICING_FROM_SCRATCH_V7_crsr')

from backend.app.services.base_rate_service import get_base_rate_service

def run_validation():
    print("=" * 80)
    print("CHUNK 3 VALIDATION: Base Price Engine")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    service = get_base_rate_service(tenant_id=1)  # YELO
    simulation_date = date(2025, 5, 31)
    
    # MVP Branches and Categories
    mvp_branches = [2, 15, 26, 34, 122, 211]
    mvp_categories = [1, 2, 3, 13, 27, 29]
    
    branch_names = {
        2: "Al Quds - Riyadh",
        15: "King Abdulaziz Airport - Jeddah",
        26: "Abha Airport",
        34: "Al Khaldiyah - Al Madina",
        122: "King Khalid Airport - Riyadh",
        211: "Al Yarmuk - Riyadh"
    }
    
    category_names = {
        1: "Economy",
        2: "Small Sedan",
        3: "Intermediate Sedan",
        13: "Intermediate SUV",
        27: "Compact",
        29: "Economy SUV"
    }
    
    all_tests_passed = True
    test_results = []
    
    # Test 1: Verify 5 random branch × category combinations have prices
    print("\n" + "=" * 70)
    print("TEST 1: Verify prices exist for 5 branch × category combinations")
    print("=" * 70)
    
    test_cases = [
        (122, 27),  # Riyadh Airport × Compact
        (2, 1),     # Al Quds × Economy
        (15, 3),    # Jeddah Airport × Intermediate Sedan
        (211, 13),  # Al Yarmuk × Intermediate SUV
        (34, 29),   # Al Madina × Economy SUV
    ]
    
    for branch_id, category_id in test_cases:
        result = service.get_base_prices_for_category(branch_id, category_id, simulation_date)
        
        branch_name = branch_names.get(branch_id, f"Branch {branch_id}")
        category_name = category_names.get(category_id, f"Category {category_id}")
        
        if result and result.daily_rate > 0:
            status = "✓ PASS"
            test_results.append(True)
            print(f"\n{status}: {branch_name} × {category_name}")
            print(f"   Daily:   {result.daily_rate:.2f} SAR")
            print(f"   Weekly:  {result.weekly_rate:.2f} SAR")
            print(f"   Monthly: {result.monthly_rate:.2f} SAR")
            print(f"   Source:  {result.source}")
            print(f"   Models:  {result.model_count}")
        else:
            status = "✗ FAIL"
            test_results.append(False)
            all_tests_passed = False
            print(f"\n{status}: {branch_name} × {category_name}")
            print(f"   No prices found!")
    
    # Test 2: Validate effective period logic
    print("\n" + "=" * 70)
    print("TEST 2: Validate effective period logic")
    print("=" * 70)
    
    # Test with different dates
    test_dates = [
        date(2025, 5, 31),   # Simulation date
        date(2025, 6, 15),   # Within validation period
        date(2024, 1, 1),    # Historical date
        date(2025, 11, 1),   # Future date (within validation)
    ]
    
    branch_id = 122
    category_id = 27
    
    for test_date in test_dates:
        result = service.get_base_prices_for_category(branch_id, category_id, test_date)
        
        if result and result.daily_rate > 0:
            status = "✓ PASS"
            test_results.append(True)
            print(f"\n{status}: Date {test_date}")
            print(f"   Daily Rate: {result.daily_rate:.2f} SAR (Models: {result.model_count})")
        else:
            status = "✗ FAIL"
            test_results.append(False)
            all_tests_passed = False
            print(f"\n{status}: Date {test_date} - No prices found")
    
    # Test 3: Verify MVP category prices summary
    print("\n" + "=" * 70)
    print("TEST 3: Verify MVP category prices summary")
    print("=" * 70)
    
    mvp_prices = service.get_mvp_category_prices(simulation_date)
    
    expected_categories = {1, 2, 3, 13, 27, 29}
    found_categories = set(mvp_prices.keys())
    
    if expected_categories == found_categories:
        status = "✓ PASS"
        test_results.append(True)
        print(f"\n{status}: All 6 MVP categories have prices")
    else:
        status = "✗ FAIL"
        test_results.append(False)
        all_tests_passed = False
        missing = expected_categories - found_categories
        print(f"\n{status}: Missing categories: {missing}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("MVP CATEGORY PRICES SUMMARY")
    print("=" * 80)
    print(f"{'Category':<25} {'Daily':>12} {'Weekly':>12} {'Monthly':>12} {'Models':>8}")
    print("-" * 80)
    
    for cat_id in sorted(mvp_prices.keys()):
        info = mvp_prices[cat_id]
        daily = f"{info['daily_rate']:.2f}" if info['daily_rate'] else "N/A"
        weekly = f"{info['weekly_rate']:.2f}" if info['weekly_rate'] else "N/A"
        monthly = f"{info['monthly_rate']:.2f}" if info['monthly_rate'] else "N/A"
        print(f"{info['category_name']:<25} {daily:>12} {weekly:>12} {monthly:>12} {info['model_count']:>8}")
    
    # Test 4: Verify model-level prices
    print("\n" + "=" * 70)
    print("TEST 4: Verify model-level prices for Compact category")
    print("=" * 70)
    
    model_prices = service.get_model_prices(27, simulation_date)
    
    if len(model_prices) > 0:
        status = "✓ PASS"
        test_results.append(True)
        print(f"\n{status}: Found {len(model_prices)} models in Compact category")
        print(f"\n{'Model':<30} {'Daily':>10} {'Weekly':>10} {'Monthly':>10}")
        print("-" * 65)
        for mp in model_prices[:5]:  # Show first 5
            daily = f"{mp.daily_rate:.2f}" if mp.daily_rate else "N/A"
            weekly = f"{mp.weekly_rate:.2f}" if mp.weekly_rate else "N/A"
            monthly = f"{mp.monthly_rate:.2f}" if mp.monthly_rate else "N/A"
            print(f"{mp.model_name[:28]:<30} {daily:>10} {weekly:>10} {monthly:>10}")
    else:
        status = "✗ FAIL"
        test_results.append(False)
        all_tests_passed = False
        print(f"\n{status}: No models found!")
    
    # Final summary
    print("\n" + "=" * 80)
    print("CHUNK 3 VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in test_results if r)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Overall Status: {'✓ ALL TESTS PASSED' if all_tests_passed else '✗ SOME TESTS FAILED'}")
    
    if all_tests_passed:
        print("\n✓ CHUNK 3 VALIDATION COMPLETE - Ready to commit!")
    else:
        print("\n✗ CHUNK 3 VALIDATION FAILED - Please review failures")
    
    return all_tests_passed


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
