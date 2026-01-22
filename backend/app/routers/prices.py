"""
Base Price API Router
CHUNK 3: Endpoints for retrieving base rental prices
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from ..schemas.base_price import (
    BasePriceResponse,
    ModelPriceResponse,
    CategoryPriceSummary,
    AllCategoryPricesResponse,
    MVPCategoryPricesResponse,
    BasePriceRequest
)
from ..services.base_rate_service import BaseRateService, get_base_rate_service

router = APIRouter(prefix="/prices", tags=["Base Prices"])


def get_service() -> BaseRateService:
    """Dependency to get BaseRateService instance"""
    return get_base_rate_service(tenant_id=1)  # YELO tenant


@router.get(
    "/base",
    response_model=BasePriceResponse,
    summary="Get base price for branch × category",
    description="Returns the base daily/weekly/monthly rates for a specific branch and category combination."
)
async def get_base_price(
    branch_id: int = Query(..., description="Branch ID", ge=1),
    category_id: int = Query(..., description="Car category ID", ge=1),
    effective_date: date = Query(..., description="Date to get prices for (YYYY-MM-DD)"),
    service: BaseRateService = Depends(get_service)
):
    """
    Get base prices for a branch × category combination.
    
    - **branch_id**: The branch ID (e.g., 122 for Riyadh Airport)
    - **category_id**: The car category ID (e.g., 27 for Compact)
    - **effective_date**: The date for which to retrieve prices
    
    Returns average prices across all models in the category.
    Falls back to default rates if no branch-specific rates exist.
    """
    result = service.get_base_prices_for_category(branch_id, category_id, effective_date)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No prices found for branch {branch_id}, category {category_id} on {effective_date}"
        )
    
    return BasePriceResponse(
        branch_id=result.branch_id,
        category_id=result.category_id,
        category_name=result.category_name,
        effective_date=result.effective_date,
        daily_rate=result.daily_rate,
        weekly_rate=result.weekly_rate,
        monthly_rate=result.monthly_rate,
        model_count=result.model_count,
        source=result.source
    )


@router.post(
    "/base",
    response_model=BasePriceResponse,
    summary="Get base price (POST)",
    description="Same as GET /prices/base but accepts JSON body."
)
async def get_base_price_post(
    request: BasePriceRequest,
    service: BaseRateService = Depends(get_service)
):
    """Get base prices via POST request with JSON body."""
    result = service.get_base_prices_for_category(
        request.branch_id,
        request.category_id,
        request.effective_date
    )
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No prices found for branch {request.branch_id}, category {request.category_id} on {request.effective_date}"
        )
    
    return BasePriceResponse(
        branch_id=result.branch_id,
        category_id=result.category_id,
        category_name=result.category_name,
        effective_date=result.effective_date,
        daily_rate=result.daily_rate,
        weekly_rate=result.weekly_rate,
        monthly_rate=result.monthly_rate,
        model_count=result.model_count,
        source=result.source
    )


@router.get(
    "/models",
    response_model=List[ModelPriceResponse],
    summary="Get prices for all models in a category",
    description="Returns individual model prices for a category."
)
async def get_model_prices(
    category_id: int = Query(..., description="Car category ID", ge=1),
    effective_date: date = Query(..., description="Date to get prices for (YYYY-MM-DD)"),
    branch_id: Optional[int] = Query(None, description="Optional branch ID (None for default rates)"),
    service: BaseRateService = Depends(get_service)
):
    """
    Get prices for all models in a category.
    
    - **category_id**: The car category ID
    - **effective_date**: The date for which to retrieve prices
    - **branch_id**: Optional branch ID (omit for default rates)
    
    Returns a list of all models with their daily/weekly/monthly rates.
    """
    results = service.get_model_prices(category_id, effective_date, branch_id)
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No model prices found for category {category_id} on {effective_date}"
        )
    
    return [
        ModelPriceResponse(
            model_id=r.model_id,
            model_name=r.model_name,
            category_id=r.category_id,
            category_name=r.category_name,
            daily_rate=r.daily_rate,
            weekly_rate=r.weekly_rate,
            monthly_rate=r.monthly_rate
        )
        for r in results
    ]


@router.get(
    "/categories",
    response_model=AllCategoryPricesResponse,
    summary="Get prices for all categories",
    description="Returns average base prices for all categories."
)
async def get_all_category_prices(
    effective_date: date = Query(..., description="Date to get prices for (YYYY-MM-DD)"),
    service: BaseRateService = Depends(get_service)
):
    """
    Get base prices for all categories.
    
    Returns average prices across all models in each category.
    Uses default rates (not branch-specific).
    """
    results = service.get_all_category_prices(effective_date)
    
    categories = [
        CategoryPriceSummary(
            category_id=cat_id,
            category_name=info['category_name'],
            model_count=info['model_count'],
            daily_rate=info['daily_rate'],
            weekly_rate=info['weekly_rate'],
            monthly_rate=info['monthly_rate']
        )
        for cat_id, info in results.items()
    ]
    
    return AllCategoryPricesResponse(
        effective_date=effective_date,
        categories=categories
    )


@router.get(
    "/mvp-categories",
    response_model=MVPCategoryPricesResponse,
    summary="Get prices for MVP categories",
    description="Returns base prices for the 6 MVP categories only."
)
async def get_mvp_category_prices(
    effective_date: date = Query(..., description="Date to get prices for (YYYY-MM-DD)"),
    service: BaseRateService = Depends(get_service)
):
    """
    Get base prices for MVP categories only.
    
    MVP Categories:
    - 1: Economy
    - 2: Small Sedan
    - 3: Intermediate Sedan
    - 13: Intermediate SUV
    - 27: Compact
    - 29: Economy SUV
    
    Returns average prices across all models in each category.
    """
    results = service.get_mvp_category_prices(effective_date)
    
    categories = {
        cat_id: CategoryPriceSummary(
            category_id=cat_id,
            category_name=info['category_name'],
            model_count=info['model_count'],
            daily_rate=info['daily_rate'],
            weekly_rate=info['weekly_rate'],
            monthly_rate=info['monthly_rate']
        )
        for cat_id, info in results.items()
    }
    
    return MVPCategoryPricesResponse(
        effective_date=effective_date,
        tenant_id=1,  # YELO
        categories=categories
    )


@router.get(
    "/summary",
    summary="Get base price summary",
    description="Returns a quick summary of base prices for validation."
)
async def get_price_summary(
    effective_date: date = Query(date(2025, 5, 31), description="Date to get prices for"),
    service: BaseRateService = Depends(get_service)
):
    """
    Quick summary endpoint for validation.
    Returns MVP category prices with statistics.
    """
    results = service.get_mvp_category_prices(effective_date)
    
    summary = {
        "effective_date": effective_date.isoformat(),
        "tenant_id": 1,
        "categories_found": len(results),
        "total_models": sum(info['model_count'] for info in results.values()),
        "price_ranges": {}
    }
    
    for cat_id, info in results.items():
        summary["price_ranges"][info['category_name']] = {
            "daily": f"{info['daily_rate']:.2f} SAR" if info['daily_rate'] else "N/A",
            "weekly": f"{info['weekly_rate']:.2f} SAR" if info['weekly_rate'] else "N/A",
            "monthly": f"{info['monthly_rate']:.2f} SAR" if info['monthly_rate'] else "N/A",
            "models": info['model_count']
        }
    
    return summary
