"""
Check data vs model feature mismatch
"""
import pandas as pd
import pickle

print("Checking data vs model features...")

# Load data
df = pd.read_parquet('data/processed/training_data_enriched.parquet')
print(f"\nData has {len(df.columns)} columns:")
print(sorted(df.columns.tolist()))

# Load model
model = pickle.load(open('models/demand_prediction_model_v3_final.pkl', 'rb'))
print(f"\nModel expects {len(model.feature_names_in_)} features:")
print(sorted(model.feature_names_in_.tolist()))

# Find missing
data_features = set(df.columns)
model_features = set(model.feature_names_in_)
missing = model_features - data_features

print(f"\nMISSING FEATURES: {len(missing)}")
for f in sorted(missing):
    print(f"  - {f}")

print(f"\nEXTRA FEATURES IN DATA: {len(data_features - model_features)}")
for f in sorted(data_features - model_features):
    print(f"  - {f}")


