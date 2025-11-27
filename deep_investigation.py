"""
DEEP INVESTIGATION: Complete System Audit
Verifies data extraction, model accuracy, feature importance, and data quality
"""

import pandas as pd
import numpy as np
import pyodbc
import pickle
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("DEEP INVESTIGATION: DYNAMIC PRICING SYSTEM AUDIT")
print("="*100)
print(f"Started at: {datetime.now()}")
print("="*100)

# ============================================================================
# PART 1: DATABASE CONNECTION & DATA VERIFICATION
# ============================================================================
print("\n[PART 1] DATABASE CONNECTION & DATA VERIFICATION")
print("-"*100)

try:
    # Connect to database
    print("\n[1.1] Connecting to database...")
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=192.168.100.4;'
        'DATABASE=RentyFM_TEST_2023;'
        'UID=sa;'
        'PWD=P@ssw0rd'
    )
    print("[OK] Database connection successful")
    
    # Check contracts table
    print("\n[1.2] Verifying Rental.Contract table...")
    query = """
    SELECT 
        COUNT(*) as total_contracts,
        MIN(Start) as earliest_date,
        MAX(Start) as latest_date,
        COUNT(DISTINCT BranchId) as unique_branches,
        COUNT(DISTINCT CategoryId) as unique_categories
    FROM Rental.Contract
    WHERE Start IS NOT NULL
    """
    df_check = pd.read_sql(query, conn)
    print(f"[OK] Total Contracts: {df_check['total_contracts'].iloc[0]:,}")
    print(f"[OK] Date Range: {df_check['earliest_date'].iloc[0]} to {df_check['latest_date'].iloc[0]}")
    print(f"[OK] Unique Branches: {df_check['unique_branches'].iloc[0]}")
    print(f"[OK] Unique Categories: {df_check['unique_categories'].iloc[0]}")
    
    # Sample actual data
    print("\n[1.3] Sampling actual contract data...")
    sample_query = """
    SELECT TOP 10
        Id, BranchId, CategoryId, Start, [End], ActualAmount, 
        DATEDIFF(day, Start, [End]) as rental_days
    FROM Rental.Contract
    WHERE Start IS NOT NULL AND [End] IS NOT NULL
    ORDER BY Start DESC
    """
    df_sample = pd.read_sql(sample_query, conn)
    print("[OK] Sample contracts:")
    print(df_sample.to_string(index=False))
    
    # Check for data quality issues
    print("\n[1.4] Checking data quality...")
    quality_query = """
    SELECT 
        COUNT(*) as total_rows,
        SUM(CASE WHEN BranchId IS NULL THEN 1 ELSE 0 END) as missing_branch,
        SUM(CASE WHEN CategoryId IS NULL THEN 1 ELSE 0 END) as missing_category,
        SUM(CASE WHEN Start IS NULL THEN 1 ELSE 0 END) as missing_start,
        SUM(CASE WHEN [End] IS NULL THEN 1 ELSE 0 END) as missing_end,
        SUM(CASE WHEN ActualAmount IS NULL OR ActualAmount = 0 THEN 1 ELSE 0 END) as missing_amount,
        SUM(CASE WHEN DATEDIFF(day, Start, [End]) < 0 THEN 1 ELSE 0 END) as negative_duration,
        SUM(CASE WHEN DATEDIFF(day, Start, [End]) > 365 THEN 1 ELSE 0 END) as suspicious_duration
    FROM Rental.Contract
    """
    df_quality = pd.read_sql(quality_query, conn)
    print(f"[CHECK] Total Rows: {df_quality['total_rows'].iloc[0]:,}")
    print(f"[CHECK] Missing Branch: {df_quality['missing_branch'].iloc[0]:,} ({df_quality['missing_branch'].iloc[0]/df_quality['total_rows'].iloc[0]*100:.2f}%)")
    print(f"[CHECK] Missing Category: {df_quality['missing_category'].iloc[0]:,} ({df_quality['missing_category'].iloc[0]/df_quality['total_rows'].iloc[0]*100:.2f}%)")
    print(f"[CHECK] Missing Start Date: {df_quality['missing_start'].iloc[0]:,}")
    print(f"[CHECK] Missing End Date: {df_quality['missing_end'].iloc[0]:,}")
    print(f"[CHECK] Missing/Zero Amount: {df_quality['missing_amount'].iloc[0]:,}")
    print(f"[CHECK] Negative Duration: {df_quality['negative_duration'].iloc[0]:,}")
    print(f"[CHECK] Suspicious Duration (>365 days): {df_quality['suspicious_duration'].iloc[0]:,}")
    
    conn.close()
    
except Exception as e:
    print(f"[ERROR] Database check failed: {str(e)}")

# ============================================================================
# PART 2: TRAINING DATA VERIFICATION
# ============================================================================
print("\n[PART 2] TRAINING DATA VERIFICATION")
print("-"*100)

try:
    print("\n[2.1] Loading training data...")
    df_train = pd.read_parquet('data/processed/training_data.parquet')
    print(f"[OK] Training data loaded: {len(df_train):,} rows, {len(df_train.columns)} columns")
    
    print("\n[2.2] Data shape and memory:")
    print(f"Rows: {len(df_train):,}")
    print(f"Columns: {len(df_train.columns)}")
    print(f"Memory usage: {df_train.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    print("\n[2.3] Key columns verification:")
    key_cols = ['start_date', 'branch_id', 'category_id', 'actual_price', 'rental_duration']
    for col in key_cols:
        if col in df_train.columns:
            print(f"[OK] {col}: {df_train[col].notna().sum():,} non-null values ({df_train[col].notna().sum()/len(df_train)*100:.1f}%)")
        else:
            print(f"[ERROR] {col}: NOT FOUND IN DATA")
    
    print("\n[2.4] Date range:")
    if 'start_date' in df_train.columns:
        print(f"Earliest: {df_train['start_date'].min()}")
        print(f"Latest: {df_train['start_date'].max()}")
        print(f"Span: {(df_train['start_date'].max() - df_train['start_date'].min()).days} days")
    
    print("\n[2.5] Price statistics:")
    if 'actual_price' in df_train.columns:
        print(f"Mean: {df_train['actual_price'].mean():.2f} SAR")
        print(f"Median: {df_train['actual_price'].median():.2f} SAR")
        print(f"Min: {df_train['actual_price'].min():.2f} SAR")
        print(f"Max: {df_train['actual_price'].max():.2f} SAR")
        print(f"Std Dev: {df_train['actual_price'].std():.2f} SAR")
    
    print("\n[2.6] Branch distribution:")
    if 'branch_id' in df_train.columns:
        branch_counts = df_train['branch_id'].value_counts().head(10)
        print(branch_counts.to_string())
    
    print("\n[2.7] Category distribution:")
    if 'category_id' in df_train.columns:
        category_counts = df_train['category_id'].value_counts()
        print(category_counts.to_string())
    
except Exception as e:
    print(f"[ERROR] Training data check failed: {str(e)}")

# ============================================================================
# PART 3: ENRICHED DATA VERIFICATION
# ============================================================================
print("\n[PART 3] ENRICHED DATA VERIFICATION")
print("-"*100)

try:
    print("\n[3.1] Loading enriched data...")
    df_enriched = pd.read_parquet('data/processed/training_data_enriched.parquet')
    print(f"[OK] Enriched data loaded: {len(df_enriched):,} rows, {len(df_enriched.columns)} columns")
    
    print("\n[3.2] External feature verification:")
    external_features = ['is_holiday', 'is_ramadan', 'is_hajj', 'is_umrah_season', 
                        'is_school_vacation', 'is_weekend']
    for feat in external_features:
        if feat in df_enriched.columns:
            true_count = df_enriched[feat].sum()
            print(f"[OK] {feat}: {true_count:,} True values ({true_count/len(df_enriched)*100:.2f}%)")
        else:
            print(f"[WARNING] {feat}: NOT FOUND")
    
    print("\n[3.3] Feature completeness:")
    missing_pct = (df_enriched.isnull().sum() / len(df_enriched) * 100).sort_values(ascending=False)
    print("Top 10 columns with missing data:")
    print(missing_pct.head(10).to_string())
    
    print("\n[3.4] Feature value ranges:")
    numeric_cols = df_enriched.select_dtypes(include=[np.number]).columns[:10]
    for col in numeric_cols:
        print(f"{col}: [{df_enriched[col].min():.2f}, {df_enriched[col].max():.2f}], mean={df_enriched[col].mean():.2f}")
    
except Exception as e:
    print(f"[ERROR] Enriched data check failed: {str(e)}")

# ============================================================================
# PART 4: MODEL VERIFICATION
# ============================================================================
print("\n[PART 4] MODEL VERIFICATION")
print("-"*100)

try:
    print("\n[4.1] Loading model...")
    with open('models/demand_prediction_model_v3_final.pkl', 'rb') as f:
        model = pickle.load(f)
    print("[OK] Model loaded successfully")
    
    print("\n[4.2] Model type and parameters:")
    print(f"Model class: {type(model).__name__}")
    print(f"Number of features: {model.n_features_in_}")
    print(f"Number of boosting rounds: {model.n_estimators}")
    
    print("\n[4.3] Feature importance (Top 20):")
    feature_importance = pd.DataFrame({
        'feature': model.feature_names_in_,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(feature_importance.head(20).to_string(index=False))
    
    print("\n[4.4] Feature importance sum check:")
    total_importance = feature_importance['importance'].sum()
    print(f"Total importance: {total_importance:.6f}")
    print(f"[CHECK] Should be close to 1.0: {'PASS' if abs(total_importance - 1.0) < 0.01 else 'FAIL'}")
    
    print("\n[4.5] Model prediction test:")
    # Create a simple test case
    test_features = pd.DataFrame([{
        feat: 0.5 for feat in model.feature_names_in_
    }])
    test_pred = model.predict(test_features)
    print(f"Test prediction: {test_pred[0]:.2f}")
    print(f"[CHECK] Prediction is reasonable: {'PASS' if test_pred[0] > 0 and test_pred[0] < 10000 else 'FAIL'}")
    
except Exception as e:
    print(f"[ERROR] Model check failed: {str(e)}")

# ============================================================================
# PART 5: MODEL PERFORMANCE VERIFICATION
# ============================================================================
print("\n[PART 5] MODEL PERFORMANCE VERIFICATION")
print("-"*100)

try:
    print("\n[5.1] Recalculating model performance on test set...")
    
    # Load enriched data
    df_full = pd.read_parquet('data/processed/training_data_enriched.parquet')
    print(f"[OK] Loaded {len(df_full):,} records")
    
    # Time-based split (same as training)
    df_full = df_full.sort_values('start_date')
    split_idx = int(len(df_full) * 0.8)
    df_train_check = df_full[:split_idx]
    df_test_check = df_full[split_idx:]
    
    print(f"[OK] Train set: {len(df_train_check):,} records")
    print(f"[OK] Test set: {len(df_test_check):,} records")
    
    # Get features
    feature_cols = [col for col in df_full.columns if col not in [
        'start_date', 'actual_price', 'branch_id', 'category_id', 'contract_id'
    ]]
    
    X_test = df_test_check[feature_cols]
    y_test = df_test_check['actual_price']
    
    print(f"\n[5.2] Making predictions on test set...")
    y_pred = model.predict(X_test)
    
    print(f"\n[5.3] Calculating metrics...")
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"R² Score: {r2:.4f} ({r2*100:.2f}%)")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    
    print(f"\n[5.4] Prediction vs Actual statistics:")
    print(f"Actual - Mean: {y_test.mean():.2f}, Std: {y_test.std():.2f}")
    print(f"Predicted - Mean: {y_pred.mean():.2f}, Std: {y_pred.std():.2f}")
    print(f"Difference in means: {abs(y_test.mean() - y_pred.mean()):.2f}")
    
    print(f"\n[5.5] Residual analysis:")
    residuals = y_test - y_pred
    print(f"Mean residual: {residuals.mean():.2f} (should be close to 0)")
    print(f"Residual std: {residuals.std():.2f}")
    print(f"Min residual: {residuals.min():.2f}")
    print(f"Max residual: {residuals.max():.2f}")
    
    print(f"\n[5.6] Prediction accuracy by range:")
    ranges = [(0, 100), (100, 200), (200, 300), (300, 500), (500, 1000), (1000, 10000)]
    for low, high in ranges:
        mask = (y_test >= low) & (y_test < high)
        if mask.sum() > 0:
            range_r2 = r2_score(y_test[mask], y_pred[mask])
            range_mae = mean_absolute_error(y_test[mask], y_pred[mask])
            print(f"{low}-{high} SAR: R²={range_r2:.4f}, MAE={range_mae:.2f}, n={mask.sum():,}")
    
except Exception as e:
    print(f"[ERROR] Performance verification failed: {str(e)}")

# ============================================================================
# PART 6: FEATURE ENGINEERING VERIFICATION
# ============================================================================
print("\n[PART 6] FEATURE ENGINEERING VERIFICATION")
print("-"*100)

try:
    print("\n[6.1] Checking temporal features...")
    temporal_features = ['day_of_week', 'month', 'day_of_month', 'week_of_year', 'season']
    for feat in temporal_features:
        if feat in df_enriched.columns:
            unique_vals = df_enriched[feat].nunique()
            print(f"[OK] {feat}: {unique_vals} unique values")
            if feat == 'day_of_week' and unique_vals != 7:
                print(f"[WARNING] Expected 7 days of week, got {unique_vals}")
            elif feat == 'month' and unique_vals != 12:
                print(f"[WARNING] Expected 12 months, got {unique_vals}")
    
    print("\n[6.2] Checking price-based features...")
    price_features = ['price_per_day', 'price_percentile_category', 'price_percentile_branch']
    for feat in price_features:
        if feat in df_enriched.columns:
            print(f"[OK] {feat}: range [{df_enriched[feat].min():.2f}, {df_enriched[feat].max():.2f}]")
    
    print("\n[6.3] Checking capacity features...")
    capacity_features = ['total_vehicles', 'category_size_ratio']
    for feat in capacity_features:
        if feat in df_enriched.columns:
            print(f"[OK] {feat}: mean={df_enriched[feat].mean():.2f}, std={df_enriched[feat].std():.2f}")
    
except Exception as e:
    print(f"[ERROR] Feature engineering check failed: {str(e)}")

# ============================================================================
# PART 7: DATA INTEGRITY CHECKS
# ============================================================================
print("\n[PART 7] DATA INTEGRITY CHECKS")
print("-"*100)

try:
    print("\n[7.1] Checking for duplicates...")
    duplicates = df_enriched.duplicated().sum()
    print(f"Duplicate rows: {duplicates:,} ({duplicates/len(df_enriched)*100:.2f}%)")
    
    print("\n[7.2] Checking for outliers in price...")
    Q1 = df_enriched['actual_price'].quantile(0.25)
    Q3 = df_enriched['actual_price'].quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((df_enriched['actual_price'] < (Q1 - 3 * IQR)) | 
                (df_enriched['actual_price'] > (Q3 + 3 * IQR))).sum()
    print(f"Price outliers (3*IQR): {outliers:,} ({outliers/len(df_enriched)*100:.2f}%)")
    print(f"Q1: {Q1:.2f}, Q3: {Q3:.2f}, IQR: {IQR:.2f}")
    
    print("\n[7.3] Checking data distribution...")
    print(f"Skewness: {df_enriched['actual_price'].skew():.2f}")
    print(f"Kurtosis: {df_enriched['actual_price'].kurtosis():.2f}")
    
except Exception as e:
    print(f"[ERROR] Data integrity check failed: {str(e)}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*100)
print("INVESTIGATION COMPLETE")
print("="*100)
print(f"Completed at: {datetime.now()}")
print("\n[SUMMARY] Key Findings:")
print("1. Database connection and data extraction - CHECK")
print("2. Training data integrity - CHECK")
print("3. Feature engineering completeness - CHECK")
print("4. Model performance metrics - CHECK")
print("5. Prediction accuracy - CHECK")
print("\n[ACTION] Review the detailed output above for any WARNING or ERROR messages")
print("="*100)


