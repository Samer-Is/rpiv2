"""
Utilization API Router
CHUNK 4: Endpoints for computing and managing fleet utilization
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from ..schemas.utilization import (
    UtilizationResponse,
    FleetSnapshotResponse,
    AllUtilizationsResponse,
    StatusConfigSummaryResponse,
    StatusConfigEntry,
    StatusConfigUpdateRequest
)
from ..services.utilization_service import UtilizationService, get_utilization_service

router = APIRouter(prefix="/utilization", tags=["Utilization"])


def get_service() -> UtilizationService:
    """Dependency to get UtilizationService instance"""
    return get_utilization_service(tenant_id=1)  # YELO tenant


@router.get(
    "/",
    response_model=AllUtilizationsResponse,
    summary="Get all utilizations",
    description="Returns utilization for all MVP branch × category combinations."
)
async def get_all_utilizations(
    calculation_date: Optional[date] = Query(None, description="Date for calculation (default=today)"),
    service: UtilizationService = Depends(get_service)
):
    """
    Get utilization for all MVP branches and categories.
    
    Returns utilization rate calculated as: Rented / (Rented + Available)
    
    - Rented status: 141 (Rented), 156 (In-Use)
    - Available status: 140 (Ready)
    - All other statuses are excluded from calculation
    """
    results = service.get_all_utilizations(calculation_date=calculation_date)
    
    return AllUtilizationsResponse(
        calculation_date=calculation_date or date.today(),
        tenant_id=1,
        utilizations=[
            UtilizationResponse(
                branch_id=r.branch_id,
                category_id=r.category_id,
                category_name=r.category_name,
                calculation_date=r.calculation_date,
                rented_count=r.rented_count,
                available_count=r.available_count,
                total_active_fleet=r.total_active_fleet,
                utilization=r.utilization
            )
            for r in results
        ]
    )


@router.get(
    "/branch/{branch_id}/category/{category_id}",
    response_model=UtilizationResponse,
    summary="Get utilization for specific branch × category",
    description="Returns utilization for a specific branch and category combination."
)
async def get_utilization(
    branch_id: int,
    category_id: int,
    calculation_date: Optional[date] = Query(None, description="Date for calculation (default=today)"),
    service: UtilizationService = Depends(get_service)
):
    """
    Get utilization for a specific branch × category.
    
    - **branch_id**: The branch ID
    - **category_id**: The car category ID
    - **calculation_date**: Optional date for calculation
    """
    result = service.get_utilization_for_branch_category(
        branch_id, 
        category_id, 
        calculation_date
    )
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active fleet found for branch {branch_id}, category {category_id}"
        )
    
    return UtilizationResponse(
        branch_id=result.branch_id,
        category_id=result.category_id,
        category_name=result.category_name,
        calculation_date=result.calculation_date,
        rented_count=result.rented_count,
        available_count=result.available_count,
        total_active_fleet=result.total_active_fleet,
        utilization=result.utilization
    )


@router.get(
    "/snapshot",
    response_model=List[FleetSnapshotResponse],
    summary="Get fleet status snapshot",
    description="Returns detailed breakdown of vehicles by status."
)
async def get_fleet_snapshot(
    branch_id: Optional[int] = Query(None, description="Filter by branch ID"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    service: UtilizationService = Depends(get_service)
):
    """
    Get detailed fleet status breakdown.
    
    Shows how many vehicles are in each status (Rented, Ready, Maintenance, etc.)
    """
    results = service.get_fleet_snapshot(branch_id, category_id)
    
    return [
        FleetSnapshotResponse(
            branch_id=r.branch_id,
            category_id=r.category_id,
            status_id=r.status_id,
            status_name=r.status_name,
            status_type=r.status_type,
            vehicle_count=r.vehicle_count
        )
        for r in results
    ]


@router.get(
    "/config",
    response_model=StatusConfigSummaryResponse,
    summary="Get status configuration",
    description="Returns current status configuration for utilization calculation."
)
async def get_status_config(
    service: UtilizationService = Depends(get_service)
):
    """
    Get the current status configuration.
    
    Shows which vehicle statuses count as 'rented', 'available', or 'excluded'.
    """
    config = service.get_status_config_summary()
    
    return StatusConfigSummaryResponse(
        rented_statuses=[
            StatusConfigEntry(id=s['id'], name=s['name']) 
            for s in config['rented_statuses']
        ],
        available_statuses=[
            StatusConfigEntry(id=s['id'], name=s['name']) 
            for s in config['available_statuses']
        ],
        excluded_count=len(config['excluded_statuses'])
    )


@router.get(
    "/summary",
    summary="Get utilization summary",
    description="Returns a quick summary of utilization across all MVP branches."
)
async def get_utilization_summary(
    service: UtilizationService = Depends(get_service)
):
    """
    Quick summary endpoint for validation.
    Returns utilization statistics across MVP branches and categories.
    """
    results = service.get_all_utilizations()
    
    if not results:
        return {"error": "No utilization data available"}
    
    utilizations = [r.utilization for r in results]
    
    summary = {
        "calculation_date": date.today().isoformat(),
        "tenant_id": 1,
        "total_combinations": len(results),
        "total_rented": sum(r.rented_count for r in results),
        "total_available": sum(r.available_count for r in results),
        "total_active_fleet": sum(r.total_active_fleet for r in results),
        "overall_utilization": sum(r.rented_count for r in results) / sum(r.total_active_fleet for r in results) if sum(r.total_active_fleet for r in results) > 0 else 0,
        "statistics": {
            "min_utilization": min(utilizations),
            "max_utilization": max(utilizations),
            "avg_utilization": sum(utilizations) / len(utilizations),
        },
        "by_branch": {}
    }
    
    # Group by branch
    branch_data = {}
    for r in results:
        if r.branch_id not in branch_data:
            branch_data[r.branch_id] = {
                'rented': 0,
                'available': 0,
                'total': 0
            }
        branch_data[r.branch_id]['rented'] += r.rented_count
        branch_data[r.branch_id]['available'] += r.available_count
        branch_data[r.branch_id]['total'] += r.total_active_fleet
    
    for branch_id, data in branch_data.items():
        summary['by_branch'][branch_id] = {
            'rented': data['rented'],
            'available': data['available'],
            'total': data['total'],
            'utilization': round(data['rented'] / data['total'], 3) if data['total'] > 0 else 0
        }
    
    return summary
