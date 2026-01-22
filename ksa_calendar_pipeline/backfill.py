"""
KSA Calendar Pipeline - Backfill Module
Populates historical holiday and event data.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from .db import create_tables_if_not_exist, upsert_holidays, upsert_event_signal
from .holidays_calendarific import fetch_holidays_range
from .events_gdelt import fetch_events_for_date_range
from .config import DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)


def backfill_holidays(
    start_year: int, 
    end_year: int,
    tenant_id: int = DEFAULT_TENANT_ID
) -> int:
    """
    Backfill holidays for a range of years.
    
    Args:
        start_year: First year (inclusive)
        end_year: Last year (inclusive)
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Number of holidays inserted/updated
    """
    logger.info(f"Backfilling holidays from {start_year} to {end_year}")
    
    # Ensure tables exist
    create_tables_if_not_exist()
    
    # Fetch holidays
    df = fetch_holidays_range(start_year, end_year)
    
    if df.empty:
        logger.warning("No holidays to backfill")
        return 0
    
    # Upsert to database
    count = upsert_holidays(df, tenant_id)
    logger.info(f"Backfilled {count} holidays")
    return count


def backfill_events(
    start_date: date,
    end_date: date,
    tenant_id: int = DEFAULT_TENANT_ID
) -> int:
    """
    Backfill GDELT event signals for a date range.
    
    Args:
        start_date: First date (inclusive)
        end_date: Last date (inclusive)
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Number of event records inserted/updated
    """
    logger.info(f"Backfilling events from {start_date} to {end_date}")
    
    # Ensure tables exist
    create_tables_if_not_exist()
    
    # Fetch events
    df = fetch_events_for_date_range(start_date, end_date)
    
    if df.empty:
        logger.warning("No events to backfill")
        return 0
    
    # Upsert to database
    count = upsert_event_signal(df, tenant_id)
    logger.info(f"Backfilled {count} event signals")
    return count


def backfill_last_n_years(
    years: int = 3,
    include_events: bool = True,
    tenant_id: int = DEFAULT_TENANT_ID
) -> dict:
    """
    Convenience function to backfill last N years of data.
    
    Args:
        years: Number of years to backfill
        include_events: Whether to also backfill GDELT events
        tenant_id: Tenant ID for multi-tenancy
        
    Returns:
        Dictionary with counts: {"holidays": N, "events": M}
    """
    current_year = datetime.now().year
    start_year = current_year - years + 1
    
    results = {"holidays": 0, "events": 0}
    
    # Backfill holidays
    results["holidays"] = backfill_holidays(start_year, current_year + 1, tenant_id)
    
    # Backfill events (only if requested - can be slow)
    if include_events:
        start_date = date(start_year, 1, 1)
        end_date = date.today() - timedelta(days=1)  # Yesterday
        results["events"] = backfill_events(start_date, end_date, tenant_id)
    
    return results


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run backfill
    print("KSA Calendar Pipeline - Backfill")
    print("=" * 50)
    
    # Backfill holidays for 2023-2027
    print("\nBackfilling holidays...")
    holidays_count = backfill_holidays(2023, 2027)
    print(f"  Holidays: {holidays_count}")
    
    # Backfill events for last 7 days only (for testing)
    print("\nBackfilling recent events...")
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=7)
    events_count = backfill_events(start_date, end_date)
    print(f"  Events: {events_count}")
    
    print("\nBackfill complete!")
