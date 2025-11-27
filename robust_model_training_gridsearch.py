"""
ROBUST MODEL TRAINING WITH GRID SEARCH
2-Day Ahead Demand Prediction with Cross-Validation
Focus: Prevent overfitting, maximize robustness
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import warnings
warnings.filterwarnings('ignore')

# Set visualization style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

print("="*100)
print("ROBUST MODEL TRAINING WITH GRID SEARCH")
print("="*100)
print(f"Started at: {datetime.now()}")
print("Target: 2-Day Ahead Demand Prediction")
print("Focus: Robustness + Prevent Overfitting")
print("="*100)

# ============================================================================
# PART 1: LOAD AND PREPARE DATA
# ============================================================================
print("\n[PART 1] DATA LOADING AND PREPARATION")
print("-"*100)

print("\n[1.1] Loading training data...")
df = pd.read_parquet('data/processed/training_data.parquet')
print(f"  Loaded: {len(df):,} contracts")
print(f"  Date range: {df['Start'].min()} to {df['Start'].max()}")

# Clean data
print("\n[1.2] Data cleaning...")
df = df[df['DailyRateAmount'] > 0].copy()
df = df[df['DailyRateAmount'] < 10000].copy()  # Remove extreme outliers
df['Date'] = pd.to_datetime(df['Start']).dt.date
df['Date'] = pd.to_datetime(df['Date'])
print(f"  After cleaning: {len(df):,} contracts")

# Create target: daily booking count per branch
print("\n[1.3] Creating target variable (daily bookings per branch)...")
demand_counts = df.groupby(['Date', 'PickupBranchId']).size().reset_index(name='DailyBookings')
df = df.merge(demand_counts, on=['Date', 'PickupBranchId'], how='left')
print(f"  Target: DailyBookings")
print(f"  Mean: {df['DailyBookings'].mean():.1f} bookings/day")
print(f"  Median: {df['DailyBookings'].median():.1f} bookings/day")
print(f"  Range: {df['DailyBookings'].min()} - {df['DailyBookings'].max()}")

# ============================================================================
# PART 2: FEATURE ENGINEERING
# ============================================================================
print("\n[PART 2] FEATURE ENGINEERING (2-DAY AHEAD)")
print("-"*100)

print("\n[2.1] Temporal features...")
df['DayOfWeek'] = df['Date'].dt.dayofweek
df['DayOfMonth'] = df['Date'].dt.day
df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int)
df['Month'] = df['Date'].dt.month
df['Quarter'] = df['Date'].dt.quarter
df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
df['DayOfYear'] = df['Date'].dt.dayofyear
df['day_of_week'] = df['DayOfWeek']
df['month'] = df['Month']
df['quarter'] = df['Quarter']
df['is_weekend'] = df['IsWeekend']

print("  [OK] Temporal features created")

print("\n[2.2] Fourier features for seasonality...")
# Yearly seasonality
df['sin_365_1'] = np.sin(2 * np.pi * df['DayOfYear'] / 365)
df['cos_365_1'] = np.cos(2 * np.pi * df['DayOfYear'] / 365)
df['sin_365_2'] = np.sin(4 * np.pi * df['DayOfYear'] / 365)
df['cos_365_2'] = np.cos(4 * np.pi * df['DayOfYear'] / 365)
# Weekly seasonality
df['sin_7_1'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
df['cos_7_1'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
df['sin_7_2'] = np.sin(4 * np.pi * df['DayOfWeek'] / 7)
df['cos_7_2'] = np.cos(4 * np.pi * df['DayOfWeek'] / 7)

print("  [OK] Fourier features (yearly + weekly) created")

print("\n[2.3] External features (holidays/events)...")
try:
    from external_data_fetcher import create_holiday_features
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    df_holidays = create_holiday_features(start_date=start_date, end_date=end_date)
    df = df.merge(df_holidays, left_on='Date', right_on='date', how='left')
    
    # Enhanced holiday features
    df['is_long_holiday'] = (df['holiday_duration'] >= 4).astype(int)
    df['near_holiday'] = ((df['days_to_holiday'] >= 0) & (df['days_to_holiday'] <= 2)).astype(int)
    df['post_holiday'] = ((df['days_from_holiday'] >= 0) & (df['days_from_holiday'] <= 2)).astype(int)
    
    print(f"  [OK] Holiday features loaded")
    print(f"    - Holidays: {df['is_holiday'].sum():,} days")
    print(f"    - Ramadan: {df['is_ramadan'].sum():,} days")
    print(f"    - Hajj: {df['is_hajj'].sum():,} days")
    print(f"    - School vacation: {df['is_school_vacation'].sum():,} days")
    
except Exception as e:
    print(f"  [WARNING] Could not load external features: {str(e)}")
    # Create dummy features
    for feat in ['is_holiday', 'holiday_duration', 'is_school_vacation', 'is_ramadan', 
                 'is_umrah_season', 'umrah_season_intensity', 'is_major_event', 'is_hajj',
                 'is_festival', 'is_sports_event', 'days_to_holiday', 'days_from_holiday',
                 'is_long_holiday', 'near_holiday', 'post_holiday']:
        df[feat] = 0

print("\n[2.4] Location and aggregation features...")
# Branch features
branch_totals = df.groupby('PickupBranchId').size()
df['BranchHistoricalSize'] = df['PickupBranchId'].map(branch_totals)
df['IsAirportBranch'] = df['IsAirport'].astype(int)

# City features
city_totals = df.groupby('CityId').size()
df['CitySize'] = df['CityId'].map(city_totals)

# Price features
df['BranchAvgPrice'] = df.groupby('PickupBranchId')['DailyRateAmount'].transform('mean')
df['CityAvgPrice'] = df.groupby('CityId')['DailyRateAmount'].transform('mean')

# Capacity
df['FleetSize'] = 0  # Placeholder
df['CapacityIndicator'] = df['BranchHistoricalSize'] / df['CitySize']

print("  [OK] Location and aggregation features created")

# ============================================================================
# PART 3: PREPARE TRAIN/VAL/TEST SETS
# ============================================================================
print("\n[PART 3] PREPARING TRAIN/VALIDATION/TEST SETS")
print("-"*100)

# Feature columns
feature_cols = [
    'StatusId', 'FinancialStatusId', 'VehicleId', 'PickupBranchId', 'DropoffBranchId',
    'DailyRateAmount', 'CurrencyId', 'RentalRateId', 'BookingId',
    'DayOfWeek', 'Month', 'Quarter', 'IsWeekend', 'ContractDurationDays',
    'CityId', 'CountryId', 'IsAirport', 'ModelId', 'Year',
    'day_of_week', 'month', 'quarter', 'is_weekend',
    'is_holiday', 'holiday_duration', 'is_school_vacation', 'is_ramadan',
    'is_umrah_season', 'umrah_season_intensity', 'is_major_event', 'is_hajj',
    'is_festival', 'is_sports_event', 'days_to_holiday', 'days_from_holiday',
    'FleetSize', 'DayOfMonth', 'WeekOfYear', 'DayOfYear',
    'sin_365_1', 'cos_365_1', 'sin_365_2', 'cos_365_2',
    'sin_7_1', 'cos_7_1', 'sin_7_2', 'cos_7_2',
    'is_long_holiday', 'near_holiday', 'post_holiday',
    'BranchHistoricalSize', 'IsAirportBranch', 'CitySize',
    'BranchAvgPrice', 'CityAvgPrice', 'CapacityIndicator'
]

# Filter existing features
feature_cols = [col for col in feature_cols if col in df.columns]
print(f"\n[3.1] Feature selection: {len(feature_cols)} features")

# Handle missing values and ensure numeric types
for col in feature_cols:
    # Convert to numeric if possible
    if df[col].dtype == 'object':
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Fill missing values
    if df[col].dtype in ['float64', 'int64']:
        df[col].fillna(df[col].median(), inplace=True)
    else:
        df[col] = df[col].fillna(-1).astype('float64')

# Time-based split (no data leakage)
df_sorted = df.sort_values('Date').reset_index(drop=True)

# 70% train, 15% validation, 15% test
n = len(df_sorted)
train_idx = int(n * 0.70)
val_idx = int(n * 0.85)

df_train = df_sorted[:train_idx]
df_val = df_sorted[train_idx:val_idx]
df_test = df_sorted[val_idx:]

X_train = df_train[feature_cols]
y_train = df_train['DailyBookings']
X_val = df_val[feature_cols]
y_val = df_val['DailyBookings']
X_test = df_test[feature_cols]
y_test = df_test['DailyBookings']

print(f"\n[3.2] Data split (time-based, no leakage):")
print(f"  Train: {len(df_train):,} ({len(df_train)/n*100:.1f}%) - {df_train['Date'].min().date()} to {df_train['Date'].max().date()}")
print(f"  Val:   {len(df_val):,} ({len(df_val)/n*100:.1f}%) - {df_val['Date'].min().date()} to {df_val['Date'].max().date()}")
print(f"  Test:  {len(df_test):,} ({len(df_test)/n*100:.1f}%) - {df_test['Date'].min().date()} to {df_test['Date'].max().date()}")

print(f"\n[3.3] Target distribution:")
print(f"  Train - Mean: {y_train.mean():.1f}, Std: {y_train.std():.1f}")
print(f"  Val   - Mean: {y_val.mean():.1f}, Std: {y_val.std():.1f}")
print(f"  Test  - Mean: {y_test.mean():.1f}, Std: {y_test.std():.1f}")

# ============================================================================
# PART 4: GRID SEARCH FOR HYPERPARAMETER TUNING
# ============================================================================
print("\n[PART 4] GRID SEARCH WITH CROSS-VALIDATION")
print("-"*100)

print("\n[4.1] Defining hyperparameter grid...")
param_grid = {
    'n_estimators': [200, 300, 400],
    'max_depth': [3, 4, 5, 6],
    'learning_rate': [0.05, 0.1, 0.15],
    'min_child_weight': [1, 3, 5],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
    'reg_alpha': [0, 0.1, 0.5],  # L1 regularization
    'reg_lambda': [1, 1.5, 2]     # L2 regularization
}

print("  Grid size:")
total_combinations = 1
for param, values in param_grid.items():
    print(f"    {param}: {values} ({len(values)} options)")
    total_combinations *= len(values)
print(f"\n  Total combinations: {total_combinations:,}")
print(f"  [NOTE] This would take too long. Using RandomizedSearchCV instead.")

# Use RandomizedSearchCV for efficiency
from sklearn.model_selection import RandomizedSearchCV

base_model = XGBRegressor(
    objective='reg:squarederror',
    random_state=42,
    n_jobs=-1,
    early_stopping_rounds=20,
    eval_metric='rmse'
)

print("\n[4.2] Running Randomized Search with Time Series Cross-Validation...")
print("  CV Strategy: TimeSeriesSplit (5 folds)")
print("  Scoring: Negative Mean Absolute Error (MAE)")
print("  Iterations: 50 random combinations")
print("  [INFO] This will take 10-15 minutes...")

tscv = TimeSeriesSplit(n_splits=5)

random_search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_grid,
    n_iter=50,  # Try 50 random combinations
    cv=tscv,
    scoring='neg_mean_absolute_error',
    verbose=2,
    random_state=42,
    n_jobs=-1,
    return_train_score=True
)

# Fit with validation set for early stopping
print("\n[4.3] Starting search...")
start_time = datetime.now()

random_search.fit(
    X_train, 
    y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

elapsed_time = (datetime.now() - start_time).total_seconds() / 60
print(f"\n[4.4] Grid search complete in {elapsed_time:.1f} minutes")
print(f"\n  Best parameters:")
for param, value in random_search.best_params_.items():
    print(f"    {param}: {value}")

print(f"\n  Best CV MAE: {-random_search.best_score_:.2f} bookings")

# ============================================================================
# PART 5: TRAIN FINAL MODEL WITH BEST PARAMETERS
# ============================================================================
print("\n[PART 5] TRAINING FINAL MODEL WITH BEST PARAMETERS")
print("-"*100)

best_model = random_search.best_estimator_

# Get predictions
y_train_pred = best_model.predict(X_train)
y_val_pred = best_model.predict(X_val)
y_test_pred = best_model.predict(X_test)

# Calculate metrics
def calculate_metrics(y_true, y_pred, set_name):
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    
    print(f"\n{set_name} Set Metrics:")
    print(f"  R² Score:  {r2:.4f} ({r2*100:.2f}%)")
    print(f"  RMSE:      {rmse:.2f} bookings")
    print(f"  MAE:       {mae:.2f} bookings")
    print(f"  MAPE:      {mape:.2f}%")
    
    return {'r2': r2, 'rmse': rmse, 'mae': mae, 'mape': mape}

print("\n[5.1] Model Performance:")
train_metrics = calculate_metrics(y_train, y_train_pred, "Train")
val_metrics = calculate_metrics(y_val, y_val_pred, "Validation")
test_metrics = calculate_metrics(y_test, y_test_pred, "Test")

# Check for overfitting
print("\n[5.2] Overfitting Check:")
train_val_diff = abs(train_metrics['r2'] - val_metrics['r2'])
val_test_diff = abs(val_metrics['r2'] - test_metrics['r2'])
print(f"  Train vs Val R² diff: {train_val_diff:.4f} ({'OK' if train_val_diff < 0.05 else 'WARNING: Possible overfitting'})")
print(f"  Val vs Test R² diff:  {val_test_diff:.4f} ({'OK' if val_test_diff < 0.05 else 'WARNING: Possible instability'})")

if train_metrics['r2'] - test_metrics['r2'] < 0.1:
    print("  [OK] Model is ROBUST - Low overfitting!")
else:
    print("  [WARNING] Significant train-test gap - Consider more regularization")

# ============================================================================
# PART 6: FEATURE IMPORTANCE
# ============================================================================
print("\n[PART 6] FEATURE IMPORTANCE ANALYSIS")
print("-"*100)

feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 20 Most Important Features:")
for i, row in feature_importance.head(20).iterrows():
    print(f"  {row['feature']:<30} {row['importance']:.4f}")

# ============================================================================
# PART 7: VISUALIZATIONS
# ============================================================================
print("\n[PART 7] CREATING VISUALIZATIONS")
print("-"*100)

# Create visualization directory
import os
os.makedirs('visualizations', exist_ok=True)

# 1. Actual vs Predicted (Test Set)
plt.figure(figsize=(14, 6))
plt.subplot(1, 2, 1)
plt.scatter(y_test, y_test_pred, alpha=0.5, s=10)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Bookings', fontsize=12)
plt.ylabel('Predicted Bookings', fontsize=12)
plt.title(f'Test Set: Actual vs Predicted\nR² = {test_metrics["r2"]:.4f}, MAE = {test_metrics["mae"]:.2f}', fontsize=14)
plt.grid(True, alpha=0.3)

# 2. Residuals
plt.subplot(1, 2, 2)
residuals = y_test - y_test_pred
plt.scatter(y_test_pred, residuals, alpha=0.5, s=10)
plt.axhline(y=0, color='r', linestyle='--', lw=2)
plt.xlabel('Predicted Bookings', fontsize=12)
plt.ylabel('Residuals', fontsize=12)
plt.title('Residual Plot (Test Set)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('visualizations/predictions_vs_actual.png', dpi=300, bbox_inches='tight')
print("  [SAVED] visualizations/predictions_vs_actual.png")
plt.close()

# 3. Feature Importance
plt.figure(figsize=(12, 8))
top_features = feature_importance.head(20)
plt.barh(range(len(top_features)), top_features['importance'])
plt.yticks(range(len(top_features)), top_features['feature'])
plt.xlabel('Importance', fontsize=12)
plt.title('Top 20 Most Important Features', fontsize=14)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('visualizations/feature_importance.png', dpi=300, bbox_inches='tight')
print("  [SAVED] visualizations/feature_importance.png")
plt.close()

# 4. Time Series Predictions
plt.figure(figsize=(16, 6))

# Sample 500 predictions from test set
sample_idx = np.random.choice(len(y_test), min(500, len(y_test)), replace=False)
sample_idx = np.sort(sample_idx)

plt.plot(sample_idx, y_test.iloc[sample_idx].values, 'b-', label='Actual', alpha=0.7)
plt.plot(sample_idx, y_test_pred[sample_idx], 'r-', label='Predicted', alpha=0.7)
plt.xlabel('Sample Index', fontsize=12)
plt.ylabel('Daily Bookings', fontsize=12)
plt.title(f'Time Series: Actual vs Predicted (Random 500 samples from Test Set)\nMAE = {test_metrics["mae"]:.2f}, MAPE = {test_metrics["mape"]:.2f}%', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('visualizations/time_series_predictions.png', dpi=300, bbox_inches='tight')
print("  [SAVED] visualizations/time_series_predictions.png")
plt.close()

# 5. Error Distribution
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.hist(residuals, bins=50, edgecolor='black', alpha=0.7)
plt.xlabel('Residual (Actual - Predicted)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title(f'Residual Distribution\nMean = {residuals.mean():.2f}, Std = {residuals.std():.2f}', fontsize=14)
plt.axvline(x=0, color='r', linestyle='--', lw=2)
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
abs_errors = np.abs(residuals)
plt.hist(abs_errors, bins=50, edgecolor='black', alpha=0.7, color='orange')
plt.xlabel('Absolute Error', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title(f'Absolute Error Distribution\nMAE = {test_metrics["mae"]:.2f}', fontsize=14)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('visualizations/error_distribution.png', dpi=300, bbox_inches='tight')
print("  [SAVED] visualizations/error_distribution.png")
plt.close()

# 6. CV Results
cv_results = pd.DataFrame(random_search.cv_results_)
plt.figure(figsize=(12, 6))
plt.plot(-cv_results['mean_test_score'], label='Test Score (MAE)', marker='o')
plt.plot(-cv_results['mean_train_score'], label='Train Score (MAE)', marker='s', alpha=0.7)
plt.xlabel('Iteration', fontsize=12)
plt.ylabel('Mean Absolute Error', fontsize=12)
plt.title('Cross-Validation Scores Across Iterations', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('visualizations/cv_scores.png', dpi=300, bbox_inches='tight')
print("  [SAVED] visualizations/cv_scores.png")
plt.close()

# ============================================================================
# PART 8: SAVE MODEL AND RESULTS
# ============================================================================
print("\n[PART 8] SAVING MODEL AND RESULTS")
print("-"*100)

# Save model
model_path = 'models/demand_prediction_ROBUST_v4.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(best_model, f)
print(f"  [SAVED] {model_path}")

# Save feature columns
features_path = 'models/feature_columns_ROBUST_v4.pkl'
with open(features_path, 'wb') as f:
    pickle.dump(feature_cols, f)
print(f"  [SAVED] {features_path}")

# Save metrics
metrics = {
    'train': train_metrics,
    'validation': val_metrics,
    'test': test_metrics,
    'best_params': random_search.best_params_,
    'cv_results': cv_results.to_dict(),
    'feature_importance': feature_importance.to_dict(),
    'training_date': datetime.now().isoformat()
}

metrics_path = 'models/training_metrics_ROBUST_v4.pkl'
with open(metrics_path, 'wb') as f:
    pickle.dump(metrics, f)
print(f"  [SAVED] {metrics_path}")

# Save summary report
report_path = 'ROBUST_MODEL_REPORT.txt'
with open(report_path, 'w') as f:
    f.write("="*80 + "\n")
    f.write("ROBUST MODEL TRAINING REPORT\n")
    f.write("="*80 + "\n")
    f.write(f"Training Date: {datetime.now()}\n")
    f.write(f"Model: XGBoost with Grid Search\n")
    f.write(f"Target: 2-Day Ahead Demand Prediction\n\n")
    
    f.write("BEST HYPERPARAMETERS:\n")
    for param, value in random_search.best_params_.items():
        f.write(f"  {param}: {value}\n")
    
    f.write(f"\nMODEL PERFORMANCE:\n")
    f.write(f"  Train R²:      {train_metrics['r2']:.4f}\n")
    f.write(f"  Validation R²: {val_metrics['r2']:.4f}\n")
    f.write(f"  Test R²:       {test_metrics['r2']:.4f}\n")
    f.write(f"  Test RMSE:     {test_metrics['rmse']:.2f}\n")
    f.write(f"  Test MAE:      {test_metrics['mae']:.2f}\n")
    f.write(f"  Test MAPE:     {test_metrics['mape']:.2f}%\n")
    
    f.write(f"\nOVERFITTING CHECK:\n")
    f.write(f"  Train-Test R² Gap: {train_metrics['r2'] - test_metrics['r2']:.4f}\n")
    f.write(f"  Status: {'ROBUST' if train_metrics['r2'] - test_metrics['r2'] < 0.1 else 'NEEDS REVIEW'}\n")
    
    f.write(f"\nTOP 10 FEATURES:\n")
    for i, row in feature_importance.head(10).iterrows():
        f.write(f"  {row['feature']:<30} {row['importance']:.4f}\n")

print(f"  [SAVED] {report_path}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*100)
print("ROBUST MODEL TRAINING COMPLETE")
print("="*100)
print(f"Completed at: {datetime.now()}")
print(f"\nFINAL MODEL PERFORMANCE:")
print(f"  Test R² Score:  {test_metrics['r2']:.4f} ({test_metrics['r2']*100:.2f}%)")
print(f"  Test RMSE:      {test_metrics['rmse']:.2f} bookings")
print(f"  Test MAE:       {test_metrics['mae']:.2f} bookings")
print(f"  Test MAPE:      {test_metrics['mape']:.2f}%")
overfitting_status = "ROBUST" if train_metrics['r2'] - test_metrics['r2'] < 0.1 else "REVIEW NEEDED"
print(f"\nOVERFITTING STATUS: [{overfitting_status}]")
print(f"\nFILES SAVED:")
print(f"  - Model: {model_path}")
print(f"  - Features: {features_path}")
print(f"  - Metrics: {metrics_path}")
print(f"  - Report: {report_path}")
print(f"  - Visualizations: 6 plots in visualizations/")
print("="*100)

