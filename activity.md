# Activity Log

This file logs all successful commits to the repository.

---

## 2026-01-22

### Commit: CHUNK 1 - SQL Server Data Discovery
- **Hash:** 9928287
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2
- **Status:** ✅ COMPLETE

**Key Discoveries:**
- YELO tenant_id = 1 (Name: 'Yelo', TenancyName: 'Default')
- Total individual rentals (2022+): 2,826,983
- Data range: 2022-01-01 to 2025-11-18
- DailyRateAmount: 100% complete, avg 234 SAR
- Filter: `Discriminator='Contract' AND StatusId=211`
- Pre-existing dynamicpricing schema found with:
  - TopBranches (6 MVP branches)
  - TopCategories (6 MVP categories)
  - TrainingData (36,308 rows)
  - ValidationData (4,749 rows)

**Files Created/Modified:**
- `scripts/data_discovery.py` - Main discovery script
- `scripts/data_discovery_part2.py` - MVP scope queries
- `scripts/data_discovery_part3.py` - Final details
- `docs/data_discovery_report.md` - Comprehensive findings
- `backend/app/core/config.py` - Windows Auth config
- `backend/app/db/session.py` - Updated connection handling
- `docs/validation_checklist.md` - Updated with discoveries

---

### Commit: CHUNK 0 - Project Scaffold
- **Hash:** a499d75
- **Branch:** main
- **Repo:** https://github.com/Samer-Is/rpiv2

**Files Created:**
- `backend/` - FastAPI Python backend
  - `app/main.py` - Main FastAPI application
  - `app/core/config.py` - Configuration from env vars
  - `app/core/security.py` - JWT authentication
  - `app/db/session.py` - SQL Server connection management
  - `app/routers/health.py` - Health check endpoint
  - `app/routers/auth.py` - Login endpoint
  - `app/schemas/auth.py` - Auth request/response models
  - `requirements.txt` - Python dependencies
  - `Dockerfile` - Backend container config
  - `.env.example` - Environment template

- `frontend/` - React + TypeScript frontend
  - `src/main.tsx` - React entry point
  - `src/App.tsx` - Router setup
  - `src/pages/LoginPage.tsx` - Login form
  - `src/pages/DashboardPage.tsx` - Main dashboard skeleton
  - `src/api/client.ts` - Axios API client
  - `src/api/auth-store.ts` - Zustand auth state
  - `src/styles/globals.css` - Tailwind styles
  - `package.json` - Node dependencies
  - `Dockerfile` - Frontend container config
  - `nginx.conf` - Production nginx config

- `docs/` - Documentation
  - `requirements.md` - Functional/non-functional requirements
  - `architecture.md` - System architecture diagrams
  - `validation_checklist.md` - Chunk validation checklist
  - `decisions_log.md` - Architecture decisions record

- Root files
  - `docker-compose.yml` - Multi-container setup
  - `README.md` - Project documentation
  - `.gitignore` - Git ignore rules
  - `.env.example` - Root environment template

**Validation Status:** PENDING (need to test backend health + frontend login)

---
