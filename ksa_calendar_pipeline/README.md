# KSA Calendar Pipeline

This pipeline provides holiday and event data for the Dynamic Pricing forecasting model.

## Features

- **KSA Holidays**: Saudi Arabia public holidays from Calendarific API
- **Event Signals**: News event intensity from GDELT 2.1 DOC API
- **Feature Builder**: Computes ML-ready features from raw data

## Setup

### Environment Variables

```bash
# SQL Server connection
SQL_SERVER=localhost
SQL_DATABASE=eJarDbSTGLite
SQL_USERNAME=     # Leave empty for Windows Auth
SQL_PASSWORD=     # Leave empty for Windows Auth

# Calendarific API (optional - fallback holidays used if not set)
CALENDARIFIC_API_KEY=your_api_key
```

### Installation

```bash
pip install requests pandas pyodbc
```

## Usage

### Initial Backfill

Populate historical data (run once):

```python
from ksa_calendar_pipeline.backfill import backfill_holidays, backfill_events
from datetime import date

# Backfill holidays for 2023-2027
backfill_holidays(2023, 2027)

# Backfill events for a date range (slow - only if needed)
backfill_events(date(2024, 1, 1), date(2025, 12, 31))
```

### Daily Updates

Run daily to keep data current:

```python
from ksa_calendar_pipeline.run_daily import run_daily_update

# Update holidays (today + 365 days) and events (today)
results = run_daily_update()
print(f"Holidays: {results['holidays']}, Events: {results['events']}")
```

Or run from command line:

```bash
python -m ksa_calendar_pipeline.run_daily
```

### Building Features

Get ML-ready features for forecasting:

```python
from ksa_calendar_pipeline.feature_builder import build_features, get_holiday_window
from datetime import date

# Build features for a date and city
features = build_features(date(2026, 1, 22), "Riyadh")
print(features)
# {
#     "date": "2026-01-22",
#     "city": "Riyadh",
#     "is_holiday": 0,
#     "holiday_name": None,
#     "is_weekend": 0,
#     "event_score_today": 2.3,
#     "event_score_3d_avg": 2.1,
#     "event_score_7d_avg": 1.8,
#     ...
# }

# Get holiday window info
window = get_holiday_window(date(2026, 1, 22))
print(window)
# {
#     "days_to_next_holiday": 31,
#     "days_since_last_holiday": 30,
#     "next_holiday_name": "Founding Day",
#     "holidays_in_window": 0
# }
```

## Database Tables

Tables are created in the `dynamicpricing` schema:

### `ksa_holidays`
| Column | Type | Description |
|--------|------|-------------|
| holiday_date | DATE | Date of holiday |
| holiday_name | NVARCHAR | English name |
| holiday_name_ar | NVARCHAR | Arabic name |
| holiday_type | NVARCHAR | National, Religious, etc. |
| is_public_holiday | BIT | Whether it's a public holiday |

### `ksa_daily_event_signal`
| Column | Type | Description |
|--------|------|-------------|
| event_date | DATE | Date |
| city_name | NVARCHAR | City name (Riyadh, Jeddah, etc.) |
| gdelt_volume | INT | Raw article count |
| gdelt_score | DECIMAL | log(1 + volume) |

## Monitored Cities

- Riyadh
- Jeddah
- Dammam
- Medina
- Abha

## API Notes

### Calendarific
- Requires API key (free tier available)
- Falls back to known fixed holidays if key not set
- Islamic holidays vary by year (lunar calendar)

### GDELT
- No API key required
- Rate limited - pipeline includes delays
- Returns news article counts mentioning city + "Saudi Arabia"
