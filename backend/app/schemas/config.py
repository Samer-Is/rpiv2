"""
Pydantic schemas for configuration API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============ Tenant Schemas ============
class TenantBase(BaseModel):
    name: str
    tenancy_name: str
    is_active: bool = True
    source_tenant_id: int

class TenantResponse(TenantBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Guardrail Schemas ============
class GuardrailBase(BaseModel):
    category_id: Optional[int] = None
    branch_id: Optional[int] = None
    min_price: Decimal = Field(default=Decimal("50.00"), ge=0)
    max_price: Optional[Decimal] = None
    min_discount_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    max_discount_pct: Decimal = Field(default=Decimal("30.00"), ge=0, le=100)
    min_premium_pct: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    max_premium_pct: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)
    is_active: bool = True

class GuardrailCreate(GuardrailBase):
    pass

class GuardrailUpdate(BaseModel):
    category_id: Optional[int] = None
    branch_id: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_discount_pct: Optional[Decimal] = None
    max_discount_pct: Optional[Decimal] = None
    min_premium_pct: Optional[Decimal] = None
    max_premium_pct: Optional[Decimal] = None
    is_active: Optional[bool] = None

class GuardrailResponse(GuardrailBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Signal Weight Schemas ============
class SignalWeightBase(BaseModel):
    signal_name: str
    weight: Decimal = Field(default=Decimal("1.000"), ge=0, le=10)
    is_enabled: bool = True
    description: Optional[str] = None

class SignalWeightCreate(SignalWeightBase):
    pass

class SignalWeightUpdate(BaseModel):
    weight: Optional[Decimal] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None

class SignalWeightResponse(SignalWeightBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Branch City Mapping Schemas ============
class BranchCityMappingBase(BaseModel):
    branch_id: int
    branch_name: Optional[str] = None
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: str = "Asia/Riyadh"
    is_active: bool = True

class BranchCityMappingCreate(BranchCityMappingBase):
    pass

class BranchCityMappingUpdate(BaseModel):
    branch_name: Optional[str] = None
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None

class BranchCityMappingResponse(BranchCityMappingBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Selection Config Schemas ============
class SelectionConfigBase(BaseModel):
    selection_type: str  # 'branch' or 'category'
    item_id: int
    item_name: Optional[str] = None
    item_subtype: Optional[str] = None  # For branches: 'airport', 'city'
    rank_order: int = 0
    is_active: bool = True

class SelectionConfigCreate(SelectionConfigBase):
    pass

class SelectionConfigUpdate(BaseModel):
    item_name: Optional[str] = None
    item_subtype: Optional[str] = None
    rank_order: Optional[int] = None
    is_active: Optional[bool] = None

class SelectionConfigResponse(SelectionConfigBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Utilization Status Config Schemas ============
class UtilizationStatusConfigBase(BaseModel):
    status_id: int
    status_name: str
    status_type: str  # 'numerator', 'denominator', 'excluded'
    description: Optional[str] = None
    is_active: bool = True

class UtilizationStatusConfigCreate(UtilizationStatusConfigBase):
    pass

class UtilizationStatusConfigUpdate(BaseModel):
    status_name: Optional[str] = None
    status_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class UtilizationStatusConfigResponse(UtilizationStatusConfigBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ Audit Log Schemas ============
class AuditLogResponse(BaseModel):
    id: int
    tenant_id: int
    action_type: str
    entity_type: str
    entity_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Bulk Response Schemas ============
class ConfigSummaryResponse(BaseModel):
    """Summary of all configuration for a tenant."""
    tenant: TenantResponse
    guardrails: List[GuardrailResponse]
    signal_weights: List[SignalWeightResponse]
    selected_branches: List[SelectionConfigResponse]
    selected_categories: List[SelectionConfigResponse]
    branch_city_mappings: List[BranchCityMappingResponse]
