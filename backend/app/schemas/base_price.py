"""
Pydantic schemas for base price endpoints
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BasePriceResponse(BaseModel):
    """Response for base price lookup"""
    branch_id: int = Field(..., description="Branch ID")
    category_id: int = Field(..., description="Car category ID")
    category_name: str = Field(..., description="Category name")
    effective_date: date = Field(..., description="Date prices are effective for")
    daily_rate: Decimal = Field(..., description="Daily rental rate in SAR")
    weekly_rate: Decimal = Field(..., description="Weekly rental rate (per day) in SAR")
    monthly_rate: Decimal = Field(..., description="Monthly rental rate (per day) in SAR")
    model_count: int = Field(..., description="Number of models in category")
    source: str = Field(..., description="Price source: 'branch_specific' or 'default'")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }


class ModelPriceResponse(BaseModel):
    """Response for individual model price"""
    model_id: int = Field(..., description="Model ID")
    model_name: str = Field(..., description="Model name")
    category_id: int = Field(..., description="Car category ID")
    category_name: str = Field(..., description="Category name")
    daily_rate: Optional[Decimal] = Field(None, description="Daily rental rate in SAR")
    weekly_rate: Optional[Decimal] = Field(None, description="Weekly rental rate (per day) in SAR")
    monthly_rate: Optional[Decimal] = Field(None, description="Monthly rental rate (per day) in SAR")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v) if v else None
        }


class CategoryPriceSummary(BaseModel):
    """Summary of prices for a category"""
    category_id: int = Field(..., description="Car category ID")
    category_name: str = Field(..., description="Category name")
    model_count: int = Field(..., description="Number of models with active prices")
    daily_rate: Optional[float] = Field(None, description="Average daily rate in SAR")
    weekly_rate: Optional[float] = Field(None, description="Average weekly rate (per day) in SAR")
    monthly_rate: Optional[float] = Field(None, description="Average monthly rate (per day) in SAR")


class AllCategoryPricesResponse(BaseModel):
    """Response for all category prices"""
    effective_date: date = Field(..., description="Date prices are effective for")
    categories: List[CategoryPriceSummary] = Field(..., description="List of category price summaries")


class MVPCategoryPricesResponse(BaseModel):
    """Response for MVP category prices"""
    effective_date: date = Field(..., description="Date prices are effective for")
    tenant_id: int = Field(..., description="Tenant ID")
    categories: Dict[int, CategoryPriceSummary] = Field(..., description="Map of category_id to price summary")


class BasePriceRequest(BaseModel):
    """Request for base price lookup"""
    branch_id: int = Field(..., description="Branch ID", ge=1)
    category_id: int = Field(..., description="Car category ID", ge=1)
    effective_date: date = Field(..., description="Date to get prices for")
