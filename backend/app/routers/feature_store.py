"""
Feature Store API Router - CHUNK 6
Endpoints for building and managing the ML feature store
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_app_db
from ..services.feature_store_service import FeatureStoreService
from ..schemas.feature_store import (
    FeatureStoreBuildRequest,
    FeatureStoreBuildResponse,
    FeatureStoreValidationResponse,
    TrainingDataResponse,
    FeatureStoreStatsResponse
)

router = APIRouter(prefix="/feature-store", tags=["Feature Store"])


@router.post("/build", response_model=FeatureStoreBuildResponse)
def build_feature_store(
    request: FeatureStoreBuildRequest,
    db: Session = Depends(get_app_db)
):
    """
    Build or rebuild the feature store for a tenant.
    
    This operation:
    1. Aggregates contract data into daily demand by branch×category
    2. Joins with weather features
    3. Joins with calendar/holiday features
    4. Joins with event features
    5. Computes lag features for time-series modeling
    6. Applies TRAIN/VALIDATION split
    
    **Warning**: This will clear and rebuild existing data in the date range.
    """
    try:
        service = FeatureStoreService(db)
        result = service.build_feature_store(
            tenant_id=request.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build feature store: {str(e)}")


@router.get("/validate", response_model=FeatureStoreValidationResponse)
def validate_feature_store(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Validate the feature store meets quality requirements.
    
    Checks:
    - Minimum row count (>= 1000)
    - Target variable has variance (not flatline)
    - Train/validation split exists
    - Missing rate < 50% for key features
    """
    try:
        service = FeatureStoreService(db)
        result = service.validate_feature_store(tenant_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/training-data", response_model=TrainingDataResponse)
def get_training_data(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    split: str = Query(default="TRAIN", description="Data split: TRAIN or VALIDATION"),
    limit: int = Query(default=1000, le=10000, description="Maximum rows to return"),
    db: Session = Depends(get_app_db)
):
    """
    Get training or validation data for ML model training.
    
    Returns feature rows with all computed features.
    """
    if split not in ("TRAIN", "VALIDATION", "TEST"):
        raise HTTPException(status_code=400, detail="Split must be TRAIN, VALIDATION, or TEST")
    
    try:
        service = FeatureStoreService(db)
        features = service.get_training_data(tenant_id, split)
        
        # Apply limit
        features = features[:limit]
        
        return TrainingDataResponse(
            tenant_id=tenant_id,
            split=split,
            row_count=len(features),
            features=features
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training data: {str(e)}")


@router.get("/stats", response_model=FeatureStoreStatsResponse)
def get_feature_store_stats(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    db: Session = Depends(get_app_db)
):
    """
    Get statistics about the feature store.
    
    Returns:
    - Total row count
    - Date range
    - Split distribution
    - Target variable statistics
    - Feature completeness percentages
    - Branch/category coverage
    """
    try:
        service = FeatureStoreService(db)
        stats = service._get_build_statistics(tenant_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/clear")
def clear_feature_store(
    tenant_id: int = Query(default=1, description="Tenant ID"),
    start_date: Optional[date] = Query(default=None, description="Start date (optional)"),
    end_date: Optional[date] = Query(default=None, description="End date (optional)"),
    db: Session = Depends(get_app_db)
):
    """
    Clear feature store data for a tenant.
    
    If dates are provided, only clears data in that range.
    Otherwise clears all data for the tenant.
    """
    try:
        service = FeatureStoreService(db)
        
        if start_date and end_date:
            deleted = service._clear_existing_data(tenant_id, start_date, end_date)
        else:
            # Clear all
            from sqlalchemy import text
            result = db.execute(text("""
                DELETE FROM dynamicpricing.fact_daily_demand
                WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id})
            db.commit()
            deleted = result.rowcount
        
        return {"message": f"Cleared {deleted} rows from feature store"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear feature store: {str(e)}")
