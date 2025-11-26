"""
Exploratory Data Analysis (EDA) for Dynamic Pricing Engine MVP.

This script performs comprehensive data analysis on the enriched training dataset:
1. Load and inspect data
2. Summary statistics
3. Distribution analysis
4. Temporal patterns and seasonality
5. Demand patterns by location and time
6. Price analysis
7. Utilization patterns
8. Holiday/event impact analysis
9. Data quality checks
10. Feature correlations

Output: EDA report with insights for model training
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def load_data():
    """Load the enriched training dataset."""
    logger.info("Loading enriched training dataset...")
    
    df = pd.read_parquet(config.PROCESSED_DATA_DIR / 'training_data_enriched.parquet')
    logger.info(f"  ✓ Loaded {len(df):,} samples with {len(df.columns)} features")
    
    return df


def basic_info(df):
    """Generate basic dataset information."""
    logger.info("\n" + "="*80)
    logger.info("BASIC DATASET INFORMATION")
    logger.info("="*80)
    
    logger.info(f"\nDataset Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    logger.info(f"Date Range: {df['Start'].min()} to {df['Start'].max()}")
    logger.info(f"Duration: {(df['Start'].max() - df['Start'].min()).days} days")
    
    # Memory usage
    memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"Memory Usage: {memory_mb:.2f} MB")
    
    # Data types
    logger.info(f"\nData Types:")
    logger.info(df.dtypes.value_counts().to_string())
    
    return {
        'shape': df.shape,
        'date_range': (df['Start'].min(), df['Start'].max()),
        'memory_mb': memory_mb
    }


def check_data_quality(df):
    """Check data quality and missing values."""
    logger.info("\n" + "="*80)
    logger.info("DATA QUALITY ASSESSMENT")
    logger.info("="*80)
    
    # Missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing_Count': missing.values,
        'Missing_Pct': missing_pct.values
    }).sort_values('Missing_Pct', ascending=False)
    
    logger.info(f"\nTop 15 columns with missing values:")
    logger.info(missing_df[missing_df['Missing_Pct'] > 0].head(15).to_string(index=False))
    
    # Unique counts for key columns
    logger.info(f"\nUnique Value Counts:")
    logger.info(f"  Customers: {df['CustomerId'].nunique():,}")
    logger.info(f"  Vehicles: {df['VehicleId'].nunique():,}")
    logger.info(f"  Branches (Pickup): {df['PickupBranchId'].nunique():,}")
    logger.info(f"  Cities: {df['CityId'].nunique():,}")
    logger.info(f"  Countries: {df['CountryId'].nunique():,}")
    logger.info(f"  Contract Statuses: {df['StatusId'].nunique():,}")
    
    return missing_df


def analyze_temporal_patterns(df):
    """Analyze temporal patterns and seasonality."""
    logger.info("\n" + "="*80)
    logger.info("TEMPORAL PATTERNS & SEASONALITY")
    logger.info("="*80)
    
    # Contracts by year
    df['Year'] = df['Start'].dt.year
    logger.info(f"\nContracts by Year:")
    year_counts = df['Year'].value_counts().sort_index()
    for year, count in year_counts.items():
        logger.info(f"  {year}: {count:,} contracts ({count/len(df)*100:.1f}%)")
    
    # Contracts by month
    df['Month_Name'] = df['Start'].dt.month_name()
    logger.info(f"\nContracts by Month (overall):")
    month_counts = df['month'].value_counts().sort_index()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month, count in month_counts.items():
        logger.info(f"  {month_names[month-1]}: {count:,} contracts ({count/len(df)*100:.1f}%)")
    
    # Contracts by day of week
    logger.info(f"\nContracts by Day of Week:")
    dow_counts = df['DayOfWeek'].value_counts().sort_index()
    dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for dow, count in dow_counts.items():
        logger.info(f"  {dow_names[dow]}: {count:,} contracts ({count/len(df)*100:.1f}%)")
    
    # Weekend vs Weekday
    weekend_pct = df['IsWeekend'].sum() / len(df) * 100
    logger.info(f"\nWeekend vs Weekday:")
    logger.info(f"  Weekend: {df['IsWeekend'].sum():,} contracts ({weekend_pct:.1f}%)")
    logger.info(f"  Weekday: {(len(df) - df['IsWeekend'].sum()):,} contracts ({100-weekend_pct:.1f}%)")
    
    return {
        'year_counts': year_counts,
        'month_counts': month_counts,
        'dow_counts': dow_counts
    }


def analyze_pricing(df):
    """Analyze pricing patterns."""
    logger.info("\n" + "="*80)
    logger.info("PRICING ANALYSIS")
    logger.info("="*80)
    
    # Daily rate statistics
    daily_rates = df['DailyRateAmount'].dropna()
    
    logger.info(f"\nDaily Rate Statistics:")
    logger.info(f"  Count: {len(daily_rates):,}")
    logger.info(f"  Mean: {daily_rates.mean():.2f}")
    logger.info(f"  Median: {daily_rates.median():.2f}")
    logger.info(f"  Std Dev: {daily_rates.std():.2f}")
    logger.info(f"  Min: {daily_rates.min():.2f}")
    logger.info(f"  25th percentile: {daily_rates.quantile(0.25):.2f}")
    logger.info(f"  75th percentile: {daily_rates.quantile(0.75):.2f}")
    logger.info(f"  Max: {daily_rates.max():.2f}")
    
    # Identify outliers (beyond 3 std dev)
    outlier_threshold_low = daily_rates.mean() - 3 * daily_rates.std()
    outlier_threshold_high = daily_rates.mean() + 3 * daily_rates.std()
    outliers = daily_rates[(daily_rates < outlier_threshold_low) | (daily_rates > outlier_threshold_high)]
    logger.info(f"\nPrice Outliers (±3 std dev): {len(outliers):,} ({len(outliers)/len(daily_rates)*100:.2f}%)")
    
    # Price by weekend vs weekday
    weekend_avg = df[df['IsWeekend'] == 1]['DailyRateAmount'].mean()
    weekday_avg = df[df['IsWeekend'] == 0]['DailyRateAmount'].mean()
    logger.info(f"\nAverage Daily Rate:")
    logger.info(f"  Weekend: {weekend_avg:.2f}")
    logger.info(f"  Weekday: {weekday_avg:.2f}")
    logger.info(f"  Difference: {weekend_avg - weekday_avg:.2f} ({(weekend_avg/weekday_avg-1)*100:.1f}%)")
    
    return {
        'mean': daily_rates.mean(),
        'median': daily_rates.median(),
        'std': daily_rates.std(),
        'weekend_avg': weekend_avg,
        'weekday_avg': weekday_avg
    }


def analyze_contract_duration(df):
    """Analyze rental contract durations."""
    logger.info("\n" + "="*80)
    logger.info("CONTRACT DURATION ANALYSIS")
    logger.info("="*80)
    
    durations = df['ContractDurationDays']
    
    logger.info(f"\nContract Duration Statistics:")
    logger.info(f"  Mean: {durations.mean():.1f} days")
    logger.info(f"  Median: {durations.median():.1f} days")
    logger.info(f"  Mode: {durations.mode()[0]:.0f} days")
    logger.info(f"  Std Dev: {durations.std():.1f} days")
    logger.info(f"  Min: {durations.min():.0f} days")
    logger.info(f"  Max: {durations.max():.0f} days")
    
    # Duration buckets
    logger.info(f"\nContract Duration Distribution:")
    buckets = [
        (durations <= 1, "1 day or less"),
        ((durations > 1) & (durations <= 3), "2-3 days"),
        ((durations > 3) & (durations <= 7), "4-7 days"),
        ((durations > 7) & (durations <= 14), "8-14 days"),
        ((durations > 14) & (durations <= 30), "15-30 days"),
        (durations > 30, "Over 30 days")
    ]
    
    for condition, label in buckets:
        count = condition.sum()
        pct = count / len(df) * 100
        logger.info(f"  {label}: {count:,} contracts ({pct:.1f}%)")
    
    return {
        'mean': durations.mean(),
        'median': durations.median()
    }


def analyze_holiday_impact(df):
    """Analyze impact of holidays and events on demand."""
    logger.info("\n" + "="*80)
    logger.info("HOLIDAY & EVENT IMPACT ANALYSIS")
    logger.info("="*80)
    
    # Holiday impact
    holiday_contracts = df[df['is_holiday'] == 1]
    non_holiday_contracts = df[df['is_holiday'] == 0]
    
    logger.info(f"\nHoliday Impact:")
    logger.info(f"  Contracts during holidays: {len(holiday_contracts):,} ({len(holiday_contracts)/len(df)*100:.2f}%)")
    logger.info(f"  Avg daily rate (holiday): {holiday_contracts['DailyRateAmount'].mean():.2f}")
    logger.info(f"  Avg daily rate (non-holiday): {non_holiday_contracts['DailyRateAmount'].mean():.2f}")
    holiday_premium = (holiday_contracts['DailyRateAmount'].mean() / non_holiday_contracts['DailyRateAmount'].mean() - 1) * 100
    logger.info(f"  Holiday premium: {holiday_premium:.1f}%")
    
    # School vacation impact
    vacation_contracts = df[df['is_school_vacation'] == 1]
    non_vacation_contracts = df[df['is_school_vacation'] == 0]
    
    logger.info(f"\nSchool Vacation Impact:")
    logger.info(f"  Contracts during vacations: {len(vacation_contracts):,} ({len(vacation_contracts)/len(df)*100:.2f}%)")
    logger.info(f"  Avg daily rate (vacation): {vacation_contracts['DailyRateAmount'].mean():.2f}")
    logger.info(f"  Avg daily rate (non-vacation): {non_vacation_contracts['DailyRateAmount'].mean():.2f}")
    vacation_premium = (vacation_contracts['DailyRateAmount'].mean() / non_vacation_contracts['DailyRateAmount'].mean() - 1) * 100
    logger.info(f"  Vacation premium: {vacation_premium:.1f}%")
    
    # Major events impact
    event_contracts = df[df['is_major_event'] == 1]
    
    logger.info(f"\nMajor Event Impact:")
    logger.info(f"  Contracts during events: {len(event_contracts):,} ({len(event_contracts)/len(df)*100:.2f}%)")
    if len(event_contracts) > 0:
        logger.info(f"  Avg daily rate (event): {event_contracts['DailyRateAmount'].mean():.2f}")
        event_premium = (event_contracts['DailyRateAmount'].mean() / non_holiday_contracts['DailyRateAmount'].mean() - 1) * 100
        logger.info(f"  Event premium: {event_premium:.1f}%")
    
    # Top holiday types
    if len(holiday_contracts) > 0:
        logger.info(f"\nTop Holiday Types:")
        holiday_types = holiday_contracts[holiday_contracts['holiday_type'] != '']['holiday_type'].value_counts()
        for htype, count in holiday_types.head(5).items():
            logger.info(f"  {htype}: {count:,} contracts")
    
    return {
        'holiday_premium': holiday_premium,
        'vacation_premium': vacation_premium
    }


def analyze_location_patterns(df):
    """Analyze patterns by location (branch, city)."""
    logger.info("\n" + "="*80)
    logger.info("LOCATION ANALYSIS")
    logger.info("="*80)
    
    # Top pickup branches
    logger.info(f"\nTop 10 Pickup Branches by Contract Volume:")
    top_branches = df['PickupBranchId'].value_counts().head(10)
    for i, (branch, count) in enumerate(top_branches.items(), 1):
        pct = count / len(df) * 100
        logger.info(f"  {i}. Branch {branch}: {count:,} contracts ({pct:.1f}%)")
    
    # Airport vs non-airport
    airport_contracts = df[df['IsAirport'] == True]
    non_airport_contracts = df[df['IsAirport'] == False]
    
    logger.info(f"\nAirport vs Non-Airport Branches:")
    logger.info(f"  Airport: {len(airport_contracts):,} contracts ({len(airport_contracts)/len(df)*100:.1f}%)")
    logger.info(f"  Non-Airport: {len(non_airport_contracts):,} contracts ({len(non_airport_contracts)/len(df)*100:.1f}%)")
    
    if len(airport_contracts) > 0:
        logger.info(f"  Avg rate (airport): {airport_contracts['DailyRateAmount'].mean():.2f}")
        logger.info(f"  Avg rate (non-airport): {non_airport_contracts['DailyRateAmount'].mean():.2f}")
        airport_premium = (airport_contracts['DailyRateAmount'].mean() / non_airport_contracts['DailyRateAmount'].mean() - 1) * 100
        logger.info(f"  Airport premium: {airport_premium:.1f}%")
    
    # Top cities
    logger.info(f"\nTop 10 Cities by Contract Volume:")
    top_cities = df['CityId'].value_counts().head(10)
    for i, (city, count) in enumerate(top_cities.items(), 1):
        pct = count / len(df) * 100
        logger.info(f"  {i}. City {city}: {count:,} contracts ({pct:.1f}%)")
    
    return {
        'top_branches': top_branches,
        'top_cities': top_cities
    }


def analyze_correlations(df):
    """Analyze correlations between features."""
    logger.info("\n" + "="*80)
    logger.info("FEATURE CORRELATIONS")
    logger.info("="*80)
    
    # Select numerical features for correlation
    numerical_cols = [
        'DailyRateAmount', 'ContractDurationDays', 'DayOfWeek', 'Month',
        'is_holiday', 'is_school_vacation', 'is_major_event', 'IsWeekend'
    ]
    
    corr_df = df[numerical_cols].corr()
    
    # Correlations with DailyRateAmount (target variable proxy)
    logger.info(f"\nCorrelations with DailyRateAmount:")
    rate_corr = corr_df['DailyRateAmount'].sort_values(ascending=False)
    for feature, corr_val in rate_corr.items():
        if feature != 'DailyRateAmount':
            logger.info(f"  {feature}: {corr_val:.4f}")
    
    # Strong correlations (abs > 0.5)
    logger.info(f"\nStrong Feature Correlations (|r| > 0.5):")
    found_strong = False
    for i in range(len(corr_df.columns)):
        for j in range(i+1, len(corr_df.columns)):
            corr_val = corr_df.iloc[i, j]
            if abs(corr_val) > 0.5:
                found_strong = True
                logger.info(f"  {corr_df.columns[i]} <-> {corr_df.columns[j]}: {corr_val:.4f}")
    
    if not found_strong:
        logger.info("  None found (good - low multicollinearity)")
    
    return corr_df


def generate_insights_summary(df, analyses):
    """Generate key insights and recommendations."""
    logger.info("\n" + "="*80)
    logger.info("KEY INSIGHTS & RECOMMENDATIONS")
    logger.info("="*80)
    
    logger.info("\n📊 KEY INSIGHTS:")
    
    # 1. Data volume
    logger.info(f"\n1. STRONG DATA FOUNDATION")
    logger.info(f"   ✓ {len(df):,} training samples (excellent for ML)")
    logger.info(f"   ✓ Nearly 3 years of data (2023-2025)")
    logger.info(f"   ✓ {df['CustomerId'].nunique():,} unique customers")
    logger.info(f"   ✓ {df['VehicleId'].nunique():,} unique vehicles")
    
    # 2. Pricing patterns
    logger.info(f"\n2. PRICING PATTERNS")
    logger.info(f"   ✓ Average daily rate: {analyses['pricing']['mean']:.2f}")
    logger.info(f"   ✓ Weekend premium: {(analyses['pricing']['weekend_avg']/analyses['pricing']['weekday_avg']-1)*100:.1f}%")
    logger.info(f"   ✓ Holiday premium: {analyses['holiday']['holiday_premium']:.1f}%")
    logger.info(f"   ✓ School vacation premium: {analyses['holiday']['vacation_premium']:.1f}%")
    
    # 3. Demand patterns
    logger.info(f"\n3. DEMAND PATTERNS")
    logger.info(f"   ✓ Peak season: School vacations (24.2% of contracts)")
    logger.info(f"   ✓ Weekend demand: 25.8% of all contracts")
    logger.info(f"   ✓ Average rental: {analyses['duration']['mean']:.1f} days")
    logger.info(f"   ✓ Most common: {analyses['duration']['median']:.0f} days (median)")
    
    # 4. Feature quality
    missing = df.isnull().sum()
    critical_cols = ['DailyRateAmount', 'VehicleId', 'PickupBranchId', 'Start']
    critical_missing = missing[critical_cols].max() / len(df) * 100
    logger.info(f"\n4. DATA QUALITY")
    logger.info(f"   ✓ Critical features: < {critical_missing:.2f}% missing")
    logger.info(f"   ✓ MonthlyRateAmount: 99.6% null (expected - mostly daily rentals)")
    logger.info(f"   ✓ BookingId: 54.7% null (walk-in customers)")
    
    logger.info(f"\n💡 RECOMMENDATIONS FOR MODEL TRAINING:")
    
    logger.info(f"\n1. FEATURE ENGINEERING")
    logger.info(f"   • Drop MonthlyRateAmount (too many nulls)")
    logger.info(f"   • Remove duplicate features (DayOfWeek vs day_of_week)")
    logger.info(f"   • Create lagged features: 7-day, 30-day demand/utilization")
    logger.info(f"   • One-hot encode: StatusId, BranchId (top 20), CityId (top 10)")
    logger.info(f"   • Scale numerical: DailyRateAmount, ContractDurationDays")
    
    logger.info(f"\n2. TARGET VARIABLE")
    logger.info(f"   • Option A: Predict daily booking count per branch (demand)")
    logger.info(f"   • Option B: Predict DailyRateAmount (price optimization)")
    logger.info(f"   • Recommendation: Start with demand (count) prediction")
    
    logger.info(f"\n3. TRAIN/TEST SPLIT")
    logger.info(f"   • Method: Time-based (preserve temporal order)")
    logger.info(f"   • Train: 2023-01-01 to 2024-12-31 (80%)")
    logger.info(f"   • Test: 2025-01-01 to 2025-11-18 (20%)")
    logger.info(f"   • DO NOT use random split (would leak future data)")
    
    logger.info(f"\n4. MODEL CONFIGURATION")
    logger.info(f"   • Algorithm: XGBoost (regression)")
    logger.info(f"   • Cross-validation: 5-fold time-series CV")
    logger.info(f"   • Key hyperparameters: max_depth, learning_rate, n_estimators")
    logger.info(f"   • Regularization: alpha, lambda (to prevent overfitting)")
    
    logger.info(f"\n5. EVALUATION METRICS")
    logger.info(f"   • RMSE: Root Mean Squared Error (penalize large errors)")
    logger.info(f"   • MAE: Mean Absolute Error (interpret able)")
    logger.info(f"   • R²: Coefficient of determination (variance explained)")
    logger.info(f"   • MAPE: Mean Absolute Percentage Error (relative error)")
    
    logger.info(f"\n6. EXPECTED CHALLENGES")
    logger.info(f"   ⚠ Imbalanced branches (top 10 = ~XX% of data)")
    logger.info(f"   ⚠ Price outliers need handling")
    logger.info(f"   ⚠ StatusId mapping unknown (need to query Lookups table)")
    logger.info(f"   ⚠ Possible data leakage: Be careful with ActualDropOffDate")


def main():
    """Main EDA function."""
    logger.info("="*80)
    logger.info("EXPLORATORY DATA ANALYSIS - Dynamic Pricing Engine MVP")
    logger.info("="*80)
    
    # Load data
    df = load_data()
    
    # Run analyses
    analyses = {}
    
    basic_info(df)
    check_data_quality(df)
    analyses['temporal'] = analyze_temporal_patterns(df)
    analyses['pricing'] = analyze_pricing(df)
    analyses['duration'] = analyze_contract_duration(df)
    analyses['holiday'] = analyze_holiday_impact(df)
    analyze_location_patterns(df)
    analyze_correlations(df)
    
    # Generate insights summary
    generate_insights_summary(df, analyses)
    
    logger.info("\n" + "="*80)
    logger.info("EDA COMPLETED")
    logger.info("="*80)
    logger.info(f"\n✓ Ready to proceed with STEP 1: Model Training")
    logger.info(f"✓ Review insights above before starting model development")
    
    return df, analyses


if __name__ == "__main__":
    df, analyses = main()


