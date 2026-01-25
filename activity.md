# Activity Log

This file logs all successful commits to the repository.

---

## 2026-01-25

### Commit: CHUNK 7 - Multi-Model Forecasting Trainer
- **Hash:** f2b3977
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**Database Tables Created:**
- `dynamicpricing.forecast_demand_30d` - 30-day horizon forecasts
- `dynamicpricing.model_evaluation_metrics` - backtesting results
- `dynamicpricing.best_model_selection` - model tracking

**Models Implemented:**
1. **SeasonalNaiveModel** - 7-day seasonal baseline
2. **SimpleETSModel** - Holt-Winters exponential smoothing
3. **LightGBMGlobalModel** - Global ML model with entity embeddings (requires lightgbm)
4. **LSTMGlobalModel** - PyTorch LSTM with CUDA GPU support (requires torch)

**ForecastTrainingService Pipeline:**
- `load_training_data()` - Load from feature store
- `train_all_models()` - Train with timing metrics
- `backtest_models()` - Rolling-origin cross-validation
- `select_best_model()` - Selection based on MAE
- `generate_forecasts()` - 30-day horizon generation
- `save_forecasts()` / `save_metrics()` - Database persistence

**API Endpoints:**
- `POST /forecast/train` - Trigger full training pipeline
- `GET /forecast/forecasts` - Get 30-day forecasts by branch/category
- `GET /forecast/metrics` - Model evaluation metrics
- `GET /forecast/best-model` - Current best model info
- `GET /forecast/summary` - Forecast statistics

**Training Results:**
- Training samples: 17,964
- Validation samples: 11,047
- Models trained: seasonal_naive, simple_ets
- Best model: seasonal_naive
- MAE: 92.27 | MAPE: 12.37%
- Forecasts generated: 1,080 records

**Validation Checks (All Passed):**
- ✅ At least 2 models trained: 2
- ✅ Best model selected: seasonal_naive
- ✅ Best MAE reasonable vs baseline
- ✅ Forecasts not flatline: std=38.22
- ✅ Correct horizon: 30 days

**Files Created:**
- `backend/app/ml/__init__.py` - ML module
- `backend/app/ml/models.py` - Forecasting model classes
- `backend/app/ml/trainer.py` - Training service
- `backend/app/routers/forecast.py` - API endpoints
- `scripts/create_forecast_tables.sql` - DDL
- `scripts/run_forecast_training.py` - Training script

---

## 2026-01-22

### Commit: CHUNK 6 - Feature Store Builder
- **Hash:** a194f96
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**Feature Store Table Created:**
- `dynamicpricing.fact_daily_demand` - ML training/inference data
- Grain: tenant_id × demand_date × branch_id × category_id
- 29,011 total rows populated

**TRAIN/VALIDATION Split:**
- TRAIN: 17,964 rows (before Oct 2024)
- VALIDATION: 11,047 rows (Oct 2024 onwards)
- Split cutoff: 2024-10-01

**Features Included:**
- Target: `executed_rentals_count`
- Pricing: avg/min/max_base_price_paid
- Utilization: utilization_contracts, utilization_bookings
- Weather: temperature_max/min/avg, precipitation_mm, wind_speed_kmh
- Calendar: is_weekend, is_public_holiday, is_religious_holiday
- Time: day_of_week, day_of_month, week_of_year, month_of_year, quarter
- Events: event_score, has_major_event
- Lag features: rentals_lag_1d, rentals_lag_7d, rentals_rolling_7d_avg, rentals_rolling_30d_avg

**FeatureStoreService Methods:**
- `build_feature_store()` - Full rebuild with all features
- `validate_feature_store()` - Quality validation checks
- `get_training_data()` - Get ML-ready data by split
- `_insert_base_demand()` - Aggregate contract data
- `_update_weather_features()` - Join weather data
- `_update_calendar_features()` - Join holiday data
- `_update_event_features()` - Join GDELT event data
- `_compute_lag_features()` - Compute time-series lag features
- `_apply_split()` - Apply TRAIN/VALIDATION split

**API Endpoints:**
- `POST /feature-store/build` - Build/rebuild feature store
- `GET /feature-store/validate` - Validate feature store quality
- `GET /feature-store/training-data` - Get training data for ML
- `GET /feature-store/stats` - Get feature store statistics
- `DELETE /feature-store/clear` - Clear feature store data

**Validation Results:**
- ✅ minimum_rows: 29,011 (threshold: 1,000)
- ✅ target_variance: 40.88 (threshold: 0.1)
- ✅ split_exists: TRAIN=17,964, VALIDATION=11,047
- ✅ missing_rate: price=0.0%, lag=6.4% (threshold: 50%)

**Target Variable Statistics:**
- Mean: 25.32 rentals/day
- Min: 1, Max: 345
- Std: 40.88

**Coverage:**
- 6 MVP branches
- 6 MVP categories
- Date range: 2023-01-01 to 2025-11-17

**Files Created:**
- `backend/app/services/feature_store_service.py` - Core service
- `backend/app/routers/feature_store.py` - API endpoints
- `backend/app/schemas/feature_store.py` - Pydantic schemas
- `scripts/create_fact_daily_demand.sql` - Table DDL
- `scripts/populate_feature_store.py` - Data population script
- `scripts/explore_feature_store.py` - Data exploration
- `scripts/check_columns.py` - Column discovery utility

---

### Commit: CHUNK 5 - External Signals
- **Hash:** 0ae9052
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**Weather Service (Open-Meteo):**
- `WeatherService` class with fetch_historical_weather() and fetch_forecast_weather()
- Automatic bad_weather_score calculation (0-1 scale based on rain/wind/conditions)
- extreme_heat_flag (1 if t_max > 43°C, common in KSA summers)
- Data stored in `dynamicpricing.weather_data` table

**Weather Features:**
- t_mean, t_max, t_min (temperature in Celsius)
- wind_max (km/h), precipitation_sum (mm)
- weather_code (WMO standard), bad_weather_score, extreme_heat_flag

**KSA Calendar Pipeline:**
Complete Python package `ksa_calendar_pipeline/`:
- `holidays_calendarific.py` - Fetches KSA holidays from Calendarific API
- `events_gdelt.py` - Fetches event intensity from GDELT 2.1 DOC API
- `feature_builder.py` - Builds ML-ready features from raw data
- `backfill.py` - Historical data population
- `run_daily.py` - Daily update runner
- `db.py` - Database operations

**Calendar Features:**
- is_holiday, holiday_name, holiday_type
- is_weekend (Friday-Saturday in KSA)
- event_score_today, event_score_3d_avg, event_score_7d_avg (GDELT)

**Database Tables Created:**
- `dynamicpricing.weather_data` - Weather data by branch/date
- `dynamicpricing.ksa_holidays` - Saudi Arabia holidays
- `dynamicpricing.ksa_daily_event_signal` - GDELT event intensity by city/date

**API Endpoints:**
- `GET /signals/weather/summary` - Weather data statistics
- `GET /signals/weather/locations` - Branch coordinates
- `GET /signals/weather/branch/{id}` - Weather by branch
- `POST /signals/weather/fetch-forecast` - Trigger forecast fetch
- `GET /signals/calendar/features` - Calendar/event features
- `GET /signals/holidays/summary` - Holiday statistics
- `GET /signals/events/summary` - Event statistics
- `GET /signals/external-signals/combined` - All signals for branch/date

**Validation Results:**
- Weather table: 96 rows, 6 branches, 16 days forecast ✅
- Holiday table: 10 holidays, 2023-2027 ✅
- Event table: 35 records, 5 cities ✅
- Feature builder outputs: All required fields ✅
- Weather service methods: Working correctly ✅
- API endpoints: Accessible ✅

**Files Created:**
- `backend/app/services/weather_service.py` - Weather service
- `backend/app/routers/signals.py` - API endpoints
- `backend/app/schemas/weather.py` - Pydantic schemas
- `ksa_calendar_pipeline/` - Complete pipeline package
- `scripts/test_chunk5_validation.py` - Validation tests

---

### Commit: CHUNK 4 - Utilization Engine
- **Hash:** 525e1e4
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**UtilizationService Created:**
- `get_all_utilizations()` - Returns utilization for all MVP branch × category combinations
- `get_utilization_for_branch_category()` - Single branch/category lookup
- `get_fleet_snapshot()` - Detailed status breakdown by vehicle
- `get_status_config_summary()` - Lists all status types and vehicle counts
- Configurable status mappings from `appconfig.utilization_status_config`

**Formula:** `Utilization = Rented / (Rented + Available)`

**Status Configuration:**
- 140 = Ready (AVAILABLE) - Available for rent
- 141 = Rented (RENTED) - Currently on rental
- 156 = In-Use (RENTED) - Currently in use
- 143 = Sold (EXCLUDED) - Sold, not in active fleet
- Other statuses excluded from utilization calculation

**API Endpoints:**
- `GET /utilization/` - Get all utilizations
- `GET /utilization/branch/{id}/category/{id}` - Specific branch/category
- `GET /utilization/snapshot` - Fleet status detail
- `GET /utilization/config` - Status configuration
- `GET /utilization/summary` - Branch/category summary

**Validation Results:**
- 36 branch × category combinations tested
- Utilization range [0, 1]: ✅ PASSED
- Utilization variance across categories: ✅ PASSED (29 unique values)
- Service vs SQL consistency: ✅ PASSED
- API endpoints accessible: ✅ PASSED

**Sample Data:**
- Utilization ranges from 0% to 100%
- Example: Branch 122 × Category 27 (Compact): 76.3% utilization
- Total active fleet: 2,264 rented + 682 available = 2,946 vehicles

**Files Created:**
- `backend/app/services/utilization_service.py` - Utilization calculation service
- `backend/app/routers/utilization.py` - API endpoints
- `backend/app/schemas/utilization.py` - Pydantic schemas
- `scripts/test_chunk4_validation.py` - Validation tests
- `scripts/explore_utilization*.py` - Data exploration scripts

---

### Commit: CHUNK 3 - Base Price Engine
- **Hash:** f43a938
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**BaseRateService Created:**
- `get_base_prices_for_category()` - Aggregated prices for branch × category
- `get_model_prices()` - Individual model prices
- `get_mvp_category_prices()` - MVP categories only
- Supports effective date filtering (Start/End period logic)
- Falls back to default rates when no branch-specific rates exist

**API Endpoints:**
- `GET /prices/base` - Get base price for branch × category
- `POST /prices/base` - Same as GET with JSON body
- `GET /prices/models` - Get prices for all models in a category
- `GET /prices/categories` - Get prices for all categories
- `GET /prices/mvp-categories` - Get prices for MVP categories
- `GET /prices/summary` - Quick validation summary

**Data Structure Discovered:**
- RentalRates → RentalRatesSchemaPeriods → RentalRatesSchemaPeriodsDetails
- Period types: Daily (1-6 days), Weekly (7-27 days), Monthly (28+ days)
- MVP branches use default rates (BranchId IS NULL)

**Validation Results:**
- 5/5 branch × category tests passed
- Effective period logic validated for 4 test dates
- All 6 MVP categories have prices
- 94 models across MVP categories

**Files Created:**
- `backend/app/services/base_rate_service.py` - Base rate service
- `backend/app/routers/prices.py` - Price API endpoints
- `backend/app/schemas/base_price.py` - Pydantic schemas
- `scripts/test_chunk3_validation.py` - Validation tests
- `scripts/explore_base_prices*.py` - Data exploration scripts

---

### Commit: CHUNK 2 - App DB + Config Tables
- **Hash:** 1162e7a
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**appconfig Schema Created (9 tables):**
- `appconfig.tenants` - Multi-tenant support
- `appconfig.tenant_settings` - Key-value settings
- `appconfig.guardrails` - Price min/max limits
- `appconfig.signal_weights` - Algorithm weights
- `appconfig.utilization_status_config` - Vehicle status mappings
- `appconfig.branch_city_mapping` - Weather API coordinates
- `appconfig.competitor_mapping` - Competitor price mapping
- `appconfig.selection_config` - MVP branches/categories
- `appconfig.audit_log` - Change tracking

**YELO Configuration Inserted:**
- Tenant ID: 1
- Default guardrails: min_price=50 SAR, max_discount=30%, max_premium=50%
- 6 signal weights configured
- 6 MVP branches with lat/lon coordinates
- 6 MVP categories

**Files Created/Modified:**
- `scripts/create_appconfig_schema.py` - Schema creation script
- `scripts/test_chunk2_validation.py` - Validation tests
- `backend/app/models/appconfig.py` - SQLAlchemy models
- `backend/app/schemas/config.py` - Pydantic schemas
- `backend/app/routers/config.py` - Config API endpoints
- `backend/app/routers/health.py` - DB health check
- `backend/app/main.py` - Router includes

---

### Commit: CHUNK 1 - SQL Server Data Discovery
- **Hash:** 9928287
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**Key Discoveries:**
- YELO tenant_id = 1 (Name: 'Yelo', TenancyName: 'Default')
- Total individual rentals (2022+): 2,826,983
- Data range: 2022-01-01 to 2025-11-18
- DailyRateAmount: 100% complete, avg 234 SAR
- Filter: `Discriminator='Contract' AND StatusId=211`
- Pre-existing dynamicpricing schema found with:
  - TopBranches (6 MVP branches)
  - TopCategories (6 MVP categories)
  - TrainingData (36,308 rows)
  - ValidationData (4,749 rows)

**Files Created/Modified:**
- `scripts/data_discovery.py` - Main discovery script
- `scripts/data_discovery_part2.py` - MVP scope queries
- `scripts/data_discovery_part3.py` - Final details
- `docs/data_discovery_report.md` - Comprehensive findings
- `backend/app/core/config.py` - Windows Auth config
- `backend/app/db/session.py` - Updated connection handling
- `docs/validation_checklist.md` - Updated with discoveries

---

### Commit: CHUNK 0 - Project Scaffold
- **Hash:** a499d75
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2

**Files Created:**
- `backend/` - FastAPI Python backend
  - `app/main.py` - Main FastAPI application
  - `app/core/config.py` - Configuration from env vars
  - `app/core/security.py` - JWT authentication
  - `app/db/session.py` - SQL Server connection management
  - `app/routers/health.py` - Health check endpoint
  - `app/routers/auth.py` - Login endpoint
  - `app/schemas/auth.py` - Auth request/response models
  - `requirements.txt` - Python dependencies
  - `Dockerfile` - Backend container config
  - `.env.example` - Environment template

- `frontend/` - React + TypeScript frontend
  - `src/main.tsx` - React entry point
  - `src/App.tsx` - Router setup
  - `src/pages/LoginPage.tsx` - Login form
  - `src/pages/DashboardPage.tsx` - Main dashboard skeleton
  - `src/api/client.ts` - Axios API client
  - `src/api/auth-store.ts` - Zustand auth state
  - `src/styles/globals.css` - Tailwind styles
  - `package.json` - Node dependencies
  - `Dockerfile` - Frontend container config
  - `nginx.conf` - Production nginx config

- `docs/` - Documentation
  - `requirements.md` - Functional/non-functional requirements
  - `architecture.md` - System architecture diagrams
  - `validation_checklist.md` - Chunk validation checklist
  - `decisions_log.md` - Architecture decisions record

- Root files
  - `docker-compose.yml` - Multi-container setup
  - `README.md` - Project documentation
  - `.gitignore` - Git ignore rules
  - `.env.example` - Root environment template

**Validation Status:** PENDING (need to test backend health + frontend login)

---
