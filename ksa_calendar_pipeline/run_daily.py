"""
KSA Calendar Pipeline - Daily Runner
Updates holiday and event data for production use.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from .db import create_tables_if_not_exist, upsert_holidays, upsert_event_signal
from .holidays_calendarific import fetch_holidays
from .events_gdelt import fetch_events_for_date
from .config import DEFAULT_TENANT_ID, MONITORED_CITIES

logger = logging.getLogger(__name__)


def update_holidays(
    today: date = None,
    horizon_days: int = 365,
    tenant_id: int = DEFAULT_TENANT_ID
) -> int:
    """
    Update holidays for today + next horizon_days.
    
    Args:
        today: Reference date (defaults to today)
        horizon_days: Days to look ahead (default 365)
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Number of holidays inserted/updated
    """
    if today is None:
        today = date.today()
    
    logger.info(f"Updating holidays from {today} + {horizon_days} days")
    
    # Ensure tables exist
    create_tables_if_not_exist()
    
    # Determine years to fetch
    end_date = today + timedelta(days=horizon_days)
    years = set([today.year, end_date.year])
    
    total_count = 0
    for year in sorted(years):
        df = fetch_holidays(year)
        if not df.empty:
            # Filter to relevant date range
            df = df[df['date'] >= today]
            df = df[df['date'] <= end_date]
            if not df.empty:
                count = upsert_holidays(df, tenant_id)
                total_count += count
    
    logger.info(f"Updated {total_count} holidays")
    return total_count


def update_events(
    today: date = None,
    cities: list = None,
    tenant_id: int = DEFAULT_TENANT_ID
) -> int:
    """
    Update GDELT event signals for today.
    
    Args:
        today: Date to fetch events for (defaults to today)
        cities: List of cities (defaults to MONITORED_CITIES)
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Number of event records inserted/updated
    """
    if today is None:
        today = date.today()
    
    if cities is None:
        cities = MONITORED_CITIES
    
    logger.info(f"Updating events for {today}")
    
    # Ensure tables exist
    create_tables_if_not_exist()
    
    # Fetch events
    df = fetch_events_for_date(today, cities)
    
    if df.empty:
        logger.warning("No events fetched")
        return 0
    
    # Upsert to database
    count = upsert_event_signal(df, tenant_id)
    logger.info(f"Updated {count} event signals")
    return count


def run_daily_update(
    today: date = None,
    tenant_id: int = DEFAULT_TENANT_ID
) -> dict:
    """
    Run full daily update (holidays + events).
    
    Args:
        today: Reference date (defaults to today)
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Dictionary with counts: {"holidays": N, "events": M}
    """
    if today is None:
        today = date.today()
    
    logger.info(f"Running daily update for {today}")
    
    results = {
        "date": today.isoformat(),
        "holidays": 0,
        "events": 0
    }
    
    # Update holidays
    results["holidays"] = update_holidays(today, horizon_days=365, tenant_id=tenant_id)
    
    # Update events
    results["events"] = update_events(today, tenant_id=tenant_id)
    
    logger.info(f"Daily update complete: {results}")
    return results


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run daily update
    print("KSA Calendar Pipeline - Daily Update")
    print("=" * 50)
    
    results = run_daily_update()
    
    print(f"\nDate: {results['date']}")
    print(f"Holidays updated: {results['holidays']}")
    print(f"Events updated: {results['events']}")
