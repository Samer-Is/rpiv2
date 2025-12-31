# Renty Dynamic Pricing System - Production Dockerfile
# Multi-stage build for optimized deployment

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend_prototype/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source files
COPY frontend_prototype/ ./

# Build production bundle
RUN npm run build

# Stage 2: Python API Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy API server files
COPY api_server.py ./
COPY pricing_engine.py ./
COPY pricing_rules.py ./
COPY utilization_query.py ./
COPY competitor_pricing.py ./
COPY stored_competitor_prices.py ./
COPY car_model_category_mapping.py ./
COPY car_model_matcher.py ./

# Copy data files (pre-exported local data)
COPY data/ ./data/

# Copy ML models
COPY models/ ./models/

# Copy frontend build from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Run the API server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]

