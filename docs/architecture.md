# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    React + TypeScript                            │
│                    Tailwind + ShadCN                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│                        FastAPI                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   Auth   │  │  Config  │  │ Pricing  │  │ Forecast │        │
│  │  Router  │  │  Router  │  │  Engine  │  │  Service │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
│  SQL Server     │ │ External  │ │   App DB        │
│  (Source)       │ │   APIs    │ │  (Schemas)      │
│ ─────────────── │ │ ───────── │ │ ─────────────── │
│ eJarDbSTGLite   │ │ Open-Meteo│ │ appconfig       │
│ eJarDbReports   │ │ GDELT     │ │ dynamicpricing  │
│                 │ │ Booking   │ │                 │
└─────────────────┘ └───────────┘ └─────────────────┘
```

## Multi-Tenancy Design

### Row-Level Tenancy
- Every table includes `tenant_id` column
- API extracts tenant from JWT claim
- All queries filter by tenant automatically

### Tenant Context Flow
```
Request → JWT Token → Extract tenant_id → Filter all queries
```

## Database Schemas

### appconfig Schema
- `tenants` - Tenant registry
- `tenant_settings` - Per-tenant configurations
- `signal_weights` - Pricing signal weights
- `guardrails` - Min/max price rules
- `utilization_status_config` - Status mappings
- `branch_city_mapping` - Branch to city for weather
- `competitor_mapping` - Category to competitor product
- `selection_config` - Selected branches/categories
- `audit_log` - Action history

### dynamicpricing Schema
- `fact_daily_demand` - Feature store
- `forecast_demand_30d` - Forecast outputs
- `recommendations_30d` - Price recommendations

## Forecasting Architecture

### Global Model Approach
Single model trained on all tenant×branch×category series with:
- Lag features (7, 14, 30 days)
- Time features (day of week, month, etc.)
- External signals (weather, events)
- Tenant/branch/category embeddings

### Model Selection
1. Train multiple models (Naive, ETS, LightGBM, LSTM)
2. Backtest with rolling-origin evaluation
3. Select best by MAE/MAPE
4. Store winning model + metrics

## Pricing Engine

### Signal Combination
```
final_adjustment = Σ(signal_i × weight_i)
recommended_price = base_price × (1 + final_adjustment)
```

### Guardrail Enforcement
```
if recommended_price < min_price: recommended_price = min_price
if discount > max_discount: discount = max_discount
if premium > max_premium: premium = max_premium
```
