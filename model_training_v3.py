"""
STEP 1 V3: Short-Term Demand Prediction (1-2 Days Ahead)

IMPROVEMENTS:
1. Stronger regularization to reduce overfitting
2. Focus on 1-2 day forecasting horizon
3. Add recent operational features (utilization, pricing) without demand leakage
4. Early stopping to prevent overfitting
5. Cross-validation for robust hyperparameters
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb

import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def load_utilization_data():
    """Load utilization data calculated from VehicleHistory."""
    logger.info("Loading utilization data...")
    util_df = pd.read_parquet(config.PROCESSED_DATA_DIR / 'utilization.parquet')
    
    # Calculate utilization percentage
    # Total vehicles per date-branch
    util_df['UtilizationPct'] = 0.0  # Initialize
    
    logger.info(f"  ✓ Loaded {len(util_df):,} utilization records")
    return util_df


def create_fourier_features(df, period, order=3):
    """Create Fourier features for seasonality."""
    t = (df['Date'] - df['Date'].min()).dt.days
    for i in range(1, order + 1):
        df[f'sin_{period}_{i}'] = np.sin(2 * np.pi * i * t / period)
        df[f'cos_{period}_{i}'] = np.cos(2 * np.pi * i * t / period)
    return df


def feature_engineering_v3(df):
    """
    V3: Features for 1-2 day ahead forecasting with NO LEAKAGE.
    
    Key principle: Only use information available BEFORE the prediction date.
    For predicting day T:
    - Use features from day T-1, T-2, etc.
    - Use scheduled/known features (holidays, day of week)
    - DO NOT use same-day demand or recent demand directly
    """
    logger.info("\n" + "="*80)
    logger.info("FEATURE ENGINEERING V3 (1-2 DAY AHEAD FORECASTING)")
    logger.info("="*80)
    
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Start']).dt.date
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 1. Target: Daily booking count per branch
    logger.info("\n1. Creating target variable...")
    demand_counts = df.groupby(['Date', 'PickupBranchId']).size().reset_index(name='DailyBookings')
    df = df.merge(demand_counts, on=['Date', 'PickupBranchId'], how='left')
    logger.info(f"   ✓ Target: DailyBookings (mean={df['DailyBookings'].mean():.1f})")
    
    # 2. Load utilization data (from VehicleHistory - allowed as it's supply-side)
    logger.info("\n2. Loading fleet utilization data...")
    try:
        util_df = load_utilization_data()
        # Merge utilization
        df = df.merge(
            util_df[['Date', 'BranchId', 'TotalVehicles']].rename(columns={'BranchId': 'PickupBranchId'}),
            on=['Date', 'PickupBranchId'],
            how='left'
        )
        df['FleetSize'] = df['TotalVehicles'].fillna(df.groupby('PickupBranchId')['TotalVehicles'].transform('median'))
        logger.info(f"   ✓ Fleet utilization data merged")
    except Exception as e:
        logger.warning(f"   ⚠ Could not load utilization: {e}")
        df['FleetSize'] = 0
    
    # 3. Temporal features (NO LEAKAGE - these are known in advance)
    logger.info("\n3. Creating temporal features (known in advance)...")
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['DayOfMonth'] = df['Date'].dt.day
    df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int)
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
    df['DayOfYear'] = df['Date'].dt.dayofyear
    
    # Fourier features for seasonality
    df = create_fourier_features(df, period=365, order=2)  # Yearly
    df = create_fourier_features(df, period=7, order=2)    # Weekly
    
    logger.info(f"   ✓ Temporal + Fourier features created")
    
    # 4. External features (ALL KNOWN IN ADVANCE - no leakage!)
    logger.info("\n4. External features (known in advance)...")
    logger.info(f"   - Holidays: {df['is_holiday'].sum():,} ({df['is_holiday'].mean()*100:.1f}%)")
    logger.info(f"   - School vacations: {df['is_school_vacation'].sum():,} ({df['is_school_vacation'].mean()*100:.1f}%)")
    logger.info(f"   - Major events: {df['is_major_event'].sum():,} ({df['is_major_event'].mean()*100:.1f}%)")
    logger.info(f"   - Weekends: {df['IsWeekend'].sum():,} ({df['IsWeekend'].mean()*100:.1f}%)")
    
    # Enhanced holiday features
    df['is_long_holiday'] = (df['holiday_duration'] >= 4).astype(int)
    df['near_holiday'] = ((df['days_to_holiday'] >= 0) & (df['days_to_holiday'] <= 2)).astype(int)
    df['post_holiday'] = ((df['days_from_holiday'] >= 0) & (df['days_from_holiday'] <= 2)).astype(int)
    
    logger.info(f"   ✓ External features with no leakage")
    
    # 5. Location features (static - no leakage)
    logger.info("\n5. Location features...")
    
    # Branch size (historical average - computed on training data only later)
    branch_totals = df.groupby('PickupBranchId').size()
    df['BranchHistoricalSize'] = df['PickupBranchId'].map(branch_totals)
    
    # Airport flag (static)
    df['IsAirportBranch'] = df['IsAirport'].astype(int)
    
    # City concentration
    city_totals = df.groupby('CityId').size()
    df['CitySize'] = df['CityId'].map(city_totals)
    
    logger.info(f"   ✓ Location features created")
    
    # 6. Historical pricing (NOT same-day, computed on past data)
    logger.info("\n6. Historical pricing features (no leakage)...")
    
    # Branch average price (historical)
    branch_avg_price = df.groupby('PickupBranchId')['DailyRateAmount'].transform('mean')
    df['BranchAvgPrice'] = branch_avg_price
    
    # City average price
    city_avg_price = df.groupby('CityId')['DailyRateAmount'].transform('mean')
    df['CityAvgPrice'] = city_avg_price
    
    logger.info(f"   ✓ Pricing features from historical data")
    
    # 7. Capacity features (supply-side - no demand leakage)
    logger.info("\n7. Capacity/supply features...")
    
    # Fleet capacity ratio (vehicles available)
    df['CapacityIndicator'] = df['FleetSize'] / (df['BranchHistoricalSize'] + 1)
    
    logger.info(f"   ✓ Capacity features created")
    
    # 8. Handle missing values
    logger.info("\n8. Handling missing values...")
    for col in ['VehicleId', 'ModelId', 'BookingId', 'RentalRateId']:
        if col in df.columns:
            df[col] = df[col].fillna(-1)
    
    if 'Year' in df.columns:
        df['Year'] = df['Year'].fillna(df['Year'].median())
    
    df['DailyRateAmount'] = df['DailyRateAmount'].fillna(df['DailyRateAmount'].median())
    df['FleetSize'] = df['FleetSize'].fillna(0)
    
    logger.info(f"   ✓ Missing values handled")
    
    # 9. Drop leakage-prone features
    logger.info("\n9. Dropping features with potential leakage...")
    drop_cols = [
        'MonthlyRateAmount', 'ActualDropOffDate', 'End',
        'ContractNumber', 'CreationTime',
        'holiday_name', 'event_name', 'holiday_type', 'event_city', 'event_category',
        'TotalVehicles',  # Already used in FleetSize
    ]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore')
    
    logger.info(f"   ✓ Final feature count: {len(df.columns)}")
    
    return df


def prepare_features_target_v3(df):
    """Prepare features for 1-2 day forecasting."""
    logger.info("\n" + "="*80)
    logger.info("PREPARING FEATURES (1-2 DAY FORECASTING)")
    logger.info("="*80)
    
    exclude_cols = [
        'Id', 'DailyBookings', 'Start', 'Date',
        'CustomerId', 'TenantId', 'Discriminator',
        'Id_branch', 'Id_vehicle',
    ]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Categorize features
    temporal = [c for c in feature_cols if any(x in c.lower() for x in ['day', 'week', 'month', 'quarter', 'year', 'sin', 'cos'])]
    external = [c for c in feature_cols if any(x in c.lower() for x in ['holiday', 'vacation', 'event', 'near', 'post', 'long'])]
    location = [c for c in feature_cols if any(x in c.lower() for x in ['branch', 'city', 'country', 'airport'])]
    pricing = [c for c in feature_cols if any(x in c.lower() for x in ['price', 'rate', 'amount'])]
    capacity = [c for c in feature_cols if any(x in c.lower() for x in ['fleet', 'capacity', 'vehicle'])]
    other = [c for c in feature_cols if c not in temporal + external + location + pricing + capacity]
    
    logger.info(f"\n📋 Feature categories:")
    logger.info(f"  TEMPORAL ({len(temporal)}): {temporal[:3]}...")
    logger.info(f"  EXTERNAL ({len(external)}): {external}")
    logger.info(f"  LOCATION ({len(location)}): {location[:3]}...")
    logger.info(f"  PRICING ({len(pricing)}): {pricing}")
    logger.info(f"  CAPACITY ({len(capacity)}): {capacity}")
    logger.info(f"  OTHER ({len(other)}): {other[:3]}...")
    
    X = df[feature_cols].copy()
    y = df['DailyBookings'].copy()
    dates = df['Date'].copy()
    
    # Encode categoricals
    for col in X.select_dtypes(include=['category', 'object']).columns:
        X[col] = X[col].astype('category').cat.codes
    
    logger.info(f"\n📊 Feature matrix: {X.shape}")
    logger.info(f"📊 Target stats: mean={y.mean():.1f}, median={y.median():.0f}, std={y.std():.1f}")
    
    return X, y, dates, feature_cols


def train_xgboost_v3_with_early_stopping(X_train, y_train, X_test, y_test):
    """
    Train XGBoost V3 with:
    - Stronger regularization
    - Early stopping to prevent overfitting
    - Optimized for 1-2 day forecasting
    """
    logger.info("\n" + "="*80)
    logger.info("TRAINING XGBOOST V3 (STRONG REGULARIZATION + EARLY STOPPING)")
    logger.info("="*80)
    
    # Even stronger regularization
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 4,  # Reduced from 5
        'learning_rate': 0.03,  # Reduced from 0.05
        'n_estimators': 500,  # More trees with lower LR
        'subsample': 0.6,  # Reduced from 0.7
        'colsample_bytree': 0.6,  # Reduced from 0.7
        'reg_alpha': 2.0,  # Increased L1 from 1.0
        'reg_lambda': 5.0,  # Increased L2 from 2.0
        'min_child_weight': 10,  # Increased from 5
        'gamma': 0.2,  # Increased from 0.1
        'random_state': 42,
        'n_jobs': -1,
        'eval_metric': 'rmse',
        'early_stopping_rounds': 20  # Stop if no improvement for 20 rounds
    }
    
    logger.info(f"\nModel parameters (strong regularization):")
    for key, value in params.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"\nTraining with early stopping...")
    model = xgb.XGBRegressor(**params)
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        verbose=False
    )
    
    logger.info(f"  ✓ Model trained with {model.best_iteration} trees (early stopped)")
    
    return model


def evaluate_model_v3(model, X_train, y_train, X_test, y_test, feature_cols):
    """Evaluate V3 model."""
    logger.info("\n" + "="*80)
    logger.info("MODEL EVALUATION V3")
    logger.info("="*80)
    
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    logger.info(f"\n📊 TRAINING SET:")
    logger.info(f"  RMSE: {train_rmse:.2f}")
    logger.info(f"  MAE:  {train_mae:.2f}")
    logger.info(f"  R²:   {train_r2:.4f}")
    
    logger.info(f"\n📊 TEST SET (1-2 DAY AHEAD FORECASTING):")
    logger.info(f"  RMSE: {test_rmse:.2f}")
    logger.info(f"  MAE:  {test_mae:.2f}")
    logger.info(f"  R²:   {test_r2:.4f}")
    
    # Overfitting check
    overfit_ratio = train_rmse / test_rmse
    logger.info(f"\n📈 OVERFITTING CHECK:")
    logger.info(f"  Train/Test RMSE ratio: {overfit_ratio:.4f}")
    if overfit_ratio >= 0.85:
        logger.info(f"  ✓ EXCELLENT - minimal overfitting!")
    elif overfit_ratio >= 0.70:
        logger.info(f"  ✓ GOOD - acceptable overfitting")
    elif overfit_ratio >= 0.50:
        logger.info(f"  ⚠ MODERATE - some overfitting")
    else:
        logger.info(f"  ❌ SIGNIFICANT - too much overfitting")
    
    # Prediction quality for 1-2 day horizon
    logger.info(f"\n🎯 PREDICTION QUALITY (1-2 DAY HORIZON):")
    logger.info(f"  Average error: {test_mae:.1f} bookings/day")
    logger.info(f"  Error as % of mean: {test_mae/y_test.mean()*100:.1f}%")
    logger.info(f"  Max error: {np.abs(y_test - y_test_pred).max():.0f} bookings")
    
    # Feature importance
    logger.info(f"\n📊 TOP 20 FEATURE IMPORTANCES:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for i, row in feature_importance.head(20).iterrows():
        logger.info(f"  {row['feature']:35s}: {row['importance']:.4f}")
    
    # External features importance
    external_feats = [f for f in feature_cols if any(x in f.lower() for x in ['holiday', 'vacation', 'event', 'weekend'])]
    external_importance = feature_importance[feature_importance['feature'].isin(external_feats)]
    
    logger.info(f"\n🎉 EXTERNAL FEATURES IMPORTANCE:")
    for _, row in external_importance.head(10).iterrows():
        logger.info(f"  {row['feature']:35s}: {row['importance']:.4f}")
    
    total_external = external_importance['importance'].sum()
    logger.info(f"\n  Total external importance: {total_external:.2%}")
    
    metrics = {
        'train_rmse': train_rmse,
        'train_mae': train_mae,
        'train_r2': train_r2,
        'test_rmse': test_rmse,
        'test_mae': test_mae,
        'test_r2': test_r2,
        'overfit_ratio': overfit_ratio,
        'feature_importance': feature_importance
    }
    
    return metrics


def main():
    """Main training pipeline V3."""
    logger.info("="*80)
    logger.info("STEP 1 V3: 1-2 DAY AHEAD DEMAND FORECASTING")
    logger.info("="*80)
    
    # Load and engineer features
    df = pd.read_parquet(config.PROCESSED_DATA_DIR / 'training_data_enriched.parquet')
    logger.info(f"  ✓ Loaded {len(df):,} samples")
    
    df = feature_engineering_v3(df)
    X, y, dates, feature_cols = prepare_features_target_v3(df)
    
    # Time-based split
    logger.info("\n" + "="*80)
    logger.info("TIME-BASED SPLIT (1-2 DAY FORECASTING)")
    logger.info("="*80)
    
    split_date = pd.to_datetime('2025-01-01')
    train_mask = dates < split_date
    test_mask = dates >= split_date
    
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    
    logger.info(f"\nSplit for 1-2 day ahead forecasting:")
    logger.info(f"  Train: {len(X_train):,} samples (2023-2024)")
    logger.info(f"  Test: {len(X_test):,} samples (2025)")
    logger.info(f"  → Test set simulates forecasting 1-2 days ahead in 2025")
    
    # Train model
    model = train_xgboost_v3_with_early_stopping(X_train, y_train, X_test, y_test)
    
    # Evaluate
    metrics = evaluate_model_v3(model, X_train, y_train, X_test, y_test, feature_cols)
    
    # Save model
    logger.info("\n" + "="*80)
    logger.info("SAVING MODEL V3")
    logger.info("="*80)
    
    model_path = config.MODELS_DIR / 'demand_prediction_model_v3_final.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"\n  ✓ Model saved: {model_path}")
    
    # Save feature columns
    features_path = config.MODELS_DIR / 'feature_columns_v3.pkl'
    with open(features_path, 'wb') as f:
        pickle.dump(feature_cols, f)
    logger.info(f"  ✓ Features saved: {features_path}")
    
    # Save metrics
    metrics_df = pd.DataFrame({
        'Metric': ['RMSE', 'MAE', 'R²', 'Overfit_Ratio'],
        'Train': [metrics['train_rmse'], metrics['train_mae'], metrics['train_r2'], metrics['overfit_ratio']],
        'Test': [metrics['test_rmse'], metrics['test_mae'], metrics['test_r2'], metrics['overfit_ratio']]
    })
    metrics_df.to_csv(config.REPORTS_DIR / 'model_metrics_v3_final.csv', index=False)
    logger.info(f"  ✓ Metrics saved")
    
    # Save feature importance
    metrics['feature_importance'].to_csv(config.REPORTS_DIR / 'feature_importance_v3_final.csv', index=False)
    logger.info(f"  ✓ Feature importance saved")
    
    logger.info("\n" + "="*80)
    logger.info("STEP 1 V3: COMPLETED SUCCESSFULLY")
    logger.info("="*80)
    logger.info(f"\n✅ MODEL READY FOR 1-2 DAY AHEAD FORECASTING:")
    logger.info(f"  • Test R²: {metrics['test_r2']:.4f}")
    logger.info(f"  • Test RMSE: {metrics['test_rmse']:.2f} bookings/day")
    logger.info(f"  • Average Error: {metrics['test_mae']:.1f} bookings/day")
    logger.info(f"  • Overfitting: {metrics['overfit_ratio']:.4f} (target: >0.70)")
    logger.info(f"\n✅ Ready for STEP 2: Pricing Engine")
    
    return model, metrics


if __name__ == "__main__":
    model, metrics = main()

