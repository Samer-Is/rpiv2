# Renty Dynamic Pricing System v2.0

An intelligent, AI-powered dynamic pricing system for car rental optimization.

## 🎯 Overview

This system uses **XGBoost machine learning** to predict demand and automatically adjust rental prices based on:
- Real-time fleet utilization
- Competitor pricing analysis
- External events (holidays, Ramadan, Hajj, etc.)
- Historical booking patterns

## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   React Frontend    │────▶│   FastAPI Backend   │
│   (Port 3000)       │     │   (Port 8000)       │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────▼─────┐     ┌──────▼──────┐    ┌──────▼──────┐
              │  XGBoost  │     │  SQL Server │    │ Competitor  │
              │   Model   │     │  Database   │    │    APIs     │
              └───────────┘     └─────────────┘    └─────────────┘
```

## 📦 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQL Server (with Windows Authentication)

### 1. Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start API server
python api_server.py
```

### 2. Frontend Setup
```bash
cd frontend_prototype
npm install
npm run dev
```

### 3. Access
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## 🚀 Server Deployment

### Prerequisites
- Linux server (Ubuntu 22.04+ recommended)
- Python 3.11+
- Node.js 18+
- Nginx (for reverse proxy)
- SSL certificate (`.pfx` file)

### Step 1: Transfer Files
```bash
# Copy project to server
scp -r . user@server:/opt/renty-pricing/
```

### Step 2: Setup Backend
```bash
cd /opt/renty-pricing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service (see deploy/renty-api.service)
sudo systemctl enable renty-api
sudo systemctl start renty-api
```

### Step 3: Setup Frontend
```bash
cd frontend_prototype
npm install
npm run build

# Serve with Nginx (see deploy/nginx.conf)
```

### Step 4: Configure SSL
```bash
# Extract certificate from PFX
openssl pkcs12 -in certificate.pfx -clcerts -nokeys -out cert.pem
openssl pkcs12 -in certificate.pfx -nocerts -nodes -out key.pem

# Configure Nginx with SSL
sudo cp deploy/nginx.conf /etc/nginx/sites-available/renty
sudo ln -s /etc/nginx/sites-available/renty /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 📁 Project Structure

```
├── api_server.py           # FastAPI backend server
├── pricing_engine.py       # Core pricing logic with XGBoost
├── pricing_rules.py        # Business rules for pricing
├── config.py               # Configuration settings
├── db.py                   # Database connection
├── competitor_pricing.py   # Competitor analysis
├── utilization_query.py    # Fleet utilization queries
├── frontend_prototype/     # React TypeScript frontend
│   ├── pages/
│   │   ├── Dashboard.tsx   # Main pricing dashboard
│   │   └── Analytics.tsx   # EDA & insights
│   └── services/
│       └── api.ts          # API client
├── models/                 # Trained ML models
├── data/                   # Data files
└── deploy/                 # Deployment configs
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
# Database
DB_SERVER=your-server
DB_NAME=your-database

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_BASE_URL=https://your-domain.com
VITE_GEMINI_API_KEY=your-gemini-key
```

### Database Connection
The system uses Windows Authentication by default. For server deployment, update `db.py` with appropriate credentials.

## 📊 Features

- **Real-time Pricing**: Dynamic price adjustments based on demand
- **Branch-specific Data**: Per-branch utilization and metrics
- **Competitor Analysis**: Integration with Booking.com and Kayak
- **Event Detection**: Automatic detection of holidays, Ramadan, Hajj
- **AI Insights**: Gemini-powered pricing recommendations
- **Adjustable Multipliers**: Customizable pricing rules

## 🔒 Security

- CORS configured for production domains
- SSL/TLS encryption support
- Database credentials via environment variables
- Certificate-based HTTPS

## 📈 Model Performance

- **Algorithm**: XGBoost Regressor
- **R² Score**: 95.35%
- **Features**: 52 engineered features
- **Training Data**: 2+ years of historical bookings

## 👥 Team Access

After deployment, share the URL with team members:
- `https://your-domain.com` - Main dashboard
- `https://your-domain.com/analytics` - EDA Analysis
- `https://your-domain.com/docs` - Documentation

## 📝 License

Internal use only - Al-Manzumah Al-Muttahidah For IT Systems
