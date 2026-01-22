"""
KSA Calendar Pipeline - Holidays Module (Calendarific)
Fetches Saudi Arabia public holidays from Calendarific API.
"""
import requests
import pandas as pd
from datetime import datetime
import logging
import time
from typing import Optional

from .config import CALENDARIFIC_API_KEY, CALENDARIFIC_COUNTRY, MAX_RETRIES, RETRY_DELAY_SECONDS

logger = logging.getLogger(__name__)

CALENDARIFIC_BASE_URL = "https://calendarific.com/api/v2/holidays"


def fetch_holidays(year: int) -> pd.DataFrame:
    """
    Fetch Saudi Arabia holidays for a given year from Calendarific API.
    
    Args:
        year: Year to fetch holidays for
        
    Returns:
        DataFrame with columns: date, holiday_name, holiday_type, holiday_name_ar, is_public_holiday
    """
    if not CALENDARIFIC_API_KEY:
        logger.warning("CALENDARIFIC_API_KEY not set, using fallback holidays")
        return _get_fallback_holidays(year)
    
    params = {
        "api_key": CALENDARIFIC_API_KEY,
        "country": CALENDARIFIC_COUNTRY,
        "year": year
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(CALENDARIFIC_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get("meta", {}).get("code") != 200:
                logger.error(f"Calendarific API error: {data}")
                return _get_fallback_holidays(year)
            
            holidays = data.get("response", {}).get("holidays", [])
            
            if not holidays:
                logger.warning(f"No holidays found for year {year}")
                return pd.DataFrame()
            
            records = []
            for h in holidays:
                # Parse date
                date_info = h.get("date", {})
                iso_date = date_info.get("iso", "")[:10]  # Get YYYY-MM-DD part
                
                if not iso_date:
                    continue
                
                records.append({
                    "date": datetime.strptime(iso_date, "%Y-%m-%d").date(),
                    "holiday_name": h.get("name", "Unknown"),
                    "holiday_type": _get_holiday_type(h.get("type", [])),
                    "holiday_name_ar": h.get("name_local", None),
                    "is_public_holiday": "National holiday" in h.get("type", [])
                })
            
            df = pd.DataFrame(records)
            logger.info(f"Fetched {len(df)} holidays for {year}")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed")
                return _get_fallback_holidays(year)
    
    return pd.DataFrame()


def _get_holiday_type(types: list) -> str:
    """Extract primary holiday type from list"""
    priority = ["National holiday", "Religious", "Muslim", "Observance"]
    for p in priority:
        for t in types:
            if p.lower() in t.lower():
                return p
    return types[0] if types else "Unknown"


def _get_fallback_holidays(year: int) -> pd.DataFrame:
    """
    Return known KSA holidays when API is unavailable.
    These are approximate dates for Islamic holidays.
    """
    # Fixed holidays
    holidays = [
        # Saudi National Day
        {"date": f"{year}-09-23", "holiday_name": "Saudi National Day", 
         "holiday_type": "National", "is_public_holiday": True},
        # Founding Day (since 2022)
        {"date": f"{year}-02-22", "holiday_name": "Founding Day", 
         "holiday_type": "National", "is_public_holiday": True},
    ]
    
    # Note: Islamic holidays vary by year (lunar calendar)
    # These are placeholders - actual dates require API or manual lookup
    islamic_holidays = [
        {"name": "Eid al-Fitr", "type": "Religious"},
        {"name": "Eid al-Adha", "type": "Religious"},
    ]
    
    records = []
    for h in holidays:
        records.append({
            "date": datetime.strptime(h["date"], "%Y-%m-%d").date(),
            "holiday_name": h["holiday_name"],
            "holiday_type": h["holiday_type"],
            "holiday_name_ar": None,
            "is_public_holiday": h["is_public_holiday"]
        })
    
    logger.info(f"Using {len(records)} fallback holidays for {year}")
    return pd.DataFrame(records)


def fetch_holidays_range(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Fetch holidays for a range of years.
    
    Args:
        start_year: First year (inclusive)
        end_year: Last year (inclusive)
        
    Returns:
        Combined DataFrame of all holidays
    """
    all_holidays = []
    
    for year in range(start_year, end_year + 1):
        df = fetch_holidays(year)
        if not df.empty:
            all_holidays.append(df)
        time.sleep(0.5)  # Rate limiting
    
    if all_holidays:
        return pd.concat(all_holidays, ignore_index=True)
    return pd.DataFrame()
