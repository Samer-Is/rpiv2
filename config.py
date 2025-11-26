"""
Configuration module for Dynamic Pricing Engine MVP.

This module handles:
- Database connection parameters (SQL Server 2019 with Windows Authentication)
- Project paths and constants
- Date filters and constraints
"""

import os
from pathlib import Path

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# SQL Server Connection (Windows Authentication)
DB_CONFIG = {
    'server': 'localhost',
    'database': 'eJarDbSTGLite',
    'driver': '{ODBC Driver 17 for SQL Server}',
    'trusted_connection': 'yes',  # Windows Authentication
}

# Connection string template
CONNECTION_STRING = (
    "DRIVER={driver};"
    "SERVER={server};"
    "DATABASE={database};"
    "Trusted_Connection={trusted_connection};"
)

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Data directories
DATA_DIR = BASE_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
EXTERNAL_DATA_DIR = DATA_DIR / 'external'

# Reports directory
REPORTS_DIR = BASE_DIR / 'reports'

# Models directory
MODELS_DIR = BASE_DIR / 'models'

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
                  EXTERNAL_DATA_DIR, REPORTS_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# DATA CONSTRAINTS
# ============================================================================

# Date filter: Only data from 2023-01-01 onwards
MIN_DATE = '2023-01-01'

# File paths
DB_DICTIONARY_FILE = BASE_DIR / 'database_dictionary.txt'
TRAINING_DATA_FILE = PROCESSED_DATA_DIR / 'training_data.parquet'
EXTERNAL_FEATURES_FILE = EXTERNAL_DATA_DIR / 'external_features.csv'

# ============================================================================
# KEY TABLES FOR ANALYSIS (Based on database dictionary review)
# ============================================================================

# Critical tables for dynamic pricing
KEY_TABLES = {
    'Fleet': [
        'VehicleHistory',  # For utilization calculation (MANDATORY)
        'Vehicles',        # Vehicle master data
        'Locations',       # Branch/location information
    ],
    'Rental': [
        'Contract',        # Rental contracts (pricing, dates)
        'Bookings',        # Booking information (demand signals)
        'Branches',        # Location/branch details
        'RentalRates',     # Historical pricing rates
        'Cities',          # City information
        'Countries',       # Country information
    ],
}

# ============================================================================
# UTILIZATION CALCULATION
# ============================================================================

# As per instructions: Utilization calculated ONLY from Fleet.VehicleHistory
UTILIZATION_SOURCE = 'Fleet.VehicleHistory'

# Vehicle status lookup values (from Lookups table)
# These will be refined after connecting to the actual database
VEHICLE_STATUS_MAPPING = {
    'RENTED': ['Rented', 'OnContract', 'InUse'],
    'AVAILABLE': ['Ready', 'Available'],
    'MAINTENANCE': ['Maintenance', 'UnderMaintenance'],
    'OTHER': ['OutOfService', 'Reserved', 'Cleaning'],
}

# ============================================================================
# EXTERNAL DATA SOURCES
# ============================================================================

# KSA holidays and events (to be fetched)
EXTERNAL_DATA_SOURCES = {
    'ksa_holidays': 'https://api.example.com/ksa-holidays',  # Placeholder
    'ksa_events': 'https://api.example.com/ksa-events',      # Placeholder
}

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# XGBoost parameters for demand prediction
XGBOOST_PARAMS = {
    'objective': 'reg:squarederror',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'random_state': 42,
}

# Train-test split ratio
TEST_SIZE = 0.2
VALIDATION_SIZE = 0.1

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

