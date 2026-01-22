# Requirements

## Functional Requirements

### Core Features
1. Dynamic pricing recommendations for car rental categories
2. 30-day rolling forecast window
3. Multi-tenant SaaS architecture (YELO as MVP tenant)
4. Configurable pricing signals and weights

### Pricing Signals (5 Elements)
1. **Utilization** - From future bookings + active contracts
2. **Demand Forecast** - 30-day ML-based prediction
3. **Weather** - From Open-Meteo API
4. **Events/Holidays** - KSA calendar + GDELT signals
5. **Competitor Pricing** - From Booking.com API

### UI Requirements
- Branch dropdown only (no category dropdown)
- Display 6 categories simultaneously
- Show base vs recommended prices (daily/weekly/monthly)
- Approve/Skip actions per category
- 30-day window view

### Granularity
- All calculations at: Branch × Category × Date

## Non-Functional Requirements

### Performance
- Forecast generation: < 5 minutes for all series
- API response time: < 500ms for recommendations

### Scalability
- Multi-tenant ready (row-level tenancy)
- Global forecasting model (not per-series)

### Security
- JWT-based authentication
- Tenant isolation via token claims

### Deployment
- Docker-ready
- Windows Server compatible
- Clear deployment documentation

## Data Sources

### SQL Server Databases
- `eJarDbSTGLite` - Contracts, bookings, vehicles, rates
- `eJarDbReports` - Reporting views

### External APIs
- Open-Meteo - Weather data
- Calendarific - KSA holidays
- GDELT - Event signals
- Booking.com - Competitor prices
