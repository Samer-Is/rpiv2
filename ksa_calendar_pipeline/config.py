"""
KSA Calendar Pipeline Configuration
Environment variables and settings.
"""
import os

# SQL Server connection settings
SQL_SERVER = os.environ.get("SQL_SERVER", "localhost")
SQL_DATABASE = os.environ.get("SQL_DATABASE", "eJarDbSTGLite")
SQL_USERNAME = os.environ.get("SQL_USERNAME", "")  # Empty for Windows Auth
SQL_PASSWORD = os.environ.get("SQL_PASSWORD", "")  # Empty for Windows Auth

# Calendarific API
CALENDARIFIC_API_KEY = os.environ.get("CALENDARIFIC_API_KEY", "")
CALENDARIFIC_COUNTRY = "SA"  # Saudi Arabia

# Cities for GDELT event monitoring
MONITORED_CITIES = [
    "Riyadh",
    "Jeddah",
    "Dammam",
    "Medina",
    "Abha"
]

# GDELT API settings
GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TIMEOUT = 30  # seconds

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Tenant ID for YELO
DEFAULT_TENANT_ID = 1
