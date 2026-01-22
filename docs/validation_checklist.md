# Validation Checklist

## CHUNK 0 - Project Scaffold
- [x] Backend runs GET /health successfully
- [x] Frontend loads login page
- [x] Frontend loads skeleton dashboard after login
- [x] Docker compose builds without errors

## CHUNK 1 - SQL Server Connection + Data Discovery
- [x] Connect to eJarDbSTGLite successfully (Windows Auth: Trusted_Connection=yes)
- [x] Identify tenant_id column location → TenantId in Rental.Contract, YELO = 1
- [x] Map branch_id correctly → PickupBranchId in Rental.Contract → Rental.Branches
- [x] Map category_id correctly → via Fleet.Vehicles.ModelId → Rental.CarModels.CarCategoryId
- [x] Identify base price source → Contract.DailyRateAmount (100% complete) or ContractsPaymentsItemsDetails.ItemTypeId=1
- [x] Confirm min/max dates → 2022-01-01 to 2025-11-18 (data available)
- [x] Count total contracts for YELO tenant → 5,722,215 total, 2,826,983 individual (2022+)
- [x] Filter individual rentals → Discriminator='Contract', StatusId=211 (Delivered)
- [x] Document join paths → See data_discovery_report.md
- [x] Discover pre-existing dynamicpricing schema with TrainingData (36,308 rows)
- [x] Discover TopBranches (6 branches) and TopCategories (6 categories) pre-defined

## CHUNK 2 - App DB + Config Tables
- [x] dynamicpricing schema exists (pre-existing)
- [x] appconfig schema created (9 tables)
- [x] All metadata tables exist:
  - [x] appconfig.tenants
  - [x] appconfig.tenant_settings
  - [x] appconfig.guardrails
  - [x] appconfig.signal_weights
  - [x] appconfig.utilization_status_config
  - [x] appconfig.branch_city_mapping
  - [x] appconfig.competitor_mapping
  - [x] appconfig.selection_config
  - [x] appconfig.audit_log
- [x] YELO tenant record inserted (id=1)
- [x] Default guardrails configured (min_price=50, max_discount=30%, max_premium=50%)
- [x] Signal weights configured (6 signals: utilization, demand_forecast, weather, holiday, event, competitor)
- [x] Branch selection config populated (6 MVP branches)
- [x] Category selection config populated (6 MVP categories)
- [x] Branch city mapping with coordinates for weather API
- [x] Config read/write via API (endpoints created, DB tested)

## CHUNK 3 - Base Price Engine
- [ ] BaseRateService returns daily/weekly/monthly prices
- [ ] Prices verified for 5 random branch×category
- [ ] Effective period logic works

## CHUNK 4 - Utilization Engine
- [ ] Utilization computed per branch×category×date
- [ ] Utilization ∈ [0, 1] validated
- [ ] Utilization varies across categories
- [ ] Admin can configure statuses via UI
- [ ] Python vs SQL aggregation match

## CHUNK 5 - External Signals
- [ ] Open-Meteo weather data fetched
- [ ] Weather table populated
- [ ] ksa_holidays table populated (Calendarific)
- [ ] ksa_daily_event_signal table populated (GDELT)
- [ ] Branch→City mapping configurable
- [ ] feature_builder returns correct outputs

## CHUNK 6 - Feature Store
- [ ] fact_daily_demand table populated
- [ ] TRAIN/VALIDATION split applied
- [ ] Date ranges correct
- [ ] Target (demand) not flatline
- [ ] Missing rate documented

## CHUNK 7 - Forecasting
- [ ] Multiple models trained (Naive, ETS, LightGBM, LSTM)
- [ ] Backtesting completed
- [ ] Best model selected by MAE/MAPE
- [ ] 30-day forecasts generated
- [ ] Forecasts not flatline
- [ ] Model metrics stored in DB

## CHUNK 8 - Competitor Pricing
- [ ] Booking.com API integrated
- [ ] Category→Competitor mapping works
- [ ] Competitor index = avg top 3
- [ ] Caching implemented

## CHUNK 9 - Pricing Engine
- [ ] Signals combined with weights
- [ ] Guardrails enforced
- [ ] Recommendations generated for all 6 categories
- [ ] Explanation text generated
- [ ] Recommendations stored in DB

## CHUNK 10 - Frontend Dashboard
- [ ] Branch dropdown works
- [ ] Start date selector works
- [ ] 6 categories displayed simultaneously
- [ ] Base vs recommended prices shown
- [ ] 30-day window scrollable
- [ ] Approve updates DB
- [ ] Skip updates DB
- [ ] Audit log populated

## CHUNK 11 - Deployment
- [ ] docker-compose runs successfully
- [ ] All services start
- [ ] Frontend accessible
- [ ] Backend accessible
- [ ] Login works
- [ ] Real data displayed
