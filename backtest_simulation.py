"""
Pricing Strategy Backtest Simulation
Simulates dynamic pricing for 1 week across 2 branches and all categories
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pricing_engine import DynamicPricingEngine
from external_data_fetcher import create_holiday_features
import warnings
warnings.filterwarnings('ignore')

# Configuration
SIMULATION_START = datetime(2025, 11, 10)  # Start date (Monday)
SIMULATION_DAYS = 7  # One week
BRANCHES = [122, 33]  # King Khalid Airport - Riyadh, King Abdulaziz Airport - Jeddah
BRANCH_NAMES = {
    122: "King Khalid Airport - Riyadh",
    33: "King Abdulaziz Airport - Jeddah"
}
CATEGORIES = {
    "Economy": 150.0,
    "Compact": 180.0,
    "Standard": 220.0,
    "SUV Compact": 280.0,
    "SUV Standard": 350.0,
    "SUV Large": 500.0,
    "Luxury Sedan": 600.0,
    "Luxury SUV": 800.0
}

def run_backtest():
    """Run complete backtest simulation"""
    
    print("="*100)
    print("PRICING STRATEGY BACKTEST SIMULATION")
    print("="*100)
    print(f"Period: {SIMULATION_START.date()} to {(SIMULATION_START + timedelta(days=SIMULATION_DAYS-1)).date()}")
    print(f"Branches: {len(BRANCHES)} ({', '.join([BRANCH_NAMES[b] for b in BRANCHES])})")
    print(f"Categories: {len(CATEGORIES)}")
    print(f"Total Simulations: {SIMULATION_DAYS} days × {len(BRANCHES)} branches × {len(CATEGORIES)} categories = {SIMULATION_DAYS * len(BRANCHES) * len(CATEGORIES)} price points")
    print("="*100)
    
    # Load pricing engine
    print("\n[*] Loading pricing engine...")
    engine = DynamicPricingEngine()
    print("[OK] Pricing engine loaded successfully")
    
    # Run simulation for each branch
    all_results = []
    
    for branch_id in BRANCHES:
        branch_name = BRANCH_NAMES[branch_id]
        print(f"\n{'='*100}")
        print(f"BRANCH: {branch_name} (ID: {branch_id})")
        print(f"{'='*100}")
        
        for day_offset in range(SIMULATION_DAYS):
            current_date = SIMULATION_START + timedelta(days=day_offset)
            day_name = current_date.strftime('%A')
            
            print(f"\n[DATE] {day_name}, {current_date.date()}")
            print("-"*100)
            
            # Get external features for this date
            is_weekend = current_date.weekday() in [4, 5]  # Friday, Saturday
            is_holiday = False  # Set based on actual calendar
            is_ramadan = False
            is_hajj = False
            
            # Simulate fleet utilization (varies by day)
            # Weekend = higher utilization, weekday = lower
            if is_weekend:
                utilization = np.random.uniform(0.65, 0.85)  # 65-85% rented on weekends
            else:
                utilization = np.random.uniform(0.40, 0.60)  # 40-60% on weekdays
            
            total_vehicles = 100
            rented_vehicles = int(total_vehicles * utilization)
            available_vehicles = total_vehicles - rented_vehicles
            
            print(f"Fleet Status: {rented_vehicles}/{total_vehicles} rented ({utilization*100:.0f}% utilization)")
            print(f"Conditions: {'Weekend' if is_weekend else 'Weekday'}")
            
            # Calculate prices for all categories
            day_results = []
            
            for category, base_price in CATEGORIES.items():
                # Get optimized price
                result = engine.calculate_optimized_price(
                    target_date=current_date,
                    branch_id=branch_id,
                    base_price=base_price,
                    available_vehicles=available_vehicles,
                    total_vehicles=total_vehicles,
                    city_id=1 if branch_id == 122 else 2,
                    city_name="Riyadh" if branch_id == 122 else "Jeddah",
                    is_airport=True,  # Both are airports
                    is_holiday=is_holiday,
                    is_school_vacation=False,
                    is_ramadan=is_ramadan,
                    is_umrah_season=False,
                    is_hajj=is_hajj,
                    is_festival=False,
                    is_sports_event=False,
                    is_conference=False,
                    days_to_holiday=-1
                )
                
                # Store results
                day_results.append({
                    'date': current_date.date(),
                    'day_name': day_name,
                    'branch_id': branch_id,
                    'branch_name': branch_name,
                    'category': category,
                    'base_price': base_price,
                    'optimized_price': result['final_price'],
                    'price_change_pct': result['price_change_pct'],
                    'predicted_demand': result.get('predicted_demand', 0),
                    'demand_multiplier': result['demand_multiplier'],
                    'supply_multiplier': result['supply_multiplier'],
                    'event_multiplier': result['event_multiplier'],
                    'utilization_pct': utilization * 100,
                    'is_weekend': is_weekend,
                    'explanation': result['explanation']
                })
            
            # Print summary for this day
            df_day = pd.DataFrame(day_results)
            print(f"\n{'Category':<15} {'Base':>8} {'Optimized':>10} {'Change':>8} {'Demand':>7} {'Supply':>7} {'Event':>7}")
            print("-"*100)
            
            for _, row in df_day.iterrows():
                change_color = "+" if row['price_change_pct'] > 0 else ""
                print(f"{row['category']:<15} {row['base_price']:>8.0f} SAR {row['optimized_price']:>9.0f} SAR "
                      f"{change_color}{row['price_change_pct']:>6.1f}% "
                      f"{row['demand_multiplier']:>6.2f}x {row['supply_multiplier']:>6.2f}x {row['event_multiplier']:>6.2f}x")
            
            all_results.extend(day_results)
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(all_results)
    
    # Summary Statistics
    print("\n" + "="*100)
    print("SIMULATION SUMMARY")
    print("="*100)
    
    print("\n[STATISTICS] Overall Statistics:")
    print(f"Total Price Points Simulated: {len(df)}")
    print(f"Average Price Change: {df['price_change_pct'].mean():+.2f}%")
    print(f"Price Increases: {(df['price_change_pct'] > 0).sum()} ({(df['price_change_pct'] > 0).sum()/len(df)*100:.1f}%)")
    print(f"Price Decreases: {(df['price_change_pct'] < 0).sum()} ({(df['price_change_pct'] < 0).sum()/len(df)*100:.1f}%)")
    print(f"No Change: {(df['price_change_pct'] == 0).sum()} ({(df['price_change_pct'] == 0).sum()/len(df)*100:.1f}%)")
    
    print("\n[DISTRIBUTION] Price Change Distribution:")
    print(f"Maximum Increase: +{df['price_change_pct'].max():.1f}%")
    print(f"Maximum Decrease: {df['price_change_pct'].min():.1f}%")
    print(f"Average Absolute Change: {df['price_change_pct'].abs().mean():.2f}%")
    
    print("\n[BRANCH] By Branch:")
    for branch_id in BRANCHES:
        branch_df = df[df['branch_id'] == branch_id]
        print(f"\n{BRANCH_NAMES[branch_id]}:")
        print(f"  Average Price Change: {branch_df['price_change_pct'].mean():+.2f}%")
        print(f"  Increases: {(branch_df['price_change_pct'] > 0).sum()}/{len(branch_df)} ({(branch_df['price_change_pct'] > 0).sum()/len(branch_df)*100:.1f}%)")
        print(f"  Decreases: {(branch_df['price_change_pct'] < 0).sum()}/{len(branch_df)} ({(branch_df['price_change_pct'] < 0).sum()/len(branch_df)*100:.1f}%)")
    
    print("\n[CATEGORY] By Category:")
    for category in CATEGORIES.keys():
        cat_df = df[df['category'] == category]
        avg_change = cat_df['price_change_pct'].mean()
        print(f"{category:<15}: Avg change {avg_change:+.2f}%, "
              f"Range [{cat_df['price_change_pct'].min():.1f}% to +{cat_df['price_change_pct'].max():.1f}%]")
    
    print("\n[WEEKDAY/WEEKEND] Weekday vs Weekend:")
    weekend_df = df[df['is_weekend'] == True]
    weekday_df = df[df['is_weekend'] == False]
    print(f"Weekend Avg Change: {weekend_df['price_change_pct'].mean():+.2f}%")
    print(f"Weekday Avg Change: {weekday_df['price_change_pct'].mean():+.2f}%")
    
    print("\n[MULTIPLIERS] Multiplier Averages:")
    print(f"Demand Multiplier: {df['demand_multiplier'].mean():.3f}x (range: {df['demand_multiplier'].min():.2f}x - {df['demand_multiplier'].max():.2f}x)")
    print(f"Supply Multiplier: {df['supply_multiplier'].mean():.3f}x (range: {df['supply_multiplier'].min():.2f}x - {df['supply_multiplier'].max():.2f}x)")
    print(f"Event Multiplier: {df['event_multiplier'].mean():.3f}x (range: {df['event_multiplier'].min():.2f}x - {df['event_multiplier'].max():.2f}x)")
    
    # Revenue Impact Analysis (Simulated)
    print("\n" + "="*100)
    print("ESTIMATED REVENUE IMPACT (Simulated)")
    print("="*100)
    
    # Assume each price point represents potential daily revenue per vehicle
    # Conservative assumption: 0.5 rentals per day per category per branch
    daily_rentals_per_category = 0.5
    
    base_revenue = df['base_price'].sum() * daily_rentals_per_category
    optimized_revenue = df['optimized_price'].sum() * daily_rentals_per_category
    revenue_diff = optimized_revenue - base_revenue
    revenue_diff_pct = (revenue_diff / base_revenue) * 100
    
    print(f"\n[REVENUE] Simulated Weekly Revenue (assuming {daily_rentals_per_category} rentals/day/category):")
    print(f"Base Pricing Revenue: {base_revenue:,.0f} SAR")
    print(f"Dynamic Pricing Revenue: {optimized_revenue:,.0f} SAR")
    print(f"Difference: {revenue_diff:+,.0f} SAR ({revenue_diff_pct:+.2f}%)")
    
    print("\n[NOTE] This is a simplified simulation. Actual results depend on:")
    print("  - Real booking patterns and price elasticity")
    print("  - Competitor pricing and market conditions")
    print("  - Seasonal demand fluctuations")
    print("  - Customer behavior and loyalty")
    
    # Export results
    output_file = f"backtest_results_{SIMULATION_START.strftime('%Y%m%d')}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n[OK] Detailed results exported to: {output_file}")
    
    # Create summary by day and branch
    print("\n" + "="*100)
    print("DAILY SUMMARY BY BRANCH")
    print("="*100)
    
    summary = df.groupby(['date', 'branch_name']).agg({
        'price_change_pct': 'mean',
        'optimized_price': 'mean',
        'base_price': 'mean'
    }).round(2)
    
    print("\n" + summary.to_string())
    
    return df


if __name__ == "__main__":
    results_df = run_backtest()
    
    print("\n" + "="*100)
    print("SIMULATION COMPLETE")
    print("="*100)
    print("\n[TAKEAWAYS] Key Takeaways:")
    print("1. Dynamic pricing adjusts based on demand predictions and fleet utilization")
    print("2. Weekend prices typically higher due to increased demand")
    print("3. Airport locations get automatic premium (+10%)")
    print("4. System balances revenue optimization with competitive positioning")
    print("\n[EXPORT] Review the exported CSV file for detailed analysis")

