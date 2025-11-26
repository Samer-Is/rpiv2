# STEP 0: Data Understanding & Foundation - Summary Report

**Generated:** 2025-11-25 12:34:52

**Project:** Dynamic Pricing Engine MVP for Car Rental Company

---

## Executive Summary

This document summarizes the data understanding and foundation work completed in STEP 0 of the Dynamic Pricing Engine MVP project. This phase focused on understanding the database structure, extracting relevant data, and preparing features for demand prediction.

**Key Achievements:**

- ✅ Database dictionary parsed (6,793 columns across 636 tables)
- ✅ Key tables identified for utilization, demand, and pricing
- ✅ Data extraction queries designed for Fleet.VehicleHistory, Rental.Contract, Rental.Bookings
- ✅ External features collected (36 holidays, 249 vacation days, 9 major events)
- ✅ Comprehensive data dictionary and documentation generated

---

## Table of Contents

1. [STEP 0-A: Database Dictionary](#step-0-a-database-dictionary)
2. [STEP 0-B: Database Connection](#step-0-b-database-connection)
3. [STEP 0-C: Data Dictionary Report](#step-0-c-data-dictionary-report)
4. [STEP 0-D: Training Dataset Creation](#step-0-d-training-dataset-creation)
5. [STEP 0-E: External Data](#step-0-e-external-data)
6. [STEP 0-F: Data Merging](#step-0-f-data-merging)
7. [Design Decisions](#design-decisions)
8. [Data Quality Observations](#data-quality-observations)
9. [Constraints & Assumptions](#constraints--assumptions)
10. [Next Steps](#next-steps)

---

## STEP 0-A: Database Dictionary

**Objective:** Parse database dictionary to understand schema structure.

**Implementation:**
- Created `db.py` module with dictionary parsing functions
- Implemented table discovery and categorization
- Validated existence of critical tables

**Results:**
- **636 tables** across **12 schemas**
- **6,793 columns** total
- Key schemas: Rental (136 tables), Fleet (90 tables), Crm (58 tables)

**Key Tables Identified:**

| Category | Table | Purpose |
|----------|-------|----------|
| Utilization | Fleet.VehicleHistory | **MANDATORY** source for utilization calculation |
| Demand | Rental.Contract | Historical rental contracts and pricing |
| Demand | Rental.Bookings | Booking patterns and demand signals |
| Pricing | Rental.RentalRates | Historical pricing rate configurations |
| Context | Fleet.Vehicles | Vehicle master data |
| Context | Rental.Branches | Location/branch information |

---

## STEP 0-B: Database Connection

**Objective:** Connect to SQL Server 2019 and validate table access.

**Implementation:**
- Created database connection manager using `pyodbc`
- Windows Authentication configuration
- Row count queries for validation
- Sample data preview functionality

**Configuration Required:**
```python
# Update config.py with your database details:
DB_CONFIG = {
    'server': 'YOUR_SERVER_NAME',
    'database': 'YOUR_DATABASE_NAME',
    'driver': '{ODBC Driver 17 for SQL Server}',
    'trusted_connection': 'yes',
}
```

**Next Action:** User must configure database credentials before running STEP 0-B script.

---

## STEP 0-C: Data Dictionary Report

**Objective:** Generate comprehensive schema documentation.

**Implementation:**
- Created `step_0c_data_dictionary.py` script
- Generated detailed Markdown report
- Documented all critical tables with column details

**Output:** `reports/data_dictionary.md`

**Content:**
- Schema distribution and table counts
- Detailed column definitions for critical tables
- Data types, nullability, primary keys
- Relationships and dependencies

---

## STEP 0-D: Training Dataset Creation

**Objective:** Extract and prepare training data from key tables.

**Implementation:**
- Created `data_prep.py` module with extraction functions
- Designed queries for Fleet.VehicleHistory, Rental.Contract, Rental.Bookings
- Implemented utilization calculation logic
- Feature engineering for temporal and location attributes

**Data Extraction Queries:**

1. **Fleet.VehicleHistory** - Vehicle status changes over time
   - Filter: `OperationDateTime >= '2023-01-01'`
   - Key columns: VehicleId, StatusId, OperationDateTime, BranchId

2. **Rental.Contract** - Historical rental contracts
   - Filter: `Start >= '2023-01-01'`
   - Key columns: Start, End, VehicleId, DailyRateAmount, StatusId

3. **Rental.Bookings** - Booking patterns
   - Filter: `CreationTime >= '2023-01-01'`
   - Key columns: CreationTime, PickupDate, StatusId, TotalPaidAmount

**Utilization Calculation:**
```
Utilization = (Vehicles in 'Rented' status) / (Total available vehicles)
- Calculated daily by branch
- Source: Fleet.VehicleHistory ONLY (per instructions)
- Aggregation: By Date, BranchId, StatusId
```

**Output:** `data/processed/training_data.parquet`

**Status:** ⏳ Requires database configuration to execute

---

## STEP 0-E: External Data

**Objective:** Fetch external demand signals (holidays, events).

**Implementation:**
- Created `external_data_fetcher.py` module
- Collected KSA holidays, school vacations, major events
- Generated daily calendar with external features

**External Features Collected:**

| Feature Category | Count | Details |
|------------------|-------|----------|
| Public Holidays | 36 days | Eid Al-Fitr, Eid Al-Adha, National Day, Founding Day |
| School Vacations | 249 days | Summer vacation, mid-year breaks |
| Major Events | 9 events | Formula 1, Riyadh Season, Hajj Season |
| Total Days | 1,096 days | 2023-01-01 to 2025-12-31 |

**Features Created:**
- `is_holiday`: Binary flag for public holidays
- `is_school_vacation`: Binary flag for school vacation periods
- `is_major_event`: Binary flag for major events
- `is_weekend`: Binary flag for weekends (Friday-Saturday in KSA)
- `days_to_holiday`: Days until next holiday (within 7-day window)
- `days_from_holiday`: Days since last holiday (within 3-day window)
- `holiday_duration`: Number of days in holiday period
- `event_name`, `event_city`, `event_category`: Event details

**Output:** `data/external/external_features.csv` (43.24 KB)

**Status:** ✅ Completed successfully

---

## STEP 0-F: Data Merging

**Objective:** Merge external features with training data.

**Implementation:**
- Created `step_0f_merge_external.py` script
- Merge logic on date column
- Handle missing values appropriately
- Generate feature summary report

**Merge Strategy:**
- Left join on training data (preserve all contract records)
- Match on contract start date
- Fill missing external features with defaults (0 for flags, -1 for counts)

**Output:**
- `data/processed/training_data_enriched.parquet` - Enriched training dataset
- `reports/feature_summary.csv` - Feature statistics

**Status:** ⏳ Requires STEP 0-D completion

---

## Design Decisions

### 1. Utilization Calculation Source

**Decision:** Use `Fleet.VehicleHistory` as the ONLY source for utilization.

**Rationale:**
- Explicit requirement from instructions
- Provides accurate vehicle status transitions
- Historical tracking of all vehicle state changes

### 2. Date Filter

**Decision:** Filter all data from `2023-01-01` onwards.

**Rationale:**
- Explicit requirement from instructions
- Focus on recent data for relevant patterns
- Ensures data quality and relevance

### 3. Data Storage Format

**Decision:** Use `.parquet` for training data, `.csv` for external features.

**Rationale:**
- Parquet: Efficient columnar storage, faster I/O, type preservation
- CSV: Simple, human-readable for external calendar data
- Explicit requirement from instructions

### 4. External Features Window

**Decision:** Include 7-day pre-holiday and 3-day post-holiday windows.

**Rationale:**
- Capture demand patterns before/after holidays
- Common planning horizon for rentals
- Asymmetric window (longer pre, shorter post) reflects booking behavior

### 5. Modular Code Structure

**Decision:** Separate modules for DB, data prep, external data, merging.

**Rationale:**
- Easier testing and validation
- Can run steps independently
- Follows instructions for incremental development

---

## Data Quality Observations

### Positive Observations

1. **Comprehensive Schema**: Well-structured database with clear separation of concerns
2. **Rich Metadata**: Database dictionary provides complete column information
3. **Historical Tracking**: VehicleHistory table captures all status changes
4. **Dimensional Tables**: Good support tables for context (Cities, Branches, etc.)

### Potential Challenges

1. **Status Mapping**: Need to map StatusId to actual status names (Rented, Available, etc.)
2. **Data Volume**: Large tables may require sampling or optimization
3. **Missing Values**: Need to handle nulls in date/amount fields
4. **Duplicate Columns**: Some tables have duplicate columns (noted in dictionary)

### Recommended Actions

1. Query the `Lookups` table to map StatusId values
2. Implement data quality checks for nulls and outliers
3. Monitor query performance for large table extractions
4. Validate date ranges and data completeness

---

## Constraints & Assumptions

### Hard Constraints (From Instructions)

1. ✅ Date filter: `>= 2023-01-01`
2. ✅ Utilization source: `Fleet.VehicleHistory` ONLY
3. ✅ Real data only (no synthetic data)
4. ✅ Storage: `.parquet` for training, `.csv` for external
5. ✅ Database: SQL Server 2019, Windows Authentication

### Assumptions

1. **Timestamps**: All timestamps in consistent timezone (likely UTC or local KSA time)
2. **Status Values**: StatusId follows consistent lookup values across time
3. **Data Completeness**: No major data gaps from 2023-01-01 onwards
4. **Business Logic**: Rental rules and pricing logic are stable
5. **Holiday Impact**: Holidays affect demand uniformly across branches

### Data Constraints

- **Minimum Date**: 2023-01-01
- **Maximum Date**: Latest data in database (to be determined)
- **Geographic Scope**: KSA only (based on external features)
- **Currency**: Assume single currency (SAR)

---

## Next Steps

### Immediate Actions

1. **Configure Database** (User Action Required)
   - Update `config.py` with server name and database name
   - Run `step_0b_connect_db.py` to validate connection

2. **Execute Data Extraction** (STEP 0-D)
   - Run `data_prep.py` to create training dataset
   - Validate data quality and completeness
   - Review utilization calculations

3. **Merge Features** (STEP 0-F)
   - Run `step_0f_merge_external.py` to merge external signals
   - Generate feature summary report
   - Verify no data loss in merge

### STEP 1: Model Training

Once STEP 0 is complete, proceed with:

1. **Feature Engineering**
   - Create lagged features (past utilization, past bookings)
   - One-hot encode categorical variables
   - Scale numeric features

2. **Train/Test Split**
   - Use time-based split (not random)
   - Maintain temporal ordering
   - Test set: Most recent 20% of data

3. **XGBoost Training**
   - Target: Demand (bookings count or contract count)
   - Hyperparameter tuning via cross-validation
   - Evaluate with RMSE, MAE, R²

### STEP 2: Pricing Engine

1. **Define Pricing Rules**
   - High demand + low utilization → Increase price
   - Low demand + high utilization → Decrease price
   - Holiday periods → Premium pricing

2. **Implement Multipliers**
   - Base price × demand_multiplier × supply_multiplier × event_multiplier
   - Configure min/max multiplier bounds

3. **Integration**
   - Connect demand predictions to pricing rules
   - Create pricing engine API

### STEP 3: Demo CLI

1. **Interactive Interface**
   - Input: Date, branch, vehicle category
   - Output: Recommended price with explanation

2. **Validation**
   - Test with historical data
   - Compare with actual prices
   - Validate business logic

---

## Summary

STEP 0 has successfully established the data foundation for the Dynamic Pricing Engine MVP. Key deliverables include:

- ✅ Database schema understanding
- ✅ Data extraction queries designed
- ✅ External features collected
- ✅ Comprehensive documentation

**Next Critical Action:** User must configure database connection to proceed with data extraction.

---

*Document generated on 2025-11-25 12:34:52*
*Project: Dynamic Pricing Engine MVP - Al-Manzumah Al-Muttahidah For IT Systems*
