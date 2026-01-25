# Renty Dynamic Pricing Tool

Production-grade Dynamic Pricing Tool for Car Rental integrated into Renty SaaS.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)](https://www.typescriptlang.org/)

## Features

- **Dynamic Pricing Engine**: Combines 5 signals (utilization, forecast, competitors, weather, holidays)
- **30-Day Forecast Window**: Rolling recommendations with ML-powered demand forecasting
- **Multi-Tenant Architecture**: SaaS-ready with row-level tenancy
- **Configurable Guardrails**: Min/max price limits, discount caps
- **Approval Workflow**: Approve/skip recommendations with audit logging
- **Real-Time Dashboard**: React frontend with branch/category views

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  - Dashboard with 6 category cards                               │
│  - Branch selector, date picker                                  │
│  - 30-day forecast table                                         │
│  - Approve/Skip workflow                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │  Auth    │ │  Config  │ │ Pricing  │ │ Signals  │            │
│  │ Router   │ │  Router  │ │  Engine  │ │ Services │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQL
┌────────────────────────────▼────────────────────────────────────┐
│                     SQL Server                                   │
│  ┌─────────────────┐  ┌──────────────────────────────┐          │
│  │ Source Data     │  │ App Data (dynamicpricing)     │          │
│  │ - rental.*      │  │ - feature_store_30d           │          │
│  │ - fleet.*       │  │ - recommendations_30d         │          │
│  │ - eJarDbReports │  │ - weather/holidays/competitors│          │
│  └─────────────────┘  └──────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- SQL Server with ODBC Driver 17
- Network access to SQL Server instance

### 1. Clone & Configure

```bash
git clone https://github.com/Samer-Is/rpiv2.git
cd rpiv2
cp .env.example .env
# Edit .env with your SQL Server credentials
```

### 2. Run with Docker

```bash
docker-compose up -d --build
```

### 3. Access

- **Frontend**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

**Default Login**: `admin` / `admin123`

## Project Structure

```
rpiv2/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Config, security, settings
│   │   ├── db/             # Database connections
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic services
│   │   │   ├── pricing_engine.py    # Core pricing logic
│   │   │   ├── utilization_service.py
│   │   │   ├── weather_service.py
│   │   │   └── competitor_service.py
│   │   ├── routers/        # API endpoints
│   │   └── ml/             # ML models (LSTM demand forecasting)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/          # Dashboard, Login pages
│   │   ├── api/            # API client, auth store
│   │   └── styles/         # Tailwind CSS
│   ├── nginx.conf          # Production nginx config
│   └── Dockerfile
├── scripts/                # SQL table creation scripts
├── docs/                   # Documentation
│   └── DEPLOYMENT.md       # Detailed deployment guide
├── docker-compose.yml
├── .env.example
└── README.md
```

## Local Development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # Runs on http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | OAuth2 login, returns JWT |
| GET | `/config/selections/branches` | Get configured branches |
| GET | `/config/selections/categories` | Get configured categories |
| GET | `/config/guardrails` | Get pricing guardrails |
| GET | `/recommendations` | Get pricing recommendations |
| GET | `/recommendations/summary` | Get recommendation stats |
| POST | `/recommendations/generate` | Generate new recommendations |
| POST | `/recommendations/{id}/approve` | Approve a recommendation |
| POST | `/recommendations/{id}/skip` | Skip a recommendation |
| POST | `/recommendations/bulk-approve` | Bulk approve by date range |
| GET | `/utilization/branch/{branch_id}` | Get utilization data |
| GET | `/prices/base` | Get base prices |

## Pricing Engine

The pricing engine combines 5 weighted signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Utilization | 30% | Current + future bookings vs fleet |
| Demand Forecast | 25% | ML-predicted demand (LSTM) |
| Competitor | 20% | Booking.com pricing data |
| Weather | 15% | Temperature impact on rentals |
| Holiday/Events | 10% | Calendar features (holidays, weekends, Ramadan) |

### Guardrails

- Minimum price floor (prevents losses)
- Maximum discount cap (e.g., -25%)
- Maximum premium cap (e.g., +50%)

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed Windows Server deployment instructions.

### Quick Production Deploy

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values

# 2. Build and start
docker-compose up -d --build

# 3. Check status
docker-compose ps
docker-compose logs -f
```

## Multi-Tenancy

- All tables include `tenant_id` column
- JWT tokens contain `tenant_id` claim
- API automatically filters by tenant context
- MVP Tenant: YELO (tenant_id = 1)

## MVP Scope

| Dimension | Values |
|-----------|--------|
| Tenant | YELO |
| Branches | 6 (Riyadh Airport, Jeddah Airport, Dammam Airport, Riyadh City, Jeddah City, Riyadh Al-Quds) |
| Categories | 6 (Economy, Compact, Standard, SUV, Luxury, Van) |
| Forecast Horizon | 30 days |
| Training Data | 2023-01-01 onwards |

## License

Proprietary - Renty SaaS

## Support

For issues, open a GitHub issue or contact the development team.
