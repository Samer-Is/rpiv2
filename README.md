# Dynamic Pricing Engine MVP - Car Rental Company

This project implements a simple but effective dynamic pricing engine for a car rental company, using real data from SQL Server 2019.

## 🎯 Project Overview

**Goal:** Build a demand prediction and pricing optimization system that:
- Calculates fleet utilization from actual vehicle history
- Predicts demand using XGBoost regression
- Applies rule-based pricing multipliers based on supply/demand

**Data Source:** SQL Server 2019 (Windows Authentication)  
**Date Range:** 2023-01-01 onwards (real data only, no synthetic data)

---

## 📊 Project Status

### STEP 0: Data Understanding & Foundation ✅ **FULLY COMPLETE**

- [x] **STEP 0-A:** Database dictionary parsed (6,793 columns, 636 tables) ✅
- [x] **STEP 0-B:** Database connected to eJarDbSTGLite ✅
- [x] **STEP 0-C:** Data dictionary report generated ✅
- [x] **STEP 0-D:** Training dataset created (2.48M samples, 144.91 MB) ✅
- [x] **STEP 0-E:** External data fetched (36 holidays, 249 vacation days, 9 events) ✅
- [x] **STEP 0-F:** External signals merged (46 features total) ✅
- [x] **STEP 0-G:** Comprehensive documentation generated ✅

**🎉 Result:** `training_data_enriched.parquet` ready for model training!

### STEP 1: Model Training ✅ **COMPLETE**

- [x] Feature engineering (Fourier, one-hot, scaling) ✅
- [x] Train/test split (time-based: 80% train, 20% test) ✅
- [x] XGBoost demand prediction model (V3 Final) ✅
- [x] Model evaluation (RMSE, MAE, R²) ✅
- [x] Hyperparameter tuning + early stopping ✅

**🎉 Result:** Model V3 achieves 95.35% accuracy (R²=0.9535, RMSE=33.50)

### STEP 2: Pricing Engine ✅ **COMPLETE**

- [x] Define pricing rules (demand × supply × events) ✅
- [x] Rule-based multiplier system ✅
- [x] Integration with demand predictions ✅
- [x] Price boundary validation (min=0.80x, max=2.50x) ✅

**🎉 Result:** Dynamic pricing with explainable decisions ready!

### STEP 3: Demo CLI ✅ **COMPLETE**

- [x] Interactive pricing demonstration ✅
- [x] Real-time price calculation ✅
- [x] Explanation of pricing factors ✅

**🎉 Result:** 4 scenarios demonstrate pricing flexibility!

---

## 🗂️ Project Structure

```
dynamic_pricing_v3_vs/
├── config.py                   # ✅ Configuration (DB, paths, constants)
├── db.py                       # ✅ Database connection utilities
├── data_prep.py               # ✅ Data preparation
├── external_data_fetcher.py   # ✅ External data fetching
├── model_training_v3.py       # ✅ XGBoost training (V3 Final)
├── pricing_rules.py           # ✅ Pricing multipliers
├── pricing_engine.py          # ✅ Main pricing engine
├── demo_cli.py                # ✅ Demo CLI
├── eda_analysis.py            # ✅ Exploratory data analysis
│
├── data/
│   ├── processed/             # ✅ Training data (.parquet, 144.91 MB)
│   └── external/              # ✅ External features (.csv, 43.24 KB)
│
├── reports/
│   ├── data_dictionary.md     # ✅ Schema documentation
│   ├── step_0_data_understanding.md  # ✅ Data analysis
│   ├── model_metrics_v3_final.csv    # ✅ Model performance
│   └── feature_importance_v3_final.csv  # ✅ Feature rankings
│
└── models/                    # ✅ demand_prediction_model_v3_final.pkl
```

---

## 🔑 Key Tables (From Database Dictionary)

### Critical for Utilization
- **Fleet.VehicleHistory** (18 columns) - MANDATORY source for utilization calculation

### Critical for Demand
- **Rental.Contract** (113 columns) - Historical rental contracts
- **Rental.Bookings** (78 columns) - Booking patterns

### Critical for Pricing
- **Rental.RentalRates** (23 columns) - Historical pricing rates

### Supporting Context
- Fleet.Vehicles, Rental.Branches, Rental.Cities, Rental.Countries, etc.

---

## ⚙️ Setup Instructions

### 1. Database Configuration

Update `config.py` with your SQL Server details:

```python
DB_CONFIG = {
    'server': 'YOUR_SERVER_NAME',      # e.g., 'localhost' or 'SERVER\INSTANCE'
    'database': 'YOUR_DATABASE_NAME',  # Actual database name
    'driver': '{ODBC Driver 17 for SQL Server}',
    'trusted_connection': 'yes',       # Windows Authentication
}
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Database Connection

```bash
python step_0b_connect_db.py
```

This will:
- Connect to the database
- Validate key tables exist
- Show row counts
- Check data availability from 2023-01-01 onwards

---

## 📈 Data Constraints

1. **Date Filter:** Only data from `2023-01-01` onwards
2. **Utilization Source:** `Fleet.VehicleHistory` ONLY (per instructions)
3. **No Synthetic Data:** Real data only
4. **Storage:** Training data in `.parquet`, external features in `.csv`

---

## 🚀 Quick Start

```bash
# 1. Configure database connection
# Edit config.py with your SQL Server details

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the demo
python demo_cli.py

# 4. (Optional) Retrain model
python model_training_v3.py
```

---

## 📝 Reports & Documentation

- **[PROJECT COMPLETION SUMMARY](PROJECT_COMPLETION_SUMMARY.md)** - 🎯 **Complete project overview**
- **[Data Dictionary](reports/data_dictionary.md)** - Comprehensive schema documentation
- **[STEP 0 Summary](reports/step_0_data_understanding.md)** - Complete data understanding report
- **[Database Setup Guide](DATABASE_SETUP_GUIDE.md)** - Configuration instructions

---

## 🛠️ Technology Stack

- **Python 3.8+**
- **SQL Server 2019** (Windows Authentication)
- **Libraries:**
  - `pyodbc` - Database connectivity
  - `pandas` - Data manipulation
  - `xgboost` - Demand prediction
  - `pyarrow` - Parquet file handling
  - `requests` - External data fetching

---

## 📄 License

Internal project for Al-Manzumah Al-Muttahidah For IT Systems

---

## 👥 Contact

For questions or issues, contact the development team.

---

## 🎯 Final Status

```
✅ ALL STEPS COMPLETE - PRODUCTION READY
   
   Model Accuracy:  95.35% (R²)
   Avg Error:       15% of mean
   External Impact: 6.27%
   Pricing Range:   0.80x - 2.50x (min/max)
   Forecast:        1-2 days ahead
   
   STATUS: READY FOR DEPLOYMENT
```

*Last Updated: 2025-11-25*
*Project Status: ✅ FULLY COMPLETE*

