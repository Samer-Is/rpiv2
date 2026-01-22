"""
Configuration API endpoints.
Provides CRUD operations for guardrails, signal weights, branch mappings, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import json
from datetime import datetime

from app.db.session import get_app_db
from app.core.security import get_current_tenant_id
from app.models.appconfig import (
    Tenant, Guardrail, SignalWeight, SelectionConfig, 
    BranchCityMapping, UtilizationStatusConfig, AuditLog
)
from app.schemas.config import (
    TenantResponse, GuardrailResponse, GuardrailCreate, GuardrailUpdate,
    SignalWeightResponse, SignalWeightUpdate, SelectionConfigResponse,
    BranchCityMappingResponse, BranchCityMappingUpdate,
    UtilizationStatusConfigResponse, UtilizationStatusConfigCreate, UtilizationStatusConfigUpdate,
    AuditLogResponse, ConfigSummaryResponse
)

router = APIRouter(prefix="/config", tags=["Configuration"])


def log_audit(db: Session, tenant_id: int, action_type: str, entity_type: str, 
              entity_id: str = None, old_value: str = None, new_value: str = None,
              user_id: str = None, notes: str = None):
    """Log an audit entry."""
    audit = AuditLog(
        tenant_id=tenant_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        user_id=user_id,
        notes=notes
    )
    db.add(audit)
    db.commit()


# ============ Tenant Endpoints ============
@router.get("/tenant", response_model=TenantResponse)
def get_tenant(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get current tenant information."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


# ============ Guardrails Endpoints ============
@router.get("/guardrails", response_model=List[GuardrailResponse])
def get_guardrails(
    category_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get guardrails for the tenant. Optionally filter by category or branch."""
    query = db.query(Guardrail).filter(Guardrail.tenant_id == tenant_id, Guardrail.is_active == True)
    
    if category_id is not None:
        query = query.filter((Guardrail.category_id == category_id) | (Guardrail.category_id == None))
    if branch_id is not None:
        query = query.filter((Guardrail.branch_id == branch_id) | (Guardrail.branch_id == None))
    
    return query.order_by(Guardrail.category_id, Guardrail.branch_id).all()


@router.post("/guardrails", response_model=GuardrailResponse, status_code=status.HTTP_201_CREATED)
def create_guardrail(
    guardrail: GuardrailCreate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Create a new guardrail."""
    db_guardrail = Guardrail(tenant_id=tenant_id, **guardrail.model_dump())
    db.add(db_guardrail)
    db.commit()
    db.refresh(db_guardrail)
    
    log_audit(db, tenant_id, "create", "guardrail", str(db_guardrail.id), 
              new_value=json.dumps(guardrail.model_dump(), default=str))
    
    return db_guardrail


@router.put("/guardrails/{guardrail_id}", response_model=GuardrailResponse)
def update_guardrail(
    guardrail_id: int,
    guardrail: GuardrailUpdate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Update a guardrail."""
    db_guardrail = db.query(Guardrail).filter(
        Guardrail.id == guardrail_id, 
        Guardrail.tenant_id == tenant_id
    ).first()
    
    if not db_guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    
    old_value = {
        "min_price": float(db_guardrail.min_price) if db_guardrail.min_price else None,
        "max_discount_pct": float(db_guardrail.max_discount_pct) if db_guardrail.max_discount_pct else None,
        "max_premium_pct": float(db_guardrail.max_premium_pct) if db_guardrail.max_premium_pct else None,
    }
    
    update_data = guardrail.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_guardrail, key, value)
    
    db_guardrail.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_guardrail)
    
    log_audit(db, tenant_id, "update", "guardrail", str(guardrail_id),
              old_value=json.dumps(old_value, default=str),
              new_value=json.dumps(update_data, default=str))
    
    return db_guardrail


# ============ Signal Weights Endpoints ============
@router.get("/signal-weights", response_model=List[SignalWeightResponse])
def get_signal_weights(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get all signal weights for the tenant."""
    return db.query(SignalWeight).filter(SignalWeight.tenant_id == tenant_id).all()


@router.put("/signal-weights/{signal_name}", response_model=SignalWeightResponse)
def update_signal_weight(
    signal_name: str,
    weight_update: SignalWeightUpdate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Update a signal weight."""
    db_weight = db.query(SignalWeight).filter(
        SignalWeight.tenant_id == tenant_id,
        SignalWeight.signal_name == signal_name
    ).first()
    
    if not db_weight:
        raise HTTPException(status_code=404, detail="Signal weight not found")
    
    old_value = {"weight": float(db_weight.weight), "is_enabled": db_weight.is_enabled}
    
    update_data = weight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_weight, key, value)
    
    db_weight.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_weight)
    
    log_audit(db, tenant_id, "update", "signal_weight", signal_name,
              old_value=json.dumps(old_value, default=str),
              new_value=json.dumps(update_data, default=str))
    
    return db_weight


# ============ Selection Config Endpoints ============
@router.get("/selections/branches", response_model=List[SelectionConfigResponse])
def get_selected_branches(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get selected branches for the tenant."""
    return db.query(SelectionConfig).filter(
        SelectionConfig.tenant_id == tenant_id,
        SelectionConfig.selection_type == "branch",
        SelectionConfig.is_active == True
    ).order_by(SelectionConfig.rank_order).all()


@router.get("/selections/categories", response_model=List[SelectionConfigResponse])
def get_selected_categories(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get selected categories for the tenant."""
    return db.query(SelectionConfig).filter(
        SelectionConfig.tenant_id == tenant_id,
        SelectionConfig.selection_type == "category",
        SelectionConfig.is_active == True
    ).order_by(SelectionConfig.rank_order).all()


# ============ Branch City Mapping Endpoints ============
@router.get("/branch-mappings", response_model=List[BranchCityMappingResponse])
def get_branch_city_mappings(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get branch to city mappings for weather API."""
    return db.query(BranchCityMapping).filter(
        BranchCityMapping.tenant_id == tenant_id,
        BranchCityMapping.is_active == True
    ).all()


@router.put("/branch-mappings/{branch_id}", response_model=BranchCityMappingResponse)
def update_branch_city_mapping(
    branch_id: int,
    mapping_update: BranchCityMappingUpdate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Update a branch city mapping (e.g., to correct coordinates)."""
    db_mapping = db.query(BranchCityMapping).filter(
        BranchCityMapping.tenant_id == tenant_id,
        BranchCityMapping.branch_id == branch_id
    ).first()
    
    if not db_mapping:
        raise HTTPException(status_code=404, detail="Branch mapping not found")
    
    update_data = mapping_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mapping, key, value)
    
    db_mapping.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_mapping)
    
    log_audit(db, tenant_id, "update", "branch_city_mapping", str(branch_id),
              new_value=json.dumps(update_data, default=str))
    
    return db_mapping


# ============ Utilization Status Config Endpoints ============
@router.get("/utilization-statuses", response_model=List[UtilizationStatusConfigResponse])
def get_utilization_status_config(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get utilization status configuration."""
    return db.query(UtilizationStatusConfig).filter(
        UtilizationStatusConfig.tenant_id == tenant_id,
        UtilizationStatusConfig.is_active == True
    ).all()


@router.post("/utilization-statuses", response_model=UtilizationStatusConfigResponse, status_code=status.HTTP_201_CREATED)
def create_utilization_status_config(
    config: UtilizationStatusConfigCreate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Add a status to utilization config."""
    # Check if status already exists
    existing = db.query(UtilizationStatusConfig).filter(
        UtilizationStatusConfig.tenant_id == tenant_id,
        UtilizationStatusConfig.status_id == config.status_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Status already configured")
    
    db_config = UtilizationStatusConfig(tenant_id=tenant_id, **config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    log_audit(db, tenant_id, "create", "utilization_status_config", str(config.status_id),
              new_value=json.dumps(config.model_dump(), default=str))
    
    return db_config


@router.put("/utilization-statuses/{status_id}", response_model=UtilizationStatusConfigResponse)
def update_utilization_status_config(
    status_id: int,
    config_update: UtilizationStatusConfigUpdate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Update a utilization status configuration."""
    db_config = db.query(UtilizationStatusConfig).filter(
        UtilizationStatusConfig.tenant_id == tenant_id,
        UtilizationStatusConfig.status_id == status_id
    ).first()
    
    if not db_config:
        raise HTTPException(status_code=404, detail="Status config not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db_config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_config)
    
    return db_config


# ============ Audit Log Endpoints ============
@router.get("/audit-log", response_model=List[AuditLogResponse])
def get_audit_log(
    entity_type: Optional[str] = None,
    limit: int = 100,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get audit log entries."""
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


# ============ Summary Endpoint ============
@router.get("/summary", response_model=ConfigSummaryResponse)
def get_config_summary(
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(get_app_db)
):
    """Get complete configuration summary for the tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    guardrails = db.query(Guardrail).filter(
        Guardrail.tenant_id == tenant_id, 
        Guardrail.is_active == True
    ).all()
    
    signal_weights = db.query(SignalWeight).filter(
        SignalWeight.tenant_id == tenant_id
    ).all()
    
    selected_branches = db.query(SelectionConfig).filter(
        SelectionConfig.tenant_id == tenant_id,
        SelectionConfig.selection_type == "branch",
        SelectionConfig.is_active == True
    ).order_by(SelectionConfig.rank_order).all()
    
    selected_categories = db.query(SelectionConfig).filter(
        SelectionConfig.tenant_id == tenant_id,
        SelectionConfig.selection_type == "category",
        SelectionConfig.is_active == True
    ).order_by(SelectionConfig.rank_order).all()
    
    branch_city_mappings = db.query(BranchCityMapping).filter(
        BranchCityMapping.tenant_id == tenant_id,
        BranchCityMapping.is_active == True
    ).all()
    
    return ConfigSummaryResponse(
        tenant=tenant,
        guardrails=guardrails,
        signal_weights=signal_weights,
        selected_branches=selected_branches,
        selected_categories=selected_categories,
        branch_city_mappings=branch_city_mappings
    )
