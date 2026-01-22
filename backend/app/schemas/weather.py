"""
Weather API Schemas
Pydantic models for weather endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class WeatherDataResponse(BaseModel):
    """Weather data for a single date"""
    weather_date: date
    city_name: str
    t_mean: float
    t_max: float
    t_min: float
    wind_max: float
    precipitation_sum: float
    weather_code: int
    bad_weather_score: float = Field(ge=0, le=1)
    extreme_heat_flag: int = Field(ge=0, le=1)


class WeatherSummaryResponse(BaseModel):
    """Summary of weather data in database"""
    total_rows: int
    branch_count: int
    min_date: Optional[str]
    max_date: Optional[str]
    forecast_rows: int
    historical_rows: int


class BranchLocationResponse(BaseModel):
    """Branch location for weather lookup"""
    branch_id: int
    city_name: str
    latitude: float
    longitude: float


class WeatherFetchResponse(BaseModel):
    """Response from weather fetch operation"""
    branches_processed: int
    days_per_branch: dict


class CalendarFeaturesResponse(BaseModel):
    """Calendar and event features for a date/city"""
    date: str
    city: str
    is_holiday: int
    holiday_name: Optional[str]
    holiday_type: Optional[str]
    is_weekend: int
    event_score_today: float
    event_score_3d_avg: float
    event_score_7d_avg: float
    event_volume_today: int


class HolidayWindowResponse(BaseModel):
    """Holiday window info"""
    days_to_next_holiday: int
    days_since_last_holiday: int
    next_holiday_name: Optional[str]
    holidays_in_window: int


class HolidaySummaryResponse(BaseModel):
    """Summary of holiday data"""
    total: int
    min_date: Optional[str]
    max_date: Optional[str]
    years: int


class EventSummaryResponse(BaseModel):
    """Summary of event data"""
    total: int
    min_date: Optional[str]
    max_date: Optional[str]
    cities: int
