"""
Dynamic Pricing API - Main Application Entry Point
Production-grade Dynamic Pricing Tool for Car Rental (Renty SaaS)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, auth, config, prices, utilization, signals, feature_store

app = FastAPI(
    title="Renty Dynamic Pricing API",
    description="Production-grade Dynamic Pricing Tool for Car Rental",
    version="0.1.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(config.router)
app.include_router(prices.router)
app.include_router(utilization.router)
app.include_router(signals.router)
app.include_router(feature_store.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Renty Dynamic Pricing API", "docs": "/docs"}
