"""
Pydantic schemas for Feature Store - CHUNK 6
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FeatureStoreBuildRequest(BaseModel):
    """Request to build/rebuild the feature store."""
    tenant_id: int = Field(default=1, description="Tenant ID")
    start_date: date = Field(default=date(2023, 1, 1), description="Start date for data")
    end_date: Optional[date] = Field(default=None, description="End date for data (defaults to today)")


class FeatureStoreBuildResponse(BaseModel):
    """Response from feature store build operation."""
    tenant_id: int
    date_range: Dict[str, str]
    rows_inserted: int
    weather_updated: int
    calendar_updated: int
    events_updated: int
    lags_updated: int
    split_stats: Dict[str, int]
    final_stats: Dict[str, Any]


class ValidationCheck(BaseModel):
    """Single validation check result."""
    name: str
    passed: bool
    value: Any
    threshold: Optional[Any] = None


class FeatureStoreValidationResponse(BaseModel):
    """Response from feature store validation."""
    passed: bool
    checks: List[ValidationCheck]


class DailyDemandFeatures(BaseModel):
    """Feature row for ML training/inference."""
    demand_date: date
    branch_id: int
    category_id: int
    executed_rentals_count: int
    avg_base_price_paid: Optional[Decimal] = None
    utilization_contracts: Optional[Decimal] = None
    utilization_bookings: Optional[Decimal] = None
    temperature_avg: Optional[Decimal] = None
    precipitation_mm: Optional[Decimal] = None
    humidity_pct: Optional[Decimal] = None
    wind_speed_kmh: Optional[Decimal] = None
    is_weekend: bool = False
    is_public_holiday: bool = False
    is_religious_holiday: bool = False
    day_of_week: int
    day_of_month: int
    week_of_year: int
    month_of_year: int
    quarter: int
    event_score: Optional[Decimal] = None
    has_major_event: bool = False
    rentals_lag_1d: Optional[int] = None
    rentals_lag_7d: Optional[int] = None
    rentals_rolling_7d_avg: Optional[Decimal] = None
    rentals_rolling_30d_avg: Optional[Decimal] = None


class TrainingDataResponse(BaseModel):
    """Response containing training data for ML."""
    tenant_id: int
    split: str
    row_count: int
    features: List[Dict[str, Any]]


class FeatureStoreStatsResponse(BaseModel):
    """Statistics about the feature store."""
    total_rows: int
    date_range: Dict[str, str]
    split_distribution: Dict[str, int]
    target_stats: Dict[str, Any]
    feature_completeness: Dict[str, float]
    coverage: Dict[str, int]
