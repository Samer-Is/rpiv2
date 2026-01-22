"""
SQLAlchemy models for appconfig schema tables.
These are used for the Dynamic Pricing Tool configuration.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Tenant(Base):
    """Tenant configuration for multi-tenant support."""
    __tablename__ = "tenants"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tenancy_name = Column(String(128), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    source_tenant_id = Column(Integer, nullable=False)  # Maps to dbo.AbpTenants.Id
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    settings = relationship("TenantSetting", back_populates="tenant")
    guardrails = relationship("Guardrail", back_populates="tenant")
    signal_weights = relationship("SignalWeight", back_populates="tenant")


class TenantSetting(Base):
    """Key-value settings per tenant."""
    __tablename__ = "tenant_settings"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    setting_key = Column(String(255), nullable=False)
    setting_value = Column(Text, nullable=False)
    setting_type = Column(String(50), nullable=False, default="string")
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="settings")


class Guardrail(Base):
    """Price guardrails configuration per tenant/category/branch."""
    __tablename__ = "guardrails"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    category_id = Column(Integer, nullable=True)  # NULL = all categories
    branch_id = Column(Integer, nullable=True)    # NULL = all branches
    min_price = Column(Numeric(10, 2), nullable=False, default=50.00)
    max_price = Column(Numeric(10, 2), nullable=True)
    min_discount_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    max_discount_pct = Column(Numeric(5, 2), nullable=False, default=30.00)
    min_premium_pct = Column(Numeric(5, 2), nullable=False, default=0.00)
    max_premium_pct = Column(Numeric(5, 2), nullable=False, default=50.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="guardrails")


class SignalWeight(Base):
    """Signal weights for pricing algorithm."""
    __tablename__ = "signal_weights"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    signal_name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 3), nullable=False, default=1.000)
    is_enabled = Column(Boolean, nullable=False, default=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="signal_weights")


class UtilizationStatusConfig(Base):
    """Configuration for which vehicle statuses count in utilization calculation."""
    __tablename__ = "utilization_status_config"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    status_id = Column(BigInteger, nullable=False)
    status_name = Column(String(255), nullable=False)
    status_type = Column(String(50), nullable=False)  # 'numerator', 'denominator', 'excluded'
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class BranchCityMapping(Base):
    """Mapping of branches to cities with coordinates for weather API."""
    __tablename__ = "branch_city_mapping"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    branch_id = Column(Integer, nullable=False)
    branch_name = Column(String(500), nullable=True)
    city_id = Column(Integer, nullable=True)
    city_name = Column(String(255), nullable=True)
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    timezone = Column(String(100), nullable=True, default="Asia/Riyadh")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class CompetitorMapping(Base):
    """Mapping of categories to competitor vehicle types."""
    __tablename__ = "competitor_mapping"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    category_id = Column(Integer, nullable=False)
    category_name = Column(String(255), nullable=True)
    competitor_vehicle_type = Column(String(255), nullable=False)
    competitor_source = Column(String(100), nullable=False, default="booking.com")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class SelectionConfig(Base):
    """Configuration for selected branches and categories (MVP scope)."""
    __tablename__ = "selection_config"
    __table_args__ = {"schema": "appconfig"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    selection_type = Column(String(50), nullable=False)  # 'branch', 'category'
    item_id = Column(Integer, nullable=False)
    item_name = Column(String(500), nullable=True)
    item_subtype = Column(String(100), nullable=True)  # For branches: 'airport', 'city'
    rank_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit log for tracking changes and approvals."""
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("IX_audit_log_tenant_created", "tenant_id", "created_at"),
        Index("IX_audit_log_action", "action_type", "created_at"),
        {"schema": "appconfig"}
    )
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("appconfig.tenants.id"), nullable=False)
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    user_id = Column(String(255), nullable=True)
    user_name = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
