"""
Competitor Pricing Module

Loads and analyzes competitor pricing data for comparison with Renty's dynamic pricing.

Features:
1. Load competitor prices from CSV
2. Calculate average competitor prices by category
3. Compare Renty prices vs competitors
4. Generate competitive positioning insights
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_competitor_prices(file_path: str = "data/competitor_prices/competitor_prices.csv") -> pd.DataFrame:
    """
    Load competitor pricing data from CSV.
    
    Expected columns:
    - Date: Pricing date
    - Category: Vehicle category (Economy, Compact, Standard, etc.)
    - Competitor_Name: Name of competitor (Hertz, Budget, etc.)
    - Competitor_Price: Their price (SAR/day)
    - Branch_City: City/location
    - Notes: Optional notes
    
    Args:
        file_path: Path to competitor pricing CSV
        
    Returns:
        pd.DataFrame: Competitor pricing data
    """
    try:
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        logger.info(f"✓ Loaded {len(df)} competitor price points")
        logger.info(f"  Competitors: {df['Competitor_Name'].unique().tolist()}")
        logger.info(f"  Categories: {df['Category'].unique().tolist()}")
        logger.info(f"  Cities: {df['Branch_City'].unique().tolist()}")
        
        return df
    except FileNotFoundError:
        logger.warning(f"⚠ Competitor pricing file not found: {file_path}")
        logger.info("  Using template competitor prices...")
        return get_default_competitor_prices()
    except Exception as e:
        logger.error(f"✗ Error loading competitor prices: {e}")
        return get_default_competitor_prices()


def get_default_competitor_prices() -> pd.DataFrame:
    """
    Get default/template competitor prices if no file exists.
    
    Returns:
        pd.DataFrame: Default competitor prices
    """
    # Default competitor prices (SAR/day) - Saudi market averages
    data = {
        'Date': [datetime.now().date()] * 24,
        'Category': [
            'Economy', 'Economy', 'Economy',
            'Compact', 'Compact', 'Compact',
            'Standard', 'Standard', 'Standard',
            'SUV Compact', 'SUV Compact', 'SUV Compact',
            'SUV Standard', 'SUV Standard', 'SUV Standard',
            'SUV Large', 'SUV Large', 'SUV Large',
            'Luxury Sedan', 'Luxury Sedan', 'Luxury Sedan',
            'Luxury SUV', 'Luxury SUV', 'Luxury SUV'
        ],
        'Competitor_Name': [
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty',
            'Hertz', 'Budget', 'Thrifty'
        ],
        'Competitor_Price': [
            140, 135, 138,  # Economy
            170, 165, 168,  # Compact
            210, 205, 208,  # Standard
            270, 265, 268,  # SUV Compact
            340, 335, 338,  # SUV Standard
            480, 475, 478,  # SUV Large
            580, 575, 578,  # Luxury Sedan
            780, 775, 778   # Luxury SUV
        ],
        'Branch_City': ['Riyadh'] * 24,
        'Notes': ['Market average'] * 24
    }
    
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    
    return df


def calculate_average_competitor_price(competitor_df: pd.DataFrame, 
                                       category: str,
                                       city: str = None,
                                       branch_id: int = None,
                                       date: datetime = None) -> dict:
    """
    Calculate average competitor price for a category.
    
    Args:
        competitor_df: Competitor pricing dataframe
        category: Vehicle category
        city: Optional city filter
        date: Optional date filter
        
    Returns:
        dict: Competitor pricing statistics
    """
    # Filter data
    mask = competitor_df['Category'] == category
    
    # Priority: Branch ID > City > All
    if branch_id and 'Branch_ID' in competitor_df.columns:
        mask = mask & (competitor_df['Branch_ID'] == branch_id)
    elif city:
        mask = mask & (competitor_df['Branch_City'] == city)
    
    # Filter by date (use most recent if date not found)
    if date:
        date_str = pd.to_datetime(date).date()
        competitor_df['date_only'] = pd.to_datetime(competitor_df['Date']).dt.date
        
        # Try exact date first
        date_mask = mask & (competitor_df['date_only'] == date_str)
        if date_mask.sum() > 0:
            mask = date_mask
        else:
            # Use most recent date before the target date
            filtered_dates = competitor_df[mask]
            if len(filtered_dates) > 0:
                most_recent = filtered_dates['Date'].max()
                mask = mask & (competitor_df['Date'] == most_recent)
    
    filtered = competitor_df[mask]
    
    if len(filtered) == 0:
        # No data, return market defaults
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'competitor_count': 0,
            'competitors': []
        }
    
    return {
        'avg_price': filtered['Competitor_Price'].mean(),
        'min_price': filtered['Competitor_Price'].min(),
        'max_price': filtered['Competitor_Price'].max(),
        'competitor_count': filtered['Competitor_Name'].nunique(),
        'competitors': filtered[['Competitor_Name', 'Competitor_Price']].to_dict('records')
    }


def compare_with_competitors(renty_price: float, 
                            competitor_stats: dict) -> dict:
    """
    Compare Renty price with competitor prices.
    
    Args:
        renty_price: Renty's optimized price
        competitor_stats: Competitor pricing statistics
        
    Returns:
        dict: Comparison analysis
    """
    if competitor_stats['avg_price'] is None:
        return {
            'position': 'Unknown',
            'price_difference': 0,
            'price_difference_pct': 0,
            'competitive_advantage': 'No competitor data available'
        }
    
    avg_comp = competitor_stats['avg_price']
    min_comp = competitor_stats['min_price']
    max_comp = competitor_stats['max_price']
    
    diff = renty_price - avg_comp
    diff_pct = (diff / avg_comp) * 100
    
    # Determine position
    if renty_price < min_comp:
        position = "Lowest (Budget Leader)"
        advantage = f"${abs(min_comp - renty_price):.0f} cheaper than cheapest competitor"
    elif renty_price <= avg_comp:
        position = "Below Average (Competitive)"
        advantage = f"{abs(diff_pct):.1f}% cheaper than market average"
    elif renty_price <= max_comp:
        position = "Above Average (Premium)"
        advantage = f"{diff_pct:.1f}% more than market average, but below max"
    else:
        position = "Highest (Ultra Premium)"
        advantage = f"{diff_pct:.1f}% above market average"
    
    return {
        'position': position,
        'price_difference': diff,
        'price_difference_pct': diff_pct,
        'competitive_advantage': advantage,
        'vs_min': renty_price - min_comp,
        'vs_max': renty_price - max_comp,
        'vs_avg': diff
    }


def generate_competitor_report(pricing_results: dict, 
                               competitor_df: pd.DataFrame,
                               city: str = "Riyadh",
                               date: datetime = None) -> pd.DataFrame:
    """
    Generate comprehensive competitor comparison report.
    
    Args:
        pricing_results: Dict of Renty pricing results by category
        competitor_df: Competitor pricing data
        city: City for comparison
        date: Date for comparison
        
    Returns:
        pd.DataFrame: Comparison report
    """
    report_data = []
    
    for category, result in pricing_results.items():
        # Get competitor stats
        comp_stats = calculate_average_competitor_price(
            competitor_df, category, city, date
        )
        
        # Compare
        comparison = compare_with_competitors(
            result['final_price'], comp_stats
        )
        
        report_data.append({
            'Category': category,
            'Renty Base Price': result['base_price'],
            'Renty Final Price': result['final_price'],
            'Renty Change %': result['price_change_pct'],
            'Competitor Avg': comp_stats['avg_price'] if comp_stats['avg_price'] else 'N/A',
            'Competitor Min': comp_stats['min_price'] if comp_stats['min_price'] else 'N/A',
            'Competitor Max': comp_stats['max_price'] if comp_stats['max_price'] else 'N/A',
            'Competitor Count': comp_stats['competitor_count'],
            'Our Position': comparison['position'],
            'Price Difference': comparison['price_difference'],
            'Difference %': comparison['price_difference_pct'],
            'Competitive Advantage': comparison['competitive_advantage']
        })
    
    return pd.DataFrame(report_data)


if __name__ == "__main__":
    # Test competitor pricing module
    logger.info("="*80)
    logger.info("COMPETITOR PRICING MODULE - TEST")
    logger.info("="*80)
    
    # Load competitor prices
    comp_df = load_competitor_prices()
    
    print("\nCompetitor Prices Summary:")
    print(comp_df.groupby('Category')['Competitor_Price'].agg(['mean', 'min', 'max']).round(2))
    
    # Test comparison
    logger.info("\n" + "="*80)
    logger.info("SAMPLE COMPARISON")
    logger.info("="*80)
    
    # Example: Renty price vs competitors
    category = "Economy"
    renty_price = 128.0
    
    comp_stats = calculate_average_competitor_price(comp_df, category)
    comparison = compare_with_competitors(renty_price, comp_stats)
    
    print(f"\nCategory: {category}")
    print(f"Renty Price: {renty_price:.2f} SAR")
    print(f"Competitor Average: {comp_stats['avg_price']:.2f} SAR")
    print(f"Position: {comparison['position']}")
    print(f"Advantage: {comparison['competitive_advantage']}")
    
    logger.info("\n✓ Competitor pricing module ready!")

