# Renty Dynamic Pricing - Deployment Guide

This guide covers deploying the Dynamic Pricing Tool on Windows Server using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [Windows Server Deployment](#windows-server-deployment)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Windows Server Requirements

- Windows Server 2019 or later
- Docker Desktop for Windows (with WSL 2 backend)
- Minimum 8GB RAM (16GB recommended)
- 20GB free disk space
- Network access to SQL Server

### SQL Server Requirements

- SQL Server 2017 or later
- Databases: `eJarDbSTGLite`, `eJarDbReports`
- Schemas created: `dynamicpricing`, `appconfig` in `eJarDbSTGLite`
- ODBC Driver 17 for SQL Server

### External API Keys (Optional but Recommended)

- **WeatherAPI.com**: For weather data - [Get API Key](https://www.weatherapi.com/)
- **Calendarific**: For holidays - [Get API Key](https://calendarific.com/)
- **Booking.com RapidAPI**: For competitor pricing - [Get API Key](https://rapidapi.com/apidojo/api/booking-com)

---

## Quick Start

```powershell
# 1. Clone the repository
git clone https://github.com/Samer-Is/rpiv2.git
cd rpiv2

# 2. Copy and configure environment
copy .env.example .env
# Edit .env with your settings

# 3. Start the application
docker-compose up -d --build

# 4. Check status
docker-compose ps
docker-compose logs -f
```

Access the application:
- **Frontend**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Environment Configuration

### Required Variables

Copy `.env.example` to `.env` and configure:

```env
# SQL Server Connection
SQL_SERVER=your-sql-server-hostname
SQL_DATABASE=eJarDbSTGLite
SQL_DATABASE_REPORTS=eJarDbReports
SQL_USERNAME=your-sql-username
SQL_PASSWORD=your-sql-password
SQL_USE_WINDOWS_AUTH=false

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your-secure-random-string-at-least-32-characters
```

### Optional Variables

```env
# External APIs
WEATHERAPI_COM_KEY=your-weatherapi-key
CALENDARIFIC_API_KEY=your-calendarific-key
BOOKING_COM_API_KEY=your-rapidapi-key

# Simulation date (for testing)
SIMULATION_TODAY=2025-05-31
```

### Generating a Secure JWT Secret

```powershell
# PowerShell
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

---

## Windows Server Deployment

### Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows from https://docs.docker.com/desktop/windows/install/
2. Run the installer
3. Enable WSL 2 backend during installation
4. Restart the server if prompted
5. Start Docker Desktop

Verify installation:
```powershell
docker --version
docker-compose --version
```

### Step 2: Configure Windows Firewall

Allow inbound traffic on ports 80 and 8000:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Dynamic Pricing HTTP" -Direction Inbound -Port 80 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Dynamic Pricing API" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
```

### Step 3: Configure SQL Server Access

Ensure the Docker containers can reach SQL Server:

1. **If SQL Server is on the same machine:**
   - Use `host.docker.internal` as `SQL_SERVER` in `.env`
   - Enable TCP/IP in SQL Server Configuration Manager
   - Ensure SQL Server allows remote connections

2. **If SQL Server is on a different machine:**
   - Use the server's hostname or IP address
   - Ensure firewall allows port 1433 (or custom port)

### Step 4: Deploy Application

```powershell
# Navigate to project directory
cd C:\path\to\rpiv2

# Build and start containers
docker-compose up -d --build

# Verify containers are running
docker-compose ps

# Check logs
docker-compose logs backend
docker-compose logs frontend
```

---

## Database Setup

The application requires two schemas in `eJarDbSTGLite`:

### Create Schemas

```sql
-- Run in SQL Server Management Studio
USE eJarDbSTGLite;
GO

-- Create schemas if not exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dynamicpricing')
    EXEC('CREATE SCHEMA dynamicpricing');
GO

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'appconfig')
    EXEC('CREATE SCHEMA appconfig');
GO
```

### Run Table Creation Scripts

The SQL scripts in the `scripts/` folder should be executed in order:

1. `create_appconfig_tables.sql` - Configuration tables
2. `create_dynamicpricing_tables.sql` - Feature store tables
3. `create_recommendations_table.sql` - Recommendations table

---

## Running the Application

### Start Services

```powershell
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d backend
docker-compose up -d frontend
```

### Stop Services

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Restart Services

```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### View Logs

```powershell
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Update Application

```powershell
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build
```

---

## Monitoring & Maintenance

### Health Checks

The application includes built-in health checks:

```powershell
# Check backend health
curl http://localhost:8000/health

# Check container health
docker-compose ps
```

### Container Status

```powershell
# View running containers
docker ps

# View resource usage
docker stats
```

### Logs Rotation

Configure Docker logging in `docker-compose.yml`:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Backup Recommendations

```powershell
# Export recommendations data
docker exec dynamic-pricing-backend python -c "
import pyodbc
# Export script here
"
```

---

## Troubleshooting

### Common Issues

#### 1. Cannot connect to SQL Server

```
Error: pyodbc.InterfaceError: ('IM002', '[IM002] [Microsoft][ODBC Driver Manager] Data source name not found')
```

**Solution:**
- Verify SQL Server is accessible from the Docker network
- Check `SQL_SERVER` hostname in `.env`
- Ensure ODBC Driver 17 is installed in the container
- Try using IP address instead of hostname

#### 2. Frontend cannot reach backend

**Solution:**
- Check nginx.conf proxy settings
- Verify backend container is running: `docker-compose ps`
- Check backend logs: `docker-compose logs backend`

#### 3. Authentication fails

**Solution:**
- Verify JWT_SECRET_KEY is set
- Check token expiration (JWT_EXPIRE_MINUTES)
- Clear browser cookies and try again

#### 4. Container keeps restarting

**Solution:**
- Check logs: `docker-compose logs backend`
- Verify environment variables
- Check database connectivity

#### 5. Out of memory

**Solution:**
- Increase Docker Desktop memory allocation
- Reduce number of workers in Dockerfile
- Monitor with `docker stats`

### Debug Mode

Enable debug mode for more verbose logging:

```env
DEBUG=true
```

### Manual Container Access

```powershell
# Access backend shell
docker exec -it dynamic-pricing-backend /bin/bash

# Access frontend shell
docker exec -it dynamic-pricing-frontend /bin/sh

# Run Python commands
docker exec dynamic-pricing-backend python -c "print('Hello')"
```

---

## Production Checklist

Before going to production:

- [ ] Change `JWT_SECRET_KEY` to a secure random value
- [ ] Set `DEBUG=false`
- [ ] Configure proper SSL/TLS (use reverse proxy like Traefik or nginx)
- [ ] Set up log rotation
- [ ] Configure backup procedures
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Test failover scenarios
- [ ] Document recovery procedures
- [ ] Configure Windows service for auto-start

### Auto-Start on Windows Boot

Create a Windows Task Scheduler job to start Docker Compose on boot:

```powershell
# Create scheduled task (run as Administrator)
$action = New-ScheduledTaskAction -Execute "docker-compose" -Argument "up -d" -WorkingDirectory "C:\path\to\rpiv2"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "DynamicPricingAutoStart" -Action $action -Trigger $trigger -Principal $principal
```

---

## Support

For issues and support:
- Check logs: `docker-compose logs`
- Review this documentation
- Open an issue on GitHub
