"""
Competitor Pricing API Router - CHUNK 8
Endpoints for competitor pricing and competitor index
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from ..database import get_app_db
from ..services.competitor_service import CompetitorPricingService

router = APIRouter(prefix="/competitors", tags=["Competitor Pricing"])


class CompetitorMappingItem(BaseModel):
    """Single competitor mapping."""
    category_id: int
    category_name: str
    competitor_vehicle_type: str
    weight: float = 1.0
    is_active: bool = True


class CompetitorMappingResponse(BaseModel):
    """Response containing all competitor mappings."""
    tenant_id: int
    mappings: List[CompetitorMappingItem]


class CompetitorPriceItem(BaseModel):
    """Single competitor price."""
    competitor_name: str
    vehicle_type: str
    daily_price: float
    weekly_price: Optional[float] = None
    monthly_price: Optional[float] = None
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_name: Optional[str] = None


class CompetitorVehicleItem(BaseModel):
    """Single competitor vehicle with full details."""
    vehicle_name: str
    brand: str
    model: str
    category: str
    daily_price: float
    seats: Optional[int] = None
    doors: Optional[int] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    bags_large: Optional[int] = None
    bags_small: Optional[int] = None
    supplier: Optional[str] = None


class CompetitorVehiclesResponse(BaseModel):
    """Response containing competitor vehicles."""
    branch_id: int
    city: str
    pickup_date: date
    dropoff_date: date
    vehicles_count: int
    brands_available: List[str]
    models_available: List[str]
    categories_available: List[str]
    vehicles: List[CompetitorVehicleItem]


class CompetitorPricesResponse(BaseModel):
    """Response containing competitor prices."""
    tenant_id: int
    branch_id: int
    category_id: int
    city: str
    price_date: date
    prices: List[CompetitorPriceItem]


class CompetitorIndexResponse(BaseModel):
    """Competitor index for a category."""
    tenant_id: int
    branch_id: int
    category_id: int
    index_date: date
    avg_price: float
    min_price: float
    max_price: float
    competitors_count: int
    our_base_price: Optional[float] = None
    price_position: Optional[float] = None


class BuildIndexRequest(BaseModel):
    """Request to build competitor index."""
    tenant_id: int = 1
    start_date: date
    end_date: date


class BuildIndexResponse(BaseModel):
    """Response from building competitor index."""
    branches: int
    categories: int
    dates_processed: int
    indexes_created: int


@router.get("/mapping", response_model=CompetitorMappingResponse)
def get_competitor_mapping(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get category to competitor vehicle type mapping.
    
    This mapping defines how our internal categories map to competitor
    vehicle types for price comparison.
    """
    result = db.execute(text("""
        SELECT category_id, category_name, competitor_vehicle_type, weight, is_active
        FROM appconfig.competitor_mapping
        WHERE tenant_id = :tenant_id
        ORDER BY category_id
    """), {"tenant_id": tenant_id})
    
    mappings = [
        CompetitorMappingItem(
            category_id=row[0],
            category_name=row[1],
            competitor_vehicle_type=row[2],
            weight=float(row[3]),
            is_active=bool(row[4])
        )
        for row in result.fetchall()
    ]
    
    return CompetitorMappingResponse(tenant_id=tenant_id, mappings=mappings)


@router.post("/mapping")
def update_competitor_mapping(
    mapping: CompetitorMappingItem,
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Update or create a competitor mapping.
    
    Maps internal category to competitor vehicle type.
    """
    try:
        db.execute(text("""
            MERGE INTO appconfig.competitor_mapping AS target
            USING (SELECT :tenant_id as tenant_id, :category_id as category_id) AS source
            ON target.tenant_id = source.tenant_id 
               AND target.category_id = source.category_id
            WHEN MATCHED THEN
                UPDATE SET category_name = :category_name,
                           competitor_vehicle_type = :vehicle_type,
                           weight = :weight,
                           is_active = :is_active,
                           updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (tenant_id, category_id, category_name, competitor_vehicle_type, weight, is_active)
                VALUES (:tenant_id, :category_id, :category_name, :vehicle_type, :weight, :is_active);
        """), {
            "tenant_id": tenant_id,
            "category_id": mapping.category_id,
            "category_name": mapping.category_name,
            "vehicle_type": mapping.competitor_vehicle_type,
            "weight": mapping.weight,
            "is_active": mapping.is_active
        })
        db.commit()
        return {"message": "Mapping updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mapping: {str(e)}")


@router.get("/prices", response_model=CompetitorPricesResponse)
def get_competitor_prices(
    branch_id: int = Query(..., description="Branch ID"),
    category_id: int = Query(..., description="Category ID"),
    price_date: Optional[date] = Query(default=None, description="Price date (defaults to today)"),
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get competitor prices for a specific branch and category.
    
    Returns prices from multiple competitors for comparison.
    """
    if price_date is None:
        price_date = date.today()
    
    service = CompetitorPricingService(db)
    
    # Get category mapping
    mapping = service.get_category_mapping(tenant_id)
    vehicle_type = mapping.get(category_id, "economy")
    
    # Get city for branch
    city = service.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
    
    # Fetch prices
    prices = service.fetch_competitor_prices(city, vehicle_type, price_date)
    
    # Save to cache
    service.save_competitor_prices(tenant_id, branch_id, category_id, prices, price_date)
    
    return CompetitorPricesResponse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        category_id=category_id,
        city=city,
        price_date=price_date,
        prices=[
            CompetitorPriceItem(
                competitor_name=p.competitor_name,
                vehicle_type=p.vehicle_type,
                daily_price=float(p.daily_price),
                weekly_price=float(p.weekly_price) if p.weekly_price else None,
                monthly_price=float(p.monthly_price) if p.monthly_price else None
            )
            for p in prices
        ]
    )


@router.get("/index", response_model=CompetitorIndexResponse)
def get_competitor_index(
    branch_id: int = Query(..., description="Branch ID"),
    category_id: int = Query(..., description="Category ID"),
    index_date: Optional[date] = Query(default=None, description="Index date (defaults to today)"),
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get competitor index for a specific branch and category.
    
    The competitor index is the average price of the top 3 competitors.
    """
    if index_date is None:
        index_date = date.today()
    
    service = CompetitorPricingService(db)
    
    # Try to get from database first
    index = service.get_competitor_index(tenant_id, branch_id, category_id, index_date)
    
    if index is None:
        # Calculate fresh
        index = service.calculate_competitor_index(
            tenant_id, branch_id, category_id, index_date
        )
        # Save for future queries
        service.save_competitor_index(tenant_id, branch_id, index)
    
    return CompetitorIndexResponse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        category_id=index.category_id,
        index_date=index.index_date,
        avg_price=float(index.avg_price),
        min_price=float(index.min_price),
        max_price=float(index.max_price),
        competitors_count=index.competitors_count,
        our_base_price=float(index.our_base_price) if index.our_base_price else None,
        price_position=float(index.price_position) if index.price_position else None
    )


@router.post("/index/build", response_model=BuildIndexResponse)
def build_competitor_index(
    request: BuildIndexRequest,
    db: Session = Depends(get_app_db)
):
    """
    Build competitor index for a date range.
    
    Calculates and stores competitor index for all MVP branches and categories.
    """
    service = CompetitorPricingService(db)
    
    try:
        stats = service.build_competitor_index_for_date_range(
            tenant_id=request.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return BuildIndexResponse(
            branches=stats["branches"],
            categories=stats["categories"],
            dates_processed=stats["dates_processed"],
            indexes_created=stats["indexes_created"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build index: {str(e)}")


@router.get("/summary")
def get_competitor_summary(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """Get summary of competitor data."""
    # Get mapping count
    mapping_count = db.execute(text("""
        SELECT COUNT(*) FROM appconfig.competitor_mapping
        WHERE tenant_id = :tenant_id AND is_active = 1
    """), {"tenant_id": tenant_id}).scalar()
    
    # Get cached prices count
    prices_count = db.execute(text("""
        SELECT COUNT(*) FROM dynamicpricing.competitor_prices
        WHERE tenant_id = :tenant_id AND expires_at > GETDATE()
    """), {"tenant_id": tenant_id}).scalar()
    
    # Get index count
    index_count = db.execute(text("""
        SELECT COUNT(*), MIN(index_date), MAX(index_date)
        FROM dynamicpricing.competitor_index
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": tenant_id}).fetchone()
    
    # Get average competitor price by category
    avg_by_category = db.execute(text("""
        SELECT category_id, AVG(competitor_avg_price) as avg_price
        FROM dynamicpricing.competitor_index
        WHERE tenant_id = :tenant_id
        GROUP BY category_id
    """), {"tenant_id": tenant_id}).fetchall()
    
    return {
        "tenant_id": tenant_id,
        "active_mappings": mapping_count,
        "cached_prices": prices_count,
        "index_records": index_count[0] if index_count else 0,
        "index_date_range": {
            "min": index_count[1] if index_count and index_count[1] else None,
            "max": index_count[2] if index_count and index_count[2] else None
        },
        "avg_competitor_price_by_category": {
            row[0]: float(row[1]) for row in avg_by_category
        } if avg_by_category else {}
    }


@router.get("/live")
def get_live_competitor_prices(
    branch_id: int = Query(..., description="Branch ID"),
    price_date: Optional[date] = Query(default=None, description="Price date (defaults to today)"),
    db: Session = Depends(get_app_db)
):
    """
    Fetch LIVE competitor prices from Booking.com API.
    
    This endpoint calls the real Booking.com API via RapidAPI.
    Results are organized by Renty category.
    
    Note: This may take a few seconds as it makes an external API call.
    """
    if price_date is None:
        price_date = date.today()
    
    service = CompetitorPricingService(db)
    
    try:
        prices = service.fetch_live_competitor_prices(branch_id, price_date)
        
        return {
            "branch_id": branch_id,
            "price_date": price_date,
            "source": "booking.com",
            "categories": prices
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch live prices: {str(e)}"
        )


@router.get("/vehicles", response_model=CompetitorVehiclesResponse)
def get_competitor_vehicles(
    branch_id: int = Query(..., description="Branch ID"),
    pickup_date: Optional[date] = Query(default=None, description="Pickup date (defaults to today)"),
    dropoff_date: Optional[date] = Query(default=None, description="Dropoff date (defaults to pickup + 3 days)"),
    db: Session = Depends(get_app_db)
):
    """
    Fetch ALL competitor vehicles with brand, model, and category information.
    
    This endpoint returns detailed vehicle information from Booking.com API,
    including extracted brand and model names, not just categories.
    
    Returns:
    - Full vehicle list with brand, model, category
    - Aggregated lists of available brands, models, and categories
    - Vehicle specifications (seats, doors, transmission, fuel type)
    
    Note: This may take a few seconds as it makes an external API call.
    """
    if pickup_date is None:
        pickup_date = date.today()
    if dropoff_date is None:
        dropoff_date = pickup_date + timedelta(days=3)
    
    service = CompetitorPricingService(db)
    city = service.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
    
    try:
        vehicles = service.fetch_all_competitor_vehicles(city, pickup_date, dropoff_date)
        
        # Extract unique brands, models, and categories
        brands = sorted(set(v["brand"] for v in vehicles if v["brand"] != "Unknown"))
        models = sorted(set(v["model"] for v in vehicles if v["model"] != "Unknown"))
        categories = sorted(set(v["category"] for v in vehicles))
        
        return CompetitorVehiclesResponse(
            branch_id=branch_id,
            city=city,
            pickup_date=pickup_date,
            dropoff_date=dropoff_date,
            vehicles_count=len(vehicles),
            brands_available=brands,
            models_available=models,
            categories_available=categories,
            vehicles=[
                CompetitorVehicleItem(
                    vehicle_name=v["vehicle_name"],
                    brand=v["brand"],
                    model=v["model"],
                    category=v["category"],
                    daily_price=v["daily_price"],
                    seats=v.get("seats"),
                    doors=v.get("doors"),
                    transmission=v.get("transmission"),
                    fuel_type=v.get("fuel_type"),
                    bags_large=v.get("bags_large"),
                    bags_small=v.get("bags_small"),
                    supplier=v.get("supplier")
                )
                for v in vehicles
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch vehicles: {str(e)}"
        )


@router.get("/brands")
def get_available_brands(
    branch_id: int = Query(..., description="Branch ID"),
    pickup_date: Optional[date] = Query(default=None, description="Pickup date (defaults to today)"),
    db: Session = Depends(get_app_db)
):
    """
    Get list of available car brands from competitors.
    
    Returns a summary of brands and their vehicle counts.
    """
    if pickup_date is None:
        pickup_date = date.today()
    dropoff_date = pickup_date + timedelta(days=3)
    
    service = CompetitorPricingService(db)
    city = service.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
    
    try:
        vehicles = service.fetch_all_competitor_vehicles(city, pickup_date, dropoff_date)
        
        # Count vehicles by brand
        brand_counts = {}
        brand_prices = {}
        for v in vehicles:
            brand = v["brand"]
            if brand not in brand_counts:
                brand_counts[brand] = 0
                brand_prices[brand] = []
            brand_counts[brand] += 1
            brand_prices[brand].append(v["daily_price"])
        
        # Calculate average prices
        brands_summary = []
        for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
            prices = brand_prices[brand]
            brands_summary.append({
                "brand": brand,
                "vehicle_count": count,
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": round(sum(prices) / len(prices), 2)
            })
        
        return {
            "branch_id": branch_id,
            "city": city,
            "pickup_date": pickup_date,
            "total_brands": len(brand_counts),
            "total_vehicles": len(vehicles),
            "brands": brands_summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch brands: {str(e)}"
        )

