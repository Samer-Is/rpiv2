"""
Pydantic schemas for utilization endpoints
"""
from datetime import date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UtilizationResponse(BaseModel):
    """Response for utilization calculation"""
    branch_id: int = Field(..., description="Branch ID")
    category_id: int = Field(..., description="Car category ID")
    category_name: str = Field(..., description="Category name")
    calculation_date: date = Field(..., description="Date of calculation")
    rented_count: int = Field(..., description="Number of vehicles currently rented")
    available_count: int = Field(..., description="Number of vehicles available for rent")
    total_active_fleet: int = Field(..., description="Total active fleet (rented + available)")
    utilization: float = Field(..., description="Utilization rate (0.0 to 1.0)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "branch_id": 122,
                "category_id": 27,
                "category_name": "Compact",
                "calculation_date": "2025-05-31",
                "rented_count": 576,
                "available_count": 179,
                "total_active_fleet": 755,
                "utilization": 0.763
            }
        }


class FleetSnapshotResponse(BaseModel):
    """Response for fleet status breakdown"""
    branch_id: int = Field(..., description="Branch ID")
    category_id: int = Field(..., description="Category ID")
    status_id: int = Field(..., description="Vehicle status ID")
    status_name: str = Field(..., description="Status name")
    status_type: str = Field(..., description="Status classification: RENTED, AVAILABLE, EXCLUDED")
    vehicle_count: int = Field(..., description="Number of vehicles in this status")


class AllUtilizationsResponse(BaseModel):
    """Response for all utilizations"""
    calculation_date: date = Field(..., description="Date of calculation")
    tenant_id: int = Field(..., description="Tenant ID")
    utilizations: List[UtilizationResponse] = Field(..., description="List of utilization results")


class StatusConfigEntry(BaseModel):
    """Status configuration entry"""
    id: int = Field(..., description="Status ID")
    name: str = Field(..., description="Status name")


class StatusConfigSummaryResponse(BaseModel):
    """Summary of status configuration"""
    rented_statuses: List[StatusConfigEntry] = Field(..., description="Statuses that count as rented")
    available_statuses: List[StatusConfigEntry] = Field(..., description="Statuses that count as available")
    excluded_count: int = Field(..., description="Number of excluded statuses")


class StatusConfigUpdateRequest(BaseModel):
    """Request to update status configuration"""
    status_id: int = Field(..., description="Status ID to update")
    status_name: str = Field(..., description="Status name")
    status_type: str = Field(..., description="Status type: RENTED, AVAILABLE, or EXCLUDED")
    description: Optional[str] = Field(None, description="Optional description")
