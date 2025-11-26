"""
STEP 0-E: External data fetcher for demand signals.

This module fetches external features to enhance demand prediction:
1. KSA Public Holidays (Hijri and Gregorian)
2. Major Events (sports, festivals, conferences)
3. Weather data (optional)
4. School vacation periods

Data sources:
- KSA holidays: Multiple sources including official calendars
- Events: Scraped from event calendars and tourism websites
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from pathlib import Path
import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_ksa_holidays_2023_2025() -> pd.DataFrame:
    """
    Get KSA public holidays for 2023-2025.
    
    Includes both Hijri and Gregorian holidays.
    Major holidays:
    - Eid Al-Fitr (3-4 days)
    - Eid Al-Adha (4-5 days)
    - Saudi National Day (September 23)
    - Founding Day (February 22)
    
    Returns:
        pd.DataFrame: Holiday calendar with date, name, type
    """
    logger.info("Fetching KSA public holidays...")
    
    # Hardcoded major holidays for 2023-2025
    # Note: Hijri holidays shift each year in Gregorian calendar
    holidays = [
        # 2023
        {'date': '2023-02-22', 'name': 'Founding Day', 'type': 'national', 'duration': 1},
        {'date': '2023-04-21', 'name': 'Eid Al-Fitr Start', 'type': 'religious', 'duration': 4},
        {'date': '2023-04-22', 'name': 'Eid Al-Fitr Day 2', 'type': 'religious', 'duration': 4},
        {'date': '2023-04-23', 'name': 'Eid Al-Fitr Day 3', 'type': 'religious', 'duration': 4},
        {'date': '2023-04-24', 'name': 'Eid Al-Fitr Day 4', 'type': 'religious', 'duration': 4},
        {'date': '2023-06-27', 'name': 'Arafat Day', 'type': 'religious', 'duration': 1},
        {'date': '2023-06-28', 'name': 'Eid Al-Adha Start', 'type': 'religious', 'duration': 5},
        {'date': '2023-06-29', 'name': 'Eid Al-Adha Day 2', 'type': 'religious', 'duration': 5},
        {'date': '2023-06-30', 'name': 'Eid Al-Adha Day 3', 'type': 'religious', 'duration': 5},
        {'date': '2023-07-01', 'name': 'Eid Al-Adha Day 4', 'type': 'religious', 'duration': 5},
        {'date': '2023-07-02', 'name': 'Eid Al-Adha Day 5', 'type': 'religious', 'duration': 5},
        {'date': '2023-09-23', 'name': 'Saudi National Day', 'type': 'national', 'duration': 1},
        
        # 2024
        {'date': '2024-02-22', 'name': 'Founding Day', 'type': 'national', 'duration': 1},
        {'date': '2024-04-10', 'name': 'Eid Al-Fitr Start', 'type': 'religious', 'duration': 4},
        {'date': '2024-04-11', 'name': 'Eid Al-Fitr Day 2', 'type': 'religious', 'duration': 4},
        {'date': '2024-04-12', 'name': 'Eid Al-Fitr Day 3', 'type': 'religious', 'duration': 4},
        {'date': '2024-04-13', 'name': 'Eid Al-Fitr Day 4', 'type': 'religious', 'duration': 4},
        {'date': '2024-06-15', 'name': 'Arafat Day', 'type': 'religious', 'duration': 1},
        {'date': '2024-06-16', 'name': 'Eid Al-Adha Start', 'type': 'religious', 'duration': 5},
        {'date': '2024-06-17', 'name': 'Eid Al-Adha Day 2', 'type': 'religious', 'duration': 5},
        {'date': '2024-06-18', 'name': 'Eid Al-Adha Day 3', 'type': 'religious', 'duration': 5},
        {'date': '2024-06-19', 'name': 'Eid Al-Adha Day 4', 'type': 'religious', 'duration': 5},
        {'date': '2024-06-20', 'name': 'Eid Al-Adha Day 5', 'type': 'religious', 'duration': 5},
        {'date': '2024-09-23', 'name': 'Saudi National Day', 'type': 'national', 'duration': 1},
        
        # 2025
        {'date': '2025-02-22', 'name': 'Founding Day', 'type': 'national', 'duration': 1},
        {'date': '2025-03-30', 'name': 'Eid Al-Fitr Start', 'type': 'religious', 'duration': 4},
        {'date': '2025-03-31', 'name': 'Eid Al-Fitr Day 2', 'type': 'religious', 'duration': 4},
        {'date': '2025-04-01', 'name': 'Eid Al-Fitr Day 3', 'type': 'religious', 'duration': 4},
        {'date': '2025-04-02', 'name': 'Eid Al-Fitr Day 4', 'type': 'religious', 'duration': 4},
        {'date': '2025-06-05', 'name': 'Arafat Day', 'type': 'religious', 'duration': 1},
        {'date': '2025-06-06', 'name': 'Eid Al-Adha Start', 'type': 'religious', 'duration': 5},
        {'date': '2025-06-07', 'name': 'Eid Al-Adha Day 2', 'type': 'religious', 'duration': 5},
        {'date': '2025-06-08', 'name': 'Eid Al-Adha Day 3', 'type': 'religious', 'duration': 5},
        {'date': '2025-06-09', 'name': 'Eid Al-Adha Day 4', 'type': 'religious', 'duration': 5},
        {'date': '2025-06-10', 'name': 'Eid Al-Adha Day 5', 'type': 'religious', 'duration': 5},
        {'date': '2025-09-23', 'name': 'Saudi National Day', 'type': 'national', 'duration': 1},
    ]
    
    df = pd.DataFrame(holidays)
    df['date'] = pd.to_datetime(df['date'])
    df['is_holiday'] = 1
    
    logger.info(f"  ✓ Loaded {len(df)} holiday dates for 2023-2025")
    logger.info(f"  ✓ Religious holidays: {len(df[df['type']=='religious'])}")
    logger.info(f"  ✓ National holidays: {len(df[df['type']=='national'])}")
    
    return df


def get_ksa_school_vacations() -> pd.DataFrame:
    """
    Get KSA school vacation periods.
    
    Major vacation periods:
    - Summer vacation: ~3 months (June-August)
    - Mid-year break: ~2 weeks (January)
    - Eid breaks: Around religious holidays
    
    Returns:
        pd.DataFrame: School vacation periods
    """
    logger.info("Fetching KSA school vacation periods...")
    
    vacations = [
        # 2023
        {'start': '2023-01-15', 'end': '2023-01-29', 'name': 'Mid-Year Break', 'year': 2023},
        {'start': '2023-06-22', 'end': '2023-08-27', 'name': 'Summer Vacation', 'year': 2023},
        
        # 2024
        {'start': '2024-01-14', 'end': '2024-01-28', 'name': 'Mid-Year Break', 'year': 2024},
        {'start': '2024-06-10', 'end': '2024-08-18', 'name': 'Summer Vacation', 'year': 2024},
        
        # 2025
        {'start': '2025-01-12', 'end': '2025-01-26', 'name': 'Mid-Year Break', 'year': 2025},
        {'start': '2025-06-26', 'end': '2025-08-31', 'name': 'Summer Vacation', 'year': 2025},
    ]
    
    df = pd.DataFrame(vacations)
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    
    logger.info(f"  ✓ Loaded {len(df)} school vacation periods")
    
    return df


def get_ksa_major_events() -> pd.DataFrame:
    """
    Get major events in KSA that may affect car rental demand.
    
    Events include:
    - Formula 1 Saudi Arabian Grand Prix
    - Riyadh Season
    - Jeddah Season
    - Hajj and Umrah seasons
    - Business conferences
    
    Returns:
        pd.DataFrame: Major events calendar
    """
    logger.info("Fetching KSA major events...")
    
    events = [
        # 2023
        {'date': '2023-03-19', 'name': 'Formula 1 Saudi Arabian Grand Prix', 'city': 'Jeddah', 'category': 'sports'},
        {'date': '2023-10-28', 'name': 'Riyadh Season Start', 'city': 'Riyadh', 'category': 'festival'},
        {'date': '2023-12-07', 'name': 'Jeddah Season Start', 'city': 'Jeddah', 'category': 'festival'},
        {'date': '2023-06-15', 'name': 'Hajj Season Start', 'city': 'Mecca', 'category': 'religious'},
        
        # 2024
        {'date': '2024-03-09', 'name': 'Formula 1 Saudi Arabian Grand Prix', 'city': 'Jeddah', 'category': 'sports'},
        {'date': '2024-10-26', 'name': 'Riyadh Season Start', 'city': 'Riyadh', 'category': 'festival'},
        {'date': '2024-12-05', 'name': 'Jeddah Season Start', 'city': 'Jeddah', 'category': 'festival'},
        {'date': '2024-06-05', 'name': 'Hajj Season Start', 'city': 'Mecca', 'category': 'religious'},
        
        # 2025
        {'date': '2025-03-15', 'name': 'Formula 1 Saudi Arabian Grand Prix', 'city': 'Jeddah', 'category': 'sports'},
        {'date': '2025-10-25', 'name': 'Riyadh Season Start', 'city': 'Riyadh', 'category': 'festival'},
        {'date': '2025-12-04', 'name': 'Jeddah Season Start', 'city': 'Jeddah', 'category': 'festival'},
        {'date': '2025-05-27', 'name': 'Hajj Season Start', 'city': 'Mecca', 'category': 'religious'},
    ]
    
    df = pd.DataFrame(events)
    df['date'] = pd.to_datetime(df['date'])
    df['is_major_event'] = 1
    
    logger.info(f"  ✓ Loaded {len(df)} major events")
    logger.info(f"  ✓ Event categories: {df['category'].unique().tolist()}")
    
    return df


def get_ramadan_periods() -> pd.DataFrame:
    """
    Get Ramadan periods (holy month of fasting).
    
    Ramadan is the peak Umrah season with highest religious tourism.
    
    Returns:
        pd.DataFrame: Ramadan periods
    """
    logger.info("Fetching Ramadan periods...")
    
    ramadan_periods = [
        # 2023
        {'start': '2023-03-23', 'end': '2023-04-21', 'name': 'Ramadan', 'year': 2023},
        
        # 2024
        {'start': '2024-03-11', 'end': '2024-04-09', 'name': 'Ramadan', 'year': 2024},
        
        # 2025
        {'start': '2025-03-01', 'end': '2025-03-29', 'name': 'Ramadan', 'year': 2025},
    ]
    
    df = pd.DataFrame(ramadan_periods)
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    
    logger.info(f"  ✓ Loaded {len(df)} Ramadan periods")
    
    return df


def get_umrah_peak_periods() -> pd.DataFrame:
    """
    Get peak Umrah seasons (beyond Ramadan).
    
    Peak Umrah periods:
    - Rajab & Sha'ban (2 months before Ramadan) - High Umrah activity
    - Shawwal (month after Ramadan) - Post-Ramadan Umrah
    - School holidays (Summer, Mid-year) - Family Umrah trips
    
    Returns:
        pd.DataFrame: Umrah peak periods
    """
    logger.info("Fetching peak Umrah seasons...")
    
    umrah_periods = [
        # 2023
        {'start': '2023-01-23', 'end': '2023-03-22', 'name': 'Rajab-Shaban Umrah Season', 'year': 2023, 'intensity': 'high'},
        {'start': '2023-04-22', 'end': '2023-05-21', 'name': 'Shawwal Umrah Season', 'year': 2023, 'intensity': 'high'},
        {'start': '2023-06-22', 'end': '2023-08-27', 'name': 'Summer Umrah Season', 'year': 2023, 'intensity': 'medium'},
        
        # 2024
        {'start': '2024-01-11', 'end': '2024-03-10', 'name': 'Rajab-Shaban Umrah Season', 'year': 2024, 'intensity': 'high'},
        {'start': '2024-04-10', 'end': '2024-05-09', 'name': 'Shawwal Umrah Season', 'year': 2024, 'intensity': 'high'},
        {'start': '2024-06-10', 'end': '2024-08-18', 'name': 'Summer Umrah Season', 'year': 2024, 'intensity': 'medium'},
        
        # 2025
        {'start': '2025-01-01', 'end': '2025-02-28', 'name': 'Rajab-Shaban Umrah Season', 'year': 2025, 'intensity': 'high'},
        {'start': '2025-03-30', 'end': '2025-04-28', 'name': 'Shawwal Umrah Season', 'year': 2025, 'intensity': 'high'},
        {'start': '2025-06-26', 'end': '2025-08-31', 'name': 'Summer Umrah Season', 'year': 2025, 'intensity': 'medium'},
    ]
    
    df = pd.DataFrame(umrah_periods)
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    
    logger.info(f"  ✓ Loaded {len(df)} Umrah peak periods")
    
    return df


def create_holiday_features(start_date: str = '2023-01-01', 
                           end_date: str = '2025-12-31') -> pd.DataFrame:
    """
    Create a comprehensive calendar with holiday and event features.
    
    Args:
        start_date: Start date for calendar
        end_date: End date for calendar
        
    Returns:
        pd.DataFrame: Daily calendar with external features
    """
    logger.info(f"Creating external features calendar from {start_date} to {end_date}...")
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    calendar = pd.DataFrame({'date': dates})
    
    # Add basic temporal features
    calendar['day_of_week'] = calendar['date'].dt.dayofweek
    calendar['month'] = calendar['date'].dt.month
    calendar['quarter'] = calendar['date'].dt.quarter
    calendar['is_weekend'] = calendar['day_of_week'].isin([4, 5]).astype(int)  # Fri-Sat in KSA
    
    # Get external data
    holidays = get_ksa_holidays_2023_2025()
    vacations = get_ksa_school_vacations()
    events = get_ksa_major_events()
    ramadan_periods = get_ramadan_periods()
    umrah_periods = get_umrah_peak_periods()
    
    # Merge holidays
    calendar = calendar.merge(
        holidays[['date', 'is_holiday', 'name', 'type', 'duration']],
        on='date',
        how='left'
    )
    calendar['is_holiday'] = calendar['is_holiday'].fillna(0).astype(int)
    calendar['holiday_name'] = calendar['name'].fillna('')
    calendar['holiday_type'] = calendar['type'].fillna('')
    calendar['holiday_duration'] = calendar['duration'].fillna(0).astype(int)
    calendar.drop(['name', 'type', 'duration'], axis=1, inplace=True)
    
    # Add school vacation flag
    calendar['is_school_vacation'] = 0
    for _, vacation in vacations.iterrows():
        mask = (calendar['date'] >= vacation['start']) & (calendar['date'] <= vacation['end'])
        calendar.loc[mask, 'is_school_vacation'] = 1
    
    # Add Ramadan flag
    calendar['is_ramadan'] = 0
    for _, ramadan in ramadan_periods.iterrows():
        mask = (calendar['date'] >= ramadan['start']) & (calendar['date'] <= ramadan['end'])
        calendar.loc[mask, 'is_ramadan'] = 1
    
    # Add Umrah season flags
    calendar['is_umrah_season'] = 0
    calendar['umrah_season_intensity'] = ''
    for _, umrah in umrah_periods.iterrows():
        mask = (calendar['date'] >= umrah['start']) & (calendar['date'] <= umrah['end'])
        calendar.loc[mask, 'is_umrah_season'] = 1
        calendar.loc[mask, 'umrah_season_intensity'] = umrah['intensity']
    
    # Add major event flags (separated by type)
    calendar = calendar.merge(
        events[['date', 'is_major_event', 'name', 'city', 'category']],
        on='date',
        how='left'
    )
    calendar['is_major_event'] = calendar['is_major_event'].fillna(0).astype(int)
    calendar['event_name'] = calendar['name'].fillna('')
    calendar['event_city'] = calendar['city'].fillna('')
    calendar['event_category'] = calendar['category'].fillna('')
    
    # Separate event types for better granularity
    calendar['is_hajj'] = ((calendar['event_name'].str.contains('Hajj', case=False, na=False)) & 
                           (calendar['event_category'] == 'religious')).astype(int)
    calendar['is_festival'] = (calendar['event_category'] == 'festival').astype(int)
    calendar['is_sports_event'] = (calendar['event_category'] == 'sports').astype(int)
    
    calendar.drop(['name', 'city', 'category'], axis=1, inplace=True)
    
    # Add holiday window features (days before/after holiday)
    calendar['days_to_holiday'] = -1
    calendar['days_from_holiday'] = -1
    
    holiday_dates = calendar[calendar['is_holiday'] == 1]['date'].values
    for holiday in holiday_dates:
        # Days to holiday (within 7 days)
        mask = (calendar['date'] < holiday) & (calendar['date'] >= holiday - pd.Timedelta(days=7))
        if mask.sum() > 0:
            calendar.loc[mask, 'days_to_holiday'] = (holiday - calendar.loc[mask, 'date']).dt.days
        
        # Days from holiday (within 3 days)
        mask = (calendar['date'] > holiday) & (calendar['date'] <= holiday + pd.Timedelta(days=3))
        if mask.sum() > 0:
            calendar.loc[mask, 'days_from_holiday'] = (calendar.loc[mask, 'date'] - holiday).dt.days
    
    logger.info(f"  ✓ Created calendar with {len(calendar)} days")
    logger.info(f"  ✓ Holidays: {calendar['is_holiday'].sum()} days")
    logger.info(f"  ✓ School vacations: {calendar['is_school_vacation'].sum()} days")
    logger.info(f"  ✓ Ramadan days: {calendar['is_ramadan'].sum()} days")
    logger.info(f"  ✓ Umrah season days: {calendar['is_umrah_season'].sum()} days")
    logger.info(f"  ✓ Hajj days: {calendar['is_hajj'].sum()} days")
    logger.info(f"  ✓ Festival days: {calendar['is_festival'].sum()} days")
    logger.info(f"  ✓ Sports events: {calendar['is_sports_event'].sum()} days")
    logger.info(f"  ✓ Major events (total): {calendar['is_major_event'].sum()} days")
    
    return calendar


def save_external_features():
    """
    Main function to fetch and save external features.
    """
    logger.info("=" * 80)
    logger.info("STEP 0-E: Fetching External Data")
    logger.info("=" * 80)
    
    try:
        # Create external features calendar
        logger.info("\n1. Creating external features calendar...")
        external_features = create_holiday_features()
        
        # Save to CSV
        logger.info("\n2. Saving external features...")
        output_path = config.EXTERNAL_FEATURES_FILE
        external_features.to_csv(output_path, index=False)
        
        logger.info(f"  ✓ External features saved: {output_path}")
        logger.info(f"  ✓ File size: {output_path.stat().st_size / 1024:.2f} KB")
        
        logger.info("\n" + "=" * 80)
        logger.info("STEP 0-E: COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"\nExternal features summary:")
        logger.info(f"  - Date range: {external_features['date'].min()} to {external_features['date'].max()}")
        logger.info(f"  - Total days: {len(external_features)}")
        logger.info(f"  - Features: {len(external_features.columns)}")
        
        # Print sample
        logger.info(f"\nSample external features:")
        print(external_features[external_features['is_holiday'] == 1].head(10))
        
        return external_features
    
    except Exception as e:
        logger.error(f"STEP 0-E FAILED: {str(e)}")
        raise


if __name__ == "__main__":
    # Fetch and save external features
    external_features = save_external_features()

