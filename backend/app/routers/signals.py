"""
External Signals API Router
CHUNK 5: Endpoints for weather, holidays, and events data.
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import date, timedelta
from typing import List, Optional
import sys

# Add ksa_calendar_pipeline to path
sys.path.insert(0, str(__file__).replace('backend\\app\\routers\\signals.py', ''))

from app.core.config import settings
from app.services.weather_service import WeatherService
from app.schemas.weather import (
    WeatherDataResponse,
    WeatherSummaryResponse,
    BranchLocationResponse,
    WeatherFetchResponse,
    CalendarFeaturesResponse,
    HolidayWindowResponse,
    HolidaySummaryResponse,
    EventSummaryResponse
)

router = APIRouter(prefix="/signals", tags=["External Signals"])

# Connection string for services
CONN_STR = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={settings.sql_server};"
    f"Database={settings.sql_database};"
    f"Trusted_Connection=yes;"
)


@router.get("/weather/summary", response_model=WeatherSummaryResponse)
def get_weather_summary():
    """Get summary of weather data in database"""
    service = WeatherService(CONN_STR)
    summary = service.get_weather_summary()
    return summary


@router.get("/weather/locations", response_model=List[BranchLocationResponse])
def get_branch_locations():
    """Get all branch locations with coordinates"""
    service = WeatherService(CONN_STR)
    locations = service.get_branch_locations()
    return locations


@router.get("/weather/branch/{branch_id}")
def get_weather_for_branch(
    branch_id: int,
    start_date: date = Query(default=None),
    end_date: date = Query(default=None)
):
    """Get weather data for a specific branch"""
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=30)
    
    service = WeatherService(CONN_STR)
    data = service.get_weather_for_date_range(branch_id, start_date, end_date)
    
    return {
        "branch_id": branch_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "count": len(data),
        "data": [
            {
                "weather_date": w.weather_date.isoformat(),
                "city_name": w.city_name,
                "t_mean": w.t_mean,
                "t_max": w.t_max,
                "t_min": w.t_min,
                "wind_max": w.wind_max,
                "precipitation_sum": w.precipitation_sum,
                "weather_code": w.weather_code,
                "bad_weather_score": w.bad_weather_score,
                "extreme_heat_flag": w.extreme_heat_flag
            }
            for w in data
        ]
    }


@router.post("/weather/fetch-forecast", response_model=WeatherFetchResponse)
def fetch_forecast_weather(
    branch_ids: Optional[List[int]] = None
):
    """Fetch and store forecast weather for branches"""
    service = WeatherService(CONN_STR)
    results = service.update_forecast_weather(branch_ids)
    return {
        "branches_processed": len(results),
        "days_per_branch": results
    }


@router.get("/calendar/features", response_model=CalendarFeaturesResponse)
def get_calendar_features(
    query_date: date = Query(default=None),
    city: str = Query(default="Riyadh")
):
    """Get calendar/event features for a date and city"""
    if query_date is None:
        query_date = date.today()
    
    try:
        from ksa_calendar_pipeline.feature_builder import build_features
        features = build_features(query_date, city)
        return features
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/holiday-window", response_model=HolidayWindowResponse)
def get_holiday_window(
    query_date: date = Query(default=None),
    window_days: int = Query(default=7)
):
    """Get holiday information within a window around a date"""
    if query_date is None:
        query_date = date.today()
    
    try:
        from ksa_calendar_pipeline.feature_builder import get_holiday_window as get_window
        window = get_window(query_date, window_days)
        return window
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/holidays/summary", response_model=HolidaySummaryResponse)
def get_holidays_summary():
    """Get summary of holiday data in database"""
    try:
        from ksa_calendar_pipeline.db import get_holidays_count
        summary = get_holidays_count()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/summary", response_model=EventSummaryResponse)
def get_events_summary():
    """Get summary of event data in database"""
    try:
        from ksa_calendar_pipeline.db import get_events_count
        summary = get_events_count()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/backfill-holidays")
def backfill_holidays(
    start_year: int = Query(default=2023),
    end_year: int = Query(default=2027)
):
    """Backfill holidays for a year range"""
    try:
        from ksa_calendar_pipeline.backfill import backfill_holidays as do_backfill
        count = do_backfill(start_year, end_year)
        return {"status": "success", "holidays_backfilled": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/external-signals/combined")
def get_combined_external_signals(
    branch_id: int,
    query_date: date = Query(default=None)
):
    """
    Get combined external signals for a branch and date.
    Returns weather + calendar features in a single response.
    """
    if query_date is None:
        query_date = date.today()
    
    # Get weather
    weather_service = WeatherService(CONN_STR)
    weather_data = weather_service.get_weather_for_date_range(
        branch_id, query_date, query_date
    )
    
    # Get branch city
    locations = weather_service.get_branch_locations()
    city = "Riyadh"  # default
    for loc in locations:
        if loc["branch_id"] == branch_id:
            city = loc["city_name"]
            break
    
    # Get calendar features
    try:
        from ksa_calendar_pipeline.feature_builder import build_features
        calendar_features = build_features(query_date, city)
    except:
        calendar_features = {}
    
    weather_dict = {}
    if weather_data:
        w = weather_data[0]
        weather_dict = {
            "t_mean": w.t_mean,
            "t_max": w.t_max,
            "t_min": w.t_min,
            "wind_max": w.wind_max,
            "bad_weather_score": w.bad_weather_score,
            "extreme_heat_flag": w.extreme_heat_flag
        }
    
    return {
        "branch_id": branch_id,
        "date": query_date.isoformat(),
        "city": city,
        "weather": weather_dict,
        "calendar": calendar_features
    }
