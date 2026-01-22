"""
KSA Calendar Pipeline - GDELT Events Module
Fetches event intensity signals from GDELT 2.1 DOC API.

GDELT (Global Database of Events, Language, and Tone) tracks news articles
worldwide. We use it to detect event intensity in Saudi Arabian cities.
"""
import requests
import pandas as pd
from datetime import datetime, date, timedelta
import logging
import time
import math
from typing import Tuple, Optional

from .config import GDELT_BASE_URL, GDELT_TIMEOUT, MAX_RETRIES, RETRY_DELAY_SECONDS, MONITORED_CITIES

logger = logging.getLogger(__name__)


def fetch_gdelt_score(city: str, query_date: date) -> Tuple[int, float]:
    """
    Fetch GDELT event intensity for a city on a specific date.
    
    Uses GDELT DOC 2.1 API to count news articles mentioning the city.
    
    Args:
        city: City name (e.g., "Riyadh", "Jeddah")
        query_date: Date to query
        
    Returns:
        Tuple of (volume, score) where:
        - volume: Raw article count
        - score: log(1 + volume)
    """
    # Format date for GDELT (YYYYMMDD format)
    date_str = query_date.strftime("%Y%m%d")
    
    # Build query - search for city name in Saudi Arabia context
    query = f'{city} "Saudi Arabia"'
    
    params = {
        "query": query,
        "mode": "artcount",  # Just get article count
        "startdatetime": f"{date_str}000000",
        "enddatetime": f"{date_str}235959",
        "maxrecords": 1,
        "format": "json"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                GDELT_BASE_URL, 
                params=params, 
                timeout=GDELT_TIMEOUT
            )
            
            # GDELT sometimes returns HTML error pages
            if "<!DOCTYPE" in response.text or "<html" in response.text.lower():
                logger.warning(f"GDELT returned HTML instead of JSON for {city} on {query_date}")
                return 0, 0.0
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # The artcount mode returns article count in the response
            if isinstance(data, dict):
                volume = data.get("artcount", 0) or data.get("count", 0) or 0
            elif isinstance(data, list) and len(data) > 0:
                volume = len(data)  # If it returns article list
            else:
                volume = 0
            
            score = math.log(1 + volume)
            logger.debug(f"GDELT {city} {query_date}: volume={volume}, score={score:.4f}")
            return volume, score
            
        except requests.exceptions.Timeout:
            logger.warning(f"GDELT timeout for {city} on {query_date}")
            return 0, 0.0
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"GDELT request failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed for {city} on {query_date}")
                return 0, 0.0
                
        except (ValueError, KeyError) as e:
            logger.warning(f"GDELT parse error for {city} on {query_date}: {e}")
            return 0, 0.0
    
    return 0, 0.0


def fetch_events_for_date(query_date: date, cities: list = None) -> pd.DataFrame:
    """
    Fetch GDELT event scores for all monitored cities on a date.
    
    Args:
        query_date: Date to query
        cities: List of city names (defaults to MONITORED_CITIES)
        
    Returns:
        DataFrame with columns: date, city_name, gdelt_volume, gdelt_score
    """
    if cities is None:
        cities = MONITORED_CITIES
    
    records = []
    
    for city in cities:
        volume, score = fetch_gdelt_score(city, query_date)
        records.append({
            "date": query_date,
            "city_name": city,
            "gdelt_volume": volume,
            "gdelt_score": round(score, 4)
        })
        time.sleep(0.3)  # Rate limiting between cities
    
    return pd.DataFrame(records)


def fetch_events_for_date_range(
    start_date: date, 
    end_date: date,
    cities: list = None
) -> pd.DataFrame:
    """
    Fetch GDELT event scores for a date range.
    
    Args:
        start_date: First date (inclusive)
        end_date: Last date (inclusive)
        cities: List of city names
        
    Returns:
        DataFrame with columns: date, city_name, gdelt_volume, gdelt_score
    """
    if cities is None:
        cities = MONITORED_CITIES
    
    all_records = []
    current = start_date
    
    while current <= end_date:
        logger.info(f"Fetching GDELT events for {current}")
        df = fetch_events_for_date(current, cities)
        if not df.empty:
            all_records.append(df)
        current += timedelta(days=1)
        time.sleep(0.5)  # Rate limiting between days
    
    if all_records:
        return pd.concat(all_records, ignore_index=True)
    return pd.DataFrame()
