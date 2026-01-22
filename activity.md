# Activity Log

This file logs all successful commits to the repository.

---

## 2026-01-22

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
