"""
Recommendations API Router - CHUNK 9
Endpoints for generating, viewing, and managing pricing recommendations.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.db.session import get_app_db
from ..services.pricing_engine import PricingEngineService

router = APIRouter(prefix="/recommendations", tags=["Pricing Recommendations"])


# ============ Request/Response Models ============

class GenerateRequest(BaseModel):
    """Request to generate recommendations."""
    tenant_id: int = 1
    branch_id: Optional[int] = None  # If None, process all branches
    category_id: Optional[int] = None  # If None, process all categories
    start_date: Optional[date] = None  # Defaults to today
    horizon_days: int = 30


class GenerateResponse(BaseModel):
    """Response from generating recommendations."""
    tenant_id: int
    run_date: str
    branches_processed: int
    categories_processed: int
    recommendations_generated: int
    recommendations_saved: int
    errors: List[str]


class RecommendationItem(BaseModel):
    """Single recommendation item."""
    id: int
    forecast_date: date
    horizon_day: int
    
    # Base prices
    base_daily: float
    base_weekly: float
    base_monthly: float
    
    # Recommended prices
    rec_daily: float
    rec_weekly: float
    rec_monthly: float
    
    # Adjustment
    premium_discount_pct: float
    
    # Signals
    utilization_signal: Optional[float] = None
    forecast_signal: Optional[float] = None
    competitor_signal: Optional[float] = None
    weather_signal: Optional[float] = None
    holiday_signal: Optional[float] = None
    
    # Explanation
    explanation_text: Optional[str] = None
    guardrail_applied: bool = False
    
    # Status
    status: str = "pending"


class RecommendationsResponse(BaseModel):
    """Response containing recommendations for a branch/category."""
    tenant_id: int
    branch_id: int
    category_id: int
    branch_name: Optional[str] = None
    category_name: Optional[str] = None
    run_date: date
    recommendations: List[RecommendationItem]


class ApprovalRequest(BaseModel):
    """Request to approve/skip a recommendation."""
    user_id: str
    reason: Optional[str] = None


class BulkApprovalRequest(BaseModel):
    """Request to bulk approve recommendations."""
    tenant_id: int = 1
    branch_id: int
    category_id: int
    start_date: date
    end_date: date
    user_id: str


class ApprovalResponse(BaseModel):
    """Response from approval action."""
    success: bool
    message: str
    count: int = 1


class RecommendationSummary(BaseModel):
    """Summary statistics for recommendations."""
    tenant_id: int
    total_recommendations: int
    pending_count: int
    approved_count: int
    skipped_count: int
    branches_with_recs: int
    categories_with_recs: int
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    avg_adjustment_pct: Optional[float] = None


# ============ Endpoints ============

@router.post("/generate", response_model=GenerateResponse)
def generate_recommendations(
    request: GenerateRequest,
    db: Session = Depends(get_app_db)
):
    """
    Generate pricing recommendations for specified scope.
    
    If branch_id and category_id are not specified, generates for all
    MVP branches and categories.
    
    This operation:
    1. Fetches all signals (utilization, forecast, competitor, weather, holiday)
    2. Applies configurable weights to combine signals
    3. Applies guardrails to constrain adjustments
    4. Generates explanations
    5. Saves to database
    
    **Note**: This may take a few minutes for all branches/categories.
    """
    service = PricingEngineService(db)
    
    start_date = request.start_date or date.today()
    
    try:
        if request.branch_id and request.category_id:
            # Generate for specific branch/category
            recs = service.generate_recommendations(
                request.tenant_id,
                request.branch_id,
                request.category_id,
                start_date,
                request.horizon_days
            )
            
            saved = service.save_recommendations(
                request.tenant_id,
                request.branch_id,
                request.category_id,
                recs
            )
            
            return GenerateResponse(
                tenant_id=request.tenant_id,
                run_date=str(date.today()),
                branches_processed=1,
                categories_processed=1,
                recommendations_generated=len(recs),
                recommendations_saved=saved,
                errors=[]
            )
        else:
            # Generate for all MVP branches and categories
            stats = service.run_full_pipeline(
                request.tenant_id,
                start_date,
                request.horizon_days
            )
            
            return GenerateResponse(
                tenant_id=stats["tenant_id"],
                run_date=stats["run_date"],
                branches_processed=stats["branches_processed"],
                categories_processed=stats["categories_processed"],
                recommendations_generated=stats["recommendations_generated"],
                recommendations_saved=stats["recommendations_saved"],
                errors=stats["errors"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("", response_model=RecommendationsResponse)
def get_recommendations(
    branch_id: int = Query(..., description="Branch ID"),
    category_id: int = Query(..., description="Category ID"),
    start_date: Optional[date] = Query(default=None, description="Start date (defaults to today)"),
    run_date: Optional[date] = Query(default=None, description="Run date (defaults to latest)"),
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get pricing recommendations for a branch and category.
    
    Returns the 30-day recommendation window starting from start_date.
    If run_date is not specified, returns the latest recommendations.
    """
    if start_date is None:
        start_date = date.today()
    
    # Build query
    if run_date:
        query = text("""
            SELECT r.id, r.forecast_date, r.horizon_day,
                   r.base_daily, r.base_weekly, r.base_monthly,
                   r.rec_daily, r.rec_weekly, r.rec_monthly,
                   r.premium_discount_pct,
                   r.utilization_signal, r.forecast_signal, r.competitor_signal,
                   r.weather_signal, r.holiday_signal,
                   r.explanation_text, r.guardrail_applied, r.status,
                   r.run_date
            FROM dynamicpricing.recommendations_30d r
            WHERE r.tenant_id = :tenant_id
              AND r.branch_id = :branch_id
              AND r.category_id = :category_id
              AND r.run_date = :run_date
              AND r.forecast_date >= :start_date
            ORDER BY r.forecast_date
        """)
        params = {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "category_id": category_id,
            "run_date": run_date,
            "start_date": start_date
        }
    else:
        # Get latest run_date
        query = text("""
            SELECT r.id, r.forecast_date, r.horizon_day,
                   r.base_daily, r.base_weekly, r.base_monthly,
                   r.rec_daily, r.rec_weekly, r.rec_monthly,
                   r.premium_discount_pct,
                   r.utilization_signal, r.forecast_signal, r.competitor_signal,
                   r.weather_signal, r.holiday_signal,
                   r.explanation_text, r.guardrail_applied, r.status,
                   r.run_date
            FROM dynamicpricing.recommendations_30d r
            WHERE r.tenant_id = :tenant_id
              AND r.branch_id = :branch_id
              AND r.category_id = :category_id
              AND r.run_date = (
                  SELECT MAX(run_date) FROM dynamicpricing.recommendations_30d
                  WHERE tenant_id = :tenant_id AND branch_id = :branch_id AND category_id = :category_id
              )
              AND r.forecast_date >= :start_date
            ORDER BY r.forecast_date
        """)
        params = {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "category_id": category_id,
            "start_date": start_date
        }
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    if not rows:
        return RecommendationsResponse(
            tenant_id=tenant_id,
            branch_id=branch_id,
            category_id=category_id,
            run_date=run_date or date.today(),
            recommendations=[]
        )
    
    actual_run_date = rows[0][17]  # run_date column
    
    recommendations = [
        RecommendationItem(
            id=row[0],
            forecast_date=row[1],
            horizon_day=row[2],
            base_daily=float(row[3]),
            base_weekly=float(row[4]),
            base_monthly=float(row[5]),
            rec_daily=float(row[6]),
            rec_weekly=float(row[7]),
            rec_monthly=float(row[8]),
            premium_discount_pct=float(row[9]),
            utilization_signal=float(row[10]) if row[10] else None,
            forecast_signal=float(row[11]) if row[11] else None,
            competitor_signal=float(row[12]) if row[12] else None,
            weather_signal=float(row[13]) if row[13] else None,
            holiday_signal=float(row[14]) if row[14] else None,
            explanation_text=row[15],
            guardrail_applied=bool(row[16]),
            status=row[17] if isinstance(row[17], str) else "pending"
        )
        for row in rows
    ]
    
    # Get branch and category names
    names_result = db.execute(text("""
        SELECT b.Name as branch_name, c.CategoryNameEn as category_name
        FROM Rental.Branches b
        CROSS JOIN fleet.CarCategories c
        WHERE b.Id = :branch_id AND c.CategoryId = :category_id
    """), {"branch_id": branch_id, "category_id": category_id})
    names_row = names_result.fetchone()
    
    branch_name = None
    category_name = None
    if names_row:
        # Parse JSON for branch name
        import json
        try:
            branch_name_json = json.loads(names_row[0]) if names_row[0] else {}
            branch_name = branch_name_json.get("en", str(branch_id))
        except:
            branch_name = str(branch_id)
        category_name = names_row[1] if names_row[1] else str(category_id)
    
    return RecommendationsResponse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        category_id=category_id,
        branch_name=branch_name,
        category_name=category_name,
        run_date=actual_run_date,
        recommendations=recommendations
    )


@router.get("/summary", response_model=RecommendationSummary)
def get_recommendations_summary(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """Get summary statistics for recommendations."""
    result = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped,
            COUNT(DISTINCT branch_id) as branches,
            COUNT(DISTINCT category_id) as categories,
            MIN(forecast_date) as min_date,
            MAX(forecast_date) as max_date,
            AVG(premium_discount_pct) as avg_adj
        FROM dynamicpricing.recommendations_30d
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": tenant_id})
    
    row = result.fetchone()
    
    return RecommendationSummary(
        tenant_id=tenant_id,
        total_recommendations=row[0] or 0,
        pending_count=row[1] or 0,
        approved_count=row[2] or 0,
        skipped_count=row[3] or 0,
        branches_with_recs=row[4] or 0,
        categories_with_recs=row[5] or 0,
        date_range_start=row[6],
        date_range_end=row[7],
        avg_adjustment_pct=float(row[8]) if row[8] else None
    )


@router.post("/{recommendation_id}/approve", response_model=ApprovalResponse)
def approve_recommendation(
    recommendation_id: int,
    request: ApprovalRequest,
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """Approve a single recommendation."""
    service = PricingEngineService(db)
    
    success = service.approve_recommendation(
        recommendation_id,
        tenant_id,
        request.user_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return ApprovalResponse(
        success=True,
        message="Recommendation approved successfully"
    )


@router.post("/{recommendation_id}/skip", response_model=ApprovalResponse)
def skip_recommendation(
    recommendation_id: int,
    request: ApprovalRequest,
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """Skip (reject) a single recommendation."""
    service = PricingEngineService(db)
    
    success = service.skip_recommendation(
        recommendation_id,
        tenant_id,
        request.user_id,
        request.reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return ApprovalResponse(
        success=True,
        message="Recommendation skipped"
    )


@router.post("/bulk-approve", response_model=ApprovalResponse)
def bulk_approve_recommendations(
    request: BulkApprovalRequest,
    db: Session = Depends(get_app_db)
):
    """Bulk approve recommendations for a branch/category/date range."""
    service = PricingEngineService(db)
    
    count = service.bulk_approve(
        request.tenant_id,
        request.branch_id,
        request.category_id,
        request.start_date,
        request.end_date,
        request.user_id
    )
    
    return ApprovalResponse(
        success=True,
        message=f"Approved {count} recommendations",
        count=count
    )


@router.get("/by-date/{target_date}")
def get_all_recommendations_for_date(
    target_date: date,
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get all recommendations for a specific date across all branches/categories.
    Useful for daily review dashboard.
    """
    result = db.execute(text("""
        SELECT r.id, r.branch_id, r.category_id,
               r.base_daily, r.rec_daily, r.premium_discount_pct,
               r.explanation_text, r.status, r.guardrail_applied
        FROM dynamicpricing.recommendations_30d r
        WHERE r.tenant_id = :tenant_id
          AND r.forecast_date = :target_date
          AND r.run_date = (
              SELECT MAX(run_date) FROM dynamicpricing.recommendations_30d
              WHERE tenant_id = :tenant_id AND forecast_date = :target_date
          )
        ORDER BY r.branch_id, r.category_id
    """), {"tenant_id": tenant_id, "target_date": target_date})
    
    rows = result.fetchall()
    
    return {
        "tenant_id": tenant_id,
        "target_date": target_date.isoformat(),
        "count": len(rows),
        "recommendations": [
            {
                "id": row[0],
                "branch_id": row[1],
                "category_id": row[2],
                "base_daily": float(row[3]),
                "rec_daily": float(row[4]),
                "premium_discount_pct": float(row[5]),
                "explanation_text": row[6],
                "status": row[7],
                "guardrail_applied": bool(row[8])
            }
            for row in rows
        ]
    }


@router.get("/history")
def get_recommendation_history(
    branch_id: int = Query(..., description="Branch ID"),
    category_id: int = Query(..., description="Category ID"),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get historical recommendations with approval status.
    Shows how recommendations were acted upon over time.
    """
    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    
    result = db.execute(text("""
        SELECT r.run_date, r.forecast_date,
               r.base_daily, r.rec_daily, r.premium_discount_pct,
               r.status, r.approved_at, r.approved_by
        FROM dynamicpricing.recommendations_30d r
        WHERE r.tenant_id = :tenant_id
          AND r.branch_id = :branch_id
          AND r.category_id = :category_id
          AND r.forecast_date BETWEEN :start_date AND :end_date
        ORDER BY r.forecast_date, r.run_date
    """), {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "category_id": category_id,
        "start_date": start_date,
        "end_date": end_date
    })
    
    rows = result.fetchall()
    
    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "category_id": category_id,
        "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        "count": len(rows),
        "history": [
            {
                "run_date": row[0].isoformat() if row[0] else None,
                "forecast_date": row[1].isoformat() if row[1] else None,
                "base_daily": float(row[2]) if row[2] else None,
                "rec_daily": float(row[3]) if row[3] else None,
                "premium_discount_pct": float(row[4]) if row[4] else None,
                "status": row[5],
                "approved_at": row[6].isoformat() if row[6] else None,
                "approved_by": row[7]
            }
            for row in rows
        ]
    }
