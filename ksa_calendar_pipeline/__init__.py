"""
KSA Calendar Pipeline
=====================

Pipeline for fetching and storing Saudi Arabia holiday and event data
for the Dynamic Pricing forecasting model.

Components:
- holidays_calendarific: Fetches KSA holidays from Calendarific API
- events_gdelt: Fetches event intensity from GDELT 2.1 DOC API
- db: Database operations for storage
- backfill: Historical data population
- run_daily: Daily update runner
- feature_builder: ML feature extraction
"""

from .config import DEFAULT_TENANT_ID, MONITORED_CITIES
from .db import (
    create_tables_if_not_exist,
    upsert_holidays,
    upsert_event_signal,
    get_holidays_count,
    get_events_count
)
from .holidays_calendarific import fetch_holidays, fetch_holidays_range
from .events_gdelt import fetch_gdelt_score, fetch_events_for_date
from .backfill import backfill_holidays, backfill_events
from .run_daily import update_holidays, update_events, run_daily_update
from .feature_builder import build_features, get_holiday_window

__all__ = [
    # Config
    'DEFAULT_TENANT_ID',
    'MONITORED_CITIES',
    # Database
    'create_tables_if_not_exist',
    'upsert_holidays',
    'upsert_event_signal',
    'get_holidays_count',
    'get_events_count',
    # Holidays
    'fetch_holidays',
    'fetch_holidays_range',
    # Events
    'fetch_gdelt_score',
    'fetch_events_for_date',
    # Backfill
    'backfill_holidays',
    'backfill_events',
    # Daily
    'update_holidays',
    'update_events',
    'run_daily_update',
    # Features
    'build_features',
    'get_holiday_window',
]
