"""
Competitor Scraper Configuration
Configure competitor websites, locations, and category mappings
"""

# ============================================================================
# LEGAL DISCLAIMER
# ============================================================================
"""
IMPORTANT LEGAL NOTICE:

This web scraping tool should only be used in compliance with:
1. The target website's Terms of Service
2. robots.txt file guidelines
3. Local and international data protection laws
4. Fair use and ethical scraping practices

RECOMMENDATIONS:
- Obtain explicit permission from competitor websites before scraping
- Use official APIs when available
- Implement rate limiting to avoid server overload
- Respect robots.txt directives
- Consider using authorized data providers

The user assumes all legal responsibility for the use of this tool.
"""

# ============================================================================
# COMPETITOR WEBSITE CONFIGURATION
# ============================================================================

COMPETITORS = {
    "Hertz": {
        "name": "Hertz",
        "base_url": "https://www.hertz.com",  # UPDATE WITH ACTUAL SAUDI SITE
        "country_code": "SA",  # Saudi Arabia
        "search_page": "/reservations/car-rental",
        "enabled": True,
        "scraping_method": "selenium",  # selenium or playwright
        "wait_time": 10,  # seconds to wait for page load
        "selectors": {
            # CSS selectors for price elements (TO BE CONFIGURED)
            "price": ".price-amount, .rate-amount, .total-price",
            "category": ".car-class, .vehicle-category",
            "location": ".pickup-location, .location-name",
            "date": ".pickup-date",
        }
    },
    "Budget": {
        "name": "Budget",
        "base_url": "https://www.budget.com",  # UPDATE WITH ACTUAL SAUDI SITE
        "country_code": "SA",
        "search_page": "/en/car-rental",
        "enabled": True,
        "scraping_method": "selenium",
        "wait_time": 10,
        "selectors": {
            "price": ".price, .rate-per-day",
            "category": ".car-type, .category-name",
            "location": ".branch-location",
            "date": ".rental-date",
        }
    },
    "Thrifty": {
        "name": "Thrifty",
        "base_url": "https://www.thrifty.com",  # UPDATE WITH ACTUAL SAUDI SITE
        "country_code": "SA",
        "search_page": "/car-rental",
        "enabled": True,
        "scraping_method": "selenium",
        "wait_time": 10,
        "selectors": {
            "price": ".daily-rate, .price-value",
            "category": ".car-category",
            "location": ".pickup-point",
            "date": ".date-selected",
        }
    }
}

# ============================================================================
# LOCATION MAPPING (Renty → Competitor)
# ============================================================================

LOCATION_MAPPING = {
    # Riyadh
    "Riyadh - King Khalid International Airport": {
        "Hertz": ["Riyadh Airport", "King Khalid International Airport", "RUH Airport"],
        "Budget": ["Riyadh King Khalid Airport", "Riyadh - Airport", "RUH"],
        "Thrifty": ["Riyadh Airport", "King Khalid Intl Airport"]
    },
    "Riyadh - City": {
        "Hertz": ["Riyadh City", "Riyadh Downtown", "Riyadh Centre"],
        "Budget": ["Riyadh City Center", "Riyadh - City"],
        "Thrifty": ["Riyadh City", "Riyadh Central"]
    },
    
    # Jeddah
    "Jeddah - King Abdulaziz International Airport": {
        "Hertz": ["Jeddah Airport", "King Abdulaziz International Airport", "JED Airport"],
        "Budget": ["Jeddah King Abdulaziz Airport", "Jeddah - Airport", "JED"],
        "Thrifty": ["Jeddah Airport", "King Abdulaziz Intl Airport"]
    },
    "Jeddah - City": {
        "Hertz": ["Jeddah City", "Jeddah Downtown", "Jeddah Centre"],
        "Budget": ["Jeddah City Center", "Jeddah - City"],
        "Thrifty": ["Jeddah City", "Jeddah Central"]
    },
    
    # Dammam
    "Dammam - King Fahd International Airport": {
        "Hertz": ["Dammam Airport", "King Fahd International Airport", "DMM Airport"],
        "Budget": ["Dammam King Fahd Airport", "Dammam - Airport", "DMM"],
        "Thrifty": ["Dammam Airport", "King Fahd Intl Airport"]
    },
    
    # Mecca
    "Mecca - City": {
        "Hertz": ["Mecca", "Makkah", "Mecca City"],
        "Budget": ["Mecca City", "Makkah"],
        "Thrifty": ["Mecca", "Makkah City"]
    },
    
    # Add more locations as needed
}

# ============================================================================
# CATEGORY MAPPING (Renty → Competitor)
# ============================================================================

CATEGORY_MAPPING = {
    "Economy": {
        "keywords": ["economy", "compact", "small", "mini", "basic", "budget"],
        "examples": ["Toyota Yaris", "Hyundai Accent", "Kia Picanto"],
        "Hertz": ["Economy", "Compact", "Mini"],
        "Budget": ["Economy Car", "Small Car", "Budget Car"],
        "Thrifty": ["Economy", "Compact Class"]
    },
    "Compact": {
        "keywords": ["compact", "small", "standard economy", "sedan compact"],
        "examples": ["Toyota Yaris", "Hyundai Elantra", "Kia Cerato"],
        "Hertz": ["Compact", "Standard Compact"],
        "Budget": ["Compact", "Compact Sedan"],
        "Thrifty": ["Compact", "Small Sedan"]
    },
    "Standard": {
        "keywords": ["standard", "midsize", "intermediate", "sedan", "medium"],
        "examples": ["Toyota Camry", "Hyundai Sonata", "Nissan Altima"],
        "Hertz": ["Standard", "Midsize", "Intermediate"],
        "Budget": ["Standard Sedan", "Midsize Car"],
        "Thrifty": ["Standard", "Mid-size"]
    },
    "SUV Compact": {
        "keywords": ["suv compact", "compact suv", "small suv", "crossover"],
        "examples": ["Hyundai Tucson", "Nissan Qashqai", "Kia Sportage"],
        "Hertz": ["Compact SUV", "Small SUV", "Crossover"],
        "Budget": ["Compact SUV", "Small 4x4"],
        "Thrifty": ["Compact SUV", "Small Crossover"]
    },
    "SUV Standard": {
        "keywords": ["suv standard", "suv", "midsize suv", "standard suv"],
        "examples": ["Toyota RAV4", "Nissan X-Trail", "Hyundai Santa Fe"],
        "Hertz": ["Standard SUV", "Midsize SUV", "SUV"],
        "Budget": ["Standard SUV", "Midsize 4x4"],
        "Thrifty": ["Standard SUV", "Mid-size SUV"]
    },
    "SUV Large": {
        "keywords": ["suv large", "full-size suv", "large suv", "premium suv"],
        "examples": ["Toyota Land Cruiser", "Nissan Patrol", "Chevrolet Tahoe"],
        "Hertz": ["Full-size SUV", "Large SUV", "Premium SUV"],
        "Budget": ["Full-size SUV", "Large 4x4"],
        "Thrifty": ["Full-size SUV", "Large SUV"]
    },
    "Luxury Sedan": {
        "keywords": ["luxury sedan", "premium sedan", "executive", "luxury car"],
        "examples": ["BMW 5 Series", "Mercedes E-Class", "Audi A6"],
        "Hertz": ["Luxury", "Premium Sedan", "Executive"],
        "Budget": ["Luxury Sedan", "Premium Car"],
        "Thrifty": ["Luxury", "Premium Sedan"]
    },
    "Luxury SUV": {
        "keywords": ["luxury suv", "premium suv", "executive suv"],
        "examples": ["BMW X5", "Mercedes GLE", "Audi Q7"],
        "Hertz": ["Luxury SUV", "Premium SUV", "Executive SUV"],
        "Budget": ["Luxury SUV", "Premium 4x4"],
        "Thrifty": ["Luxury SUV", "Premium SUV"]
    }
}

# ============================================================================
# SCRAPING SETTINGS
# ============================================================================

SCRAPING_SETTINGS = {
    "timeout": 30,  # Maximum time to wait for page load (seconds)
    "retry_attempts": 3,  # Number of retries if scraping fails
    "retry_delay": 5,  # Delay between retries (seconds)
    "parallel_scraping": True,  # Scrape competitors in parallel
    "cache_duration": 600,  # Cache results for 10 minutes (seconds)
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "headless": True,  # Run browser in headless mode
    "screenshot_on_error": True,  # Take screenshot if scraping fails
    "respect_robots_txt": True,  # Check robots.txt before scraping
}

# ============================================================================
# CACHE SETTINGS
# ============================================================================

CACHE_SETTINGS = {
    "enabled": True,
    "backend": "file",  # file, redis, or memory
    "cache_dir": "data/cache/competitor_prices",
    "ttl": 600,  # Time to live (seconds)
    "max_cache_size": 1000,  # Maximum number of cached entries
}

# ============================================================================
# ERROR HANDLING
# ============================================================================

FALLBACK_STRATEGY = {
    "use_cached_on_error": True,
    "show_last_known": True,
    "show_timestamp": True,
    "show_error_message": True,
    "default_message": "Unable to fetch current prices. Showing last known prices.",
    "cache_expiry_warning": "⚠️ Prices may be outdated (last updated: {timestamp})"
}

# ============================================================================
# FUZZY MATCHING SETTINGS
# ============================================================================

FUZZY_MATCH_SETTINGS = {
    "threshold": 70,  # Minimum similarity score (0-100)
    "algorithm": "token_sort_ratio",  # fuzzywuzzy algorithm
    "location_threshold": 75,
    "category_threshold": 70,
}

# ============================================================================
# LOGGING
# ============================================================================

LOGGING_SETTINGS = {
    "log_scraping_attempts": True,
    "log_cache_hits": True,
    "log_failures": True,
    "log_file": "logs/competitor_scraper.log",
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
}

