# Decisions Log

This document tracks architectural and implementation decisions made during development.

---

## Decision 001: Multi-Tenancy Approach
**Date:** 2026-01-22  
**Decision:** Row-level tenancy with tenant_id column in all tables  
**Rationale:** 
- Simpler than database-per-tenant
- Works well with shared SQL Server
- Easy to filter in queries
- JWT claims carry tenant context

---

## Decision 002: Frontend Stack
**Date:** 2026-01-22  
**Decision:** React + TypeScript + Vite + Tailwind  
**Rationale:**
- Modern, fast development
- Strong typing with TypeScript
- Tailwind for rapid UI development
- Vite for fast builds

---

## Decision 003: Backend Stack
**Date:** 2026-01-22  
**Decision:** FastAPI + SQLAlchemy + pyodbc  
**Rationale:**
- FastAPI is modern, async-capable, auto-docs
- SQLAlchemy for ORM with SQL Server support
- pyodbc for reliable ODBC connections

---

## Decision 004: Global Forecasting Model
**Date:** 2026-01-22  
**Decision:** Train single global model for all series  
**Rationale:**
- Per-series models don't scale for SaaS
- Global model shares learning across series
- More robust with limited data per series

---

## Decision 005: Forecast Horizon
**Date:** 2026-01-22  
**Decision:** 30-day rolling window  
**Rationale:**
- Balances accuracy vs planning horizon
- Matches typical booking lead times
- Refreshed daily

---

*More decisions will be logged as development progresses.*
