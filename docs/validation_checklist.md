# Validation Checklist

## CHUNK 0 - Project Scaffold
- [ ] Backend runs GET /health successfully
- [ ] Frontend loads login page
- [ ] Frontend loads skeleton dashboard after login
- [ ] Docker compose builds without errors

## CHUNK 1 - SQL Server Connection + Data Discovery
- [ ] Connect to eJarDbSTGLite successfully
- [ ] Connect to eJarDbReports successfully
- [ ] Identify tenant_id column location
- [ ] Map branch_id correctly
- [ ] Map category_id correctly
- [ ] Extract base price paid from ContractsPaymentsItemsDetails
- [ ] Confirm min/max dates (data through 18-Nov-2025)
- [ ] Count total contracts for YELO tenant
- [ ] Count total bookings for YELO tenant
- [ ] Filter individual rentals (exclude corporate/lease)
- [ ] Document join paths

## CHUNK 2 - App DB + Config Tables
- [ ] appconfig schema created
- [ ] dynamicpricing schema created
- [ ] All metadata tables exist
- [ ] YELO tenant record inserted
- [ ] Config read/write via API works

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
