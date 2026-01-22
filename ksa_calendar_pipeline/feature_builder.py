"""
KSA Calendar Pipeline - Feature Builder
Builds features from holiday and event data for the forecasting model.
"""
import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional
import pyodbc

from .db import get_connection
from .config import DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)


def build_features(
    query_date: date,
    city: str,
    tenant_id: int = DEFAULT_TENANT_ID
) -> Dict[str, Any]:
    """
    Build calendar/event features for a specific date and city.
    
    Returns:
        Dictionary with features:
        - is_holiday: 1 if date is a holiday, 0 otherwise
        - holiday_name: Name of holiday or None
        - event_score_today: GDELT score for the date
        - event_score_3d_avg: Average GDELT score over 3 days
        - event_score_7d_avg: Average GDELT score over 7 days
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    features = {
        "date": query_date.isoformat(),
        "city": city,
        "is_holiday": 0,
        "holiday_name": None,
        "holiday_type": None,
        "is_weekend": 1 if query_date.weekday() >= 4 else 0,  # Fri-Sat in KSA
        "event_score_today": 0.0,
        "event_score_3d_avg": 0.0,
        "event_score_7d_avg": 0.0,
        "event_volume_today": 0
    }
    
    try:
        # Check if date is a holiday
        cursor.execute("""
            SELECT TOP 1 holiday_name, holiday_type
            FROM dynamicpricing.ksa_holidays
            WHERE tenant_id = ? AND holiday_date = ?
        """, [tenant_id, query_date])
        
        row = cursor.fetchone()
        if row:
            features["is_holiday"] = 1
            features["holiday_name"] = row[0]
            features["holiday_type"] = row[1]
        
        # Get today's event score
        cursor.execute("""
            SELECT gdelt_volume, gdelt_score
            FROM dynamicpricing.ksa_daily_event_signal
            WHERE tenant_id = ? AND event_date = ? AND city_name = ?
        """, [tenant_id, query_date, city])
        
        row = cursor.fetchone()
        if row:
            features["event_volume_today"] = row[0] or 0
            features["event_score_today"] = float(row[1] or 0)
        
        # Get 3-day average event score
        start_3d = query_date - timedelta(days=2)
        cursor.execute("""
            SELECT AVG(gdelt_score)
            FROM dynamicpricing.ksa_daily_event_signal
            WHERE tenant_id = ? 
              AND event_date BETWEEN ? AND ?
              AND city_name = ?
        """, [tenant_id, start_3d, query_date, city])
        
        row = cursor.fetchone()
        if row and row[0]:
            features["event_score_3d_avg"] = round(float(row[0]), 4)
        
        # Get 7-day average event score
        start_7d = query_date - timedelta(days=6)
        cursor.execute("""
            SELECT AVG(gdelt_score)
            FROM dynamicpricing.ksa_daily_event_signal
            WHERE tenant_id = ? 
              AND event_date BETWEEN ? AND ?
              AND city_name = ?
        """, [tenant_id, start_7d, query_date, city])
        
        row = cursor.fetchone()
        if row and row[0]:
            features["event_score_7d_avg"] = round(float(row[0]), 4)
        
        return features
        
    except Exception as e:
        logger.error(f"Error building features for {city} on {query_date}: {e}")
        return features
    finally:
        cursor.close()
        conn.close()


def build_features_range(
    start_date: date,
    end_date: date,
    city: str,
    tenant_id: int = DEFAULT_TENANT_ID
) -> list:
    """
    Build features for a date range.
    
    Returns:
        List of feature dictionaries
    """
    features_list = []
    current = start_date
    
    while current <= end_date:
        features = build_features(current, city, tenant_id)
        features_list.append(features)
        current += timedelta(days=1)
    
    return features_list


def get_holiday_window(
    query_date: date,
    window_days: int = 7,
    tenant_id: int = DEFAULT_TENANT_ID
) -> Dict[str, Any]:
    """
    Get holiday information within a window around a date.
    
    Returns:
        Dictionary with:
        - days_to_next_holiday: Days until next holiday (-1 if none in window)
        - days_since_last_holiday: Days since last holiday (-1 if none in window)
        - next_holiday_name: Name of next holiday or None
        - holidays_in_window: Count of holidays in window
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    result = {
        "days_to_next_holiday": -1,
        "days_since_last_holiday": -1,
        "next_holiday_name": None,
        "holidays_in_window": 0
    }
    
    try:
        window_start = query_date - timedelta(days=window_days)
        window_end = query_date + timedelta(days=window_days)
        
        # Count holidays in window
        cursor.execute("""
            SELECT COUNT(*)
            FROM dynamicpricing.ksa_holidays
            WHERE tenant_id = ? AND holiday_date BETWEEN ? AND ?
        """, [tenant_id, window_start, window_end])
        
        row = cursor.fetchone()
        result["holidays_in_window"] = row[0] if row else 0
        
        # Find next holiday
        cursor.execute("""
            SELECT TOP 1 holiday_date, holiday_name
            FROM dynamicpricing.ksa_holidays
            WHERE tenant_id = ? AND holiday_date >= ?
            ORDER BY holiday_date ASC
        """, [tenant_id, query_date])
        
        row = cursor.fetchone()
        if row:
            days_to = (row[0] - query_date).days
            if days_to <= window_days:
                result["days_to_next_holiday"] = days_to
                result["next_holiday_name"] = row[1]
        
        # Find last holiday
        cursor.execute("""
            SELECT TOP 1 holiday_date
            FROM dynamicpricing.ksa_holidays
            WHERE tenant_id = ? AND holiday_date <= ?
            ORDER BY holiday_date DESC
        """, [tenant_id, query_date])
        
        row = cursor.fetchone()
        if row:
            days_since = (query_date - row[0]).days
            if days_since <= window_days:
                result["days_since_last_holiday"] = days_since
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting holiday window for {query_date}: {e}")
        return result
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test feature builder
    from datetime import date
    
    test_date = date(2026, 1, 22)
    test_city = "Riyadh"
    
    print(f"Building features for {test_city} on {test_date}")
    print("=" * 50)
    
    features = build_features(test_date, test_city)
    for k, v in features.items():
        print(f"  {k}: {v}")
    
    print("\nHoliday window:")
    window = get_holiday_window(test_date)
    for k, v in window.items():
        print(f"  {k}: {v}")
