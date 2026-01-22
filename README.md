# Renty Dynamic Pricing Tool

Production-grade Dynamic Pricing Tool for Car Rental integrated into Renty SaaS.

## Project Structure

```
rpiv4/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Config, security
│   │   ├── db/             # Database connections
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── routers/        # API endpoints
│   │   └── utils/          # Utilities
│   ├── tests/
│   ├── alembic/            # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   └── styles/
│   ├── package.json
│   └── Dockerfile
├── docs/                   # Documentation
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- SQL Server with ODBC Driver 17
- Node.js 20+ (for local frontend dev)
- Python 3.10+ (for local backend dev)

### Environment Setup

1. Copy environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your SQL Server credentials and API keys.

### Run with Docker

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:80
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /auth/login | Login and get JWT |
| GET | /config/* | Configuration endpoints |
| GET | /recommendations | Get pricing recommendations |
| POST | /recommendations/{id}/approve | Approve recommendation |
| POST | /recommendations/{id}/skip | Skip recommendation |

## Deployment (Windows Server)

1. Install Docker Desktop on Windows Server
2. Clone repository
3. Configure `.env` file
4. Run `docker-compose up -d`

## Multi-Tenancy

- All tables include `tenant_id` column
- JWT tokens contain `tenant_id` claim
- API automatically filters by tenant context

## MVP Scope

- Tenant: YELO
- Branches: Top 6 (3 airport + 3 non-airport)
- Categories: Top 6 by rental volume
