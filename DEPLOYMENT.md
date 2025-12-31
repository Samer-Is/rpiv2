# Renty Dynamic Pricing System - Deployment Guide

## Overview

This system runs entirely on **local data files** and does not require database connectivity in production. All required data has been pre-exported and is included in the deployment package.

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose installed
- SSL certificate (rentey.pfx)

### 1. Extract SSL Certificate

```powershell
cd deploy
.\setup-ssl.ps1
```

This will create:
- `certs/cert.pem` - Public certificate
- `certs/key.pem` - Private key

### 2. Build and Run

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access the Application

- **HTTPS**: https://your-server-ip (or your domain)
- **HTTP**: Automatically redirects to HTTPS

## Manual Deployment (Without Docker)

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start API server
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend_prototype

# Install dependencies
npm install

# Build production bundle
npm run build

# The built files will be in 'dist/' folder
```

### 3. Nginx Configuration

Copy `deploy/nginx.conf` to your Nginx configuration and update:
- Server name
- SSL certificate paths
- Frontend dist path

## Data Files

All data is stored locally in the `data/` folder:

| File | Description |
|------|-------------|
| `vehicle_history_local.csv` | Fleet utilization per branch |
| `branches.json` | Branch information (names, cities) |
| `contract_stats.json` | Total contract statistics |
| `weekly_distribution.json` | Weekly booking patterns per branch |
| `seasonal_impact.json` | Seasonal demand factors per branch |
| `competitor_prices/daily_competitor_prices.json` | Latest competitor pricing |

## Updating Data

To update the data files (requires database access):

```bash
python export_all_data.py
```

This should be run periodically on a machine with database connectivity, then the updated files can be deployed.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /api/branches` | List all branches |
| `GET /api/metrics` | System metrics |
| `GET /api/pricing/all` | All category pricing |
| `GET /api/demand-data` | Demand forecasts |
| `GET /api/analytics/weekly-distribution` | Weekly patterns |
| `GET /api/analytics/seasonal-impact` | Seasonal factors |

## Troubleshooting

### API Not Starting
- Check if port 8000 is available
- Verify all data files exist in `data/`
- Check logs: `docker-compose logs api`

### SSL Certificate Issues
- Ensure cert.pem and key.pem are valid
- Check Nginx logs: `docker-compose logs nginx`

### Frontend Not Loading
- Verify the build completed successfully
- Check browser console for errors
- Ensure API is accessible

## Security Notes

- Change default ports if needed
- Enable firewall rules for your network
- Keep SSL certificates secure
- Update data files regularly

## Support

For issues, check the logs first:
```bash
docker-compose logs -f
```

---

*Renty Dynamic Pricing System v2.0*

