"""
Dynamic Pricing API - Main Application Entry Point
Production-grade Dynamic Pricing Tool for Car Rental (Renty SaaS)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dynamic-pricing-api", "version": "0.1.0"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Renty Dynamic Pricing API", "docs": "/docs"}
