"""
Accurate Car Model to Category Mapping
Based on industry standards and actual vehicle specifications

This mapping is used to correctly categorize competitor vehicles from the API
into Renty's category system.
"""

# Comprehensive car model mapping
# Format: "Vehicle Name": {"renty_category": "Category", "type": "Type", "notes": "Additional info"}

CAR_MODEL_MAPPING = {
    # ECONOMY - Subcompact and Small Economy Cars
    "Chevrolet Spark": {
        "renty_category": "Economy",
        "type": "Subcompact Hatchback",
        "seats": 4,
        "notes": "City car, very fuel efficient"
    },
    "Kia Picanto": {
        "renty_category": "Economy",
        "type": "Subcompact Hatchback",
        "seats": 4,
        "notes": "Similar to Spark"
    },
    "Hyundai i10": {
        "renty_category": "Economy",
        "type": "Subcompact Hatchback",
        "seats": 4,
        "notes": "Economy city car"
    },
    
    # COMPACT - Compact Sedans (NOT SUVs)
    "Nissan Sunny": {
        "renty_category": "Compact",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Popular compact sedan in Middle East"
    },
    "Hyundai Accent": {
        "renty_category": "Compact",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Compact sedan, good for city/highway"
    },
    "Kia Cerato": {
        "renty_category": "Compact",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Compact sedan, spacious"
    },
    "Toyota Yaris": {
        "renty_category": "Compact",
        "type": "Compact Sedan/Hatchback",
        "seats": 5,
        "notes": "Reliable compact"
    },
    "Kia Pegas": {
        "renty_category": "Compact",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Budget compact sedan"
    },
    
    # STANDARD - Mid-size Sedans
    "Hyundai Elantra": {
        "renty_category": "Standard",
        "type": "Compact/Mid-size Sedan",
        "seats": 5,
        "notes": "Between compact and standard"
    },
    "Changan Eado": {
        "renty_category": "Standard",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Chinese brand, compact sedan"
    },
    "Toyota Camry": {
        "renty_category": "Standard",
        "type": "Mid-size Sedan",
        "seats": 5,
        "notes": "Best-selling mid-size sedan"
    },
    "Hyundai Sonata": {
        "renty_category": "Standard",
        "type": "Mid-size Sedan",
        "seats": 5,
        "notes": "Popular mid-size"
    },
    "Nissan Altima": {
        "renty_category": "Standard",
        "type": "Mid-size Sedan",
        "seats": 5,
        "notes": "Comfortable mid-size"
    },
    "Toyota Corolla": {
        "renty_category": "Standard",
        "type": "Compact/Mid-size Sedan",
        "seats": 5,
        "notes": "World's best-selling car"
    },
    "Chevrolet Malibu": {
        "renty_category": "Standard",
        "type": "Mid-size Sedan",
        "seats": 5,
        "notes": "American mid-size sedan"
    },
    "Ford Taurus": {
        "renty_category": "Standard",
        "type": "Full-size Sedan",
        "seats": 5,
        "notes": "Large American sedan"
    },
    "Dodge Neon": {
        "renty_category": "Standard",
        "type": "Compact Sedan",
        "seats": 5,
        "notes": "Compact/standard sedan"
    },
    "BYD Seal 7": {
        "renty_category": "Standard",
        "type": "Mid-size Electric Sedan",
        "seats": 5,
        "notes": "Chinese electric sedan"
    },
    
    # SUV COMPACT - Compact SUVs and Crossovers
    "GAC GS3": {
        "renty_category": "SUV Compact",
        "type": "Compact SUV/Crossover",
        "seats": 5,
        "notes": "Chinese brand compact SUV"
    },
    "Hyundai Tucson": {
        "renty_category": "SUV Compact",
        "type": "Compact SUV",
        "seats": 5,
        "notes": "Popular compact SUV"
    },
    "Hyundai Creta": {
        "renty_category": "SUV Compact",
        "type": "Compact SUV",
        "seats": 5,
        "notes": "Subcompact SUV popular in Middle East"
    },
    "Hyundai Kona": {
        "renty_category": "SUV Compact",
        "type": "Subcompact SUV/Crossover",
        "seats": 5,
        "notes": "Electric/hybrid subcompact SUV"
    },
    "Nissan Qashqai": {
        "renty_category": "SUV Compact",
        "type": "Compact Crossover",
        "seats": 5,
        "notes": "Compact crossover SUV"
    },
    "Kia Sportage": {
        "renty_category": "SUV Compact",
        "type": "Compact SUV",
        "seats": 5,
        "notes": "Spacious compact SUV"
    },
    
    # SUV STANDARD - Mid-size SUVs
    "Toyota RAV4": {
        "renty_category": "SUV Standard",
        "type": "Compact/Mid-size SUV",
        "seats": 5,
        "notes": "Best-selling SUV"
    },
    "Toyota Fortuner": {
        "renty_category": "SUV Standard",
        "type": "Mid-size SUV",
        "seats": 7,
        "notes": "Body-on-frame mid-size SUV, popular in Middle East"
    },
    "Nissan X-Trail": {
        "renty_category": "SUV Standard",
        "type": "Mid-size SUV",
        "seats": 7,
        "notes": "3-row option available"
    },
    "Hyundai Santa Fe": {
        "renty_category": "SUV Standard",
        "type": "Mid-size SUV",
        "seats": 7,
        "notes": "3-row mid-size SUV"
    },
    
    # SUV LARGE - Full-size/Large SUVs
    "Toyota Highlander": {
        "renty_category": "SUV Large",
        "type": "Mid-size/Large 3-Row SUV",
        "seats": 8,
        "notes": "CURRENTLY MISCLASSIFIED AS LUXURY SEDAN - Should be SUV Large"
    },
    "Toyota Land Cruiser": {
        "renty_category": "SUV Large",
        "type": "Full-size SUV",
        "seats": 8,
        "notes": "Flagship large SUV"
    },
    "Toyota Land Cruiser Prado": {
        "renty_category": "SUV Large",
        "type": "Mid-size/Large SUV",
        "seats": 7,
        "notes": "CURRENTLY MISCLASSIFIED AS LUXURY SEDAN - Should be SUV Large"
    },
    "Toyota Land Cruiser Prado GPS": {
        "renty_category": "SUV Large",
        "type": "Mid-size/Large SUV",
        "seats": 7,
        "notes": "Same as Prado but with GPS - MISCLASSIFIED AS LUXURY SEDAN"
    },
    "Nissan Patrol": {
        "renty_category": "SUV Large",
        "type": "Full-size SUV",
        "seats": 8,
        "notes": "Large luxury SUV"
    },
    "Chevrolet Tahoe": {
        "renty_category": "SUV Large",
        "type": "Full-size SUV",
        "seats": 8,
        "notes": "American full-size SUV"
    },
    
    # LUXURY SEDAN - Premium/Luxury Sedans
    "Chrysler 300C": {
        "renty_category": "Luxury Sedan",
        "type": "Full-size Luxury Sedan",
        "seats": 5,
        "notes": "American luxury sedan - CORRECTLY CLASSIFIED"
    },
    "BMW 5 Series": {
        "renty_category": "Luxury Sedan",
        "type": "Mid-size Luxury Sedan",
        "seats": 5,
        "notes": "German luxury sedan - CORRECTLY CLASSIFIED"
    },
    "Mercedes E-Class": {
        "renty_category": "Luxury Sedan",
        "type": "Mid-size Luxury Sedan",
        "seats": 5,
        "notes": "German luxury sedan"
    },
    "Audi A6": {
        "renty_category": "Luxury Sedan",
        "type": "Mid-size Luxury Sedan",
        "seats": 5,
        "notes": "German luxury sedan"
    },
    "Audi A4": {
        "renty_category": "Luxury Sedan",
        "type": "Compact Luxury Sedan",
        "seats": 5,
        "notes": "Entry luxury sedan - Could also be Premium/Standard depending on trim"
    },
    
    # LUXURY SUV - Premium/Luxury SUVs
    "BMW X1": {
        "renty_category": "SUV Compact",
        "type": "Compact Luxury SUV",
        "seats": 5,
        "notes": "Compact luxury SUV"
    },
    "BMW X2": {
        "renty_category": "SUV Compact",
        "type": "Compact Luxury SUV/Crossover",
        "seats": 5,
        "notes": "Compact luxury crossover SUV"
    },
    "BMW X3": {
        "renty_category": "SUV Standard",
        "type": "Mid-size Luxury SUV",
        "seats": 5,
        "notes": "Mid-size luxury SUV"
    },
    "BMW X4": {
        "renty_category": "SUV Standard",
        "type": "Mid-size Luxury SUV Coupe",
        "seats": 5,
        "notes": "Sport luxury SUV"
    },
    "BMW X5": {
        "renty_category": "Luxury SUV",
        "type": "Mid-size Luxury SUV",
        "seats": 7,
        "notes": "German luxury SUV"
    },
    "BMW X6": {
        "renty_category": "Luxury SUV",
        "type": "Mid-size Luxury SUV Coupe",
        "seats": 5,
        "notes": "Sport luxury SUV"
    },
    "BMW X7": {
        "renty_category": "Luxury SUV",
        "type": "Full-size Luxury SUV",
        "seats": 7,
        "notes": "Large luxury SUV"
    },
    "Mercedes GLE": {
        "renty_category": "Luxury SUV",
        "type": "Mid-size Luxury SUV",
        "seats": 7,
        "notes": "German luxury SUV"
    },
    "Audi Q7": {
        "renty_category": "Luxury SUV",
        "type": "Mid-size Luxury SUV",
        "seats": 7,
        "notes": "German luxury SUV"
    },
    "Range Rover": {
        "renty_category": "Luxury SUV",
        "type": "Full-size Luxury SUV",
        "seats": 7,
        "notes": "British luxury SUV"
    }
}

# Reverse mapping: Booking.com category -> Renty category
# This is what the API returns as "group"
BOOKING_CATEGORY_MAPPING = {
    # Economy mappings
    "Economy": "Economy",
    "Mini": "Economy",
    "Subcompact": "Economy",
    
    # Compact sedan mappings (NOT SUVs)
    "Compact": "Compact",
    
    # Standard sedan mappings
    "Standard": "Standard",
    "Intermediate": "Standard",
    "Fullsize": "Standard",
    "Full Size": "Standard",
    
    # SUV mappings - need to check actual vehicle model
    "SUV": "NEEDS_MODEL_CHECK",  # Could be Compact, Standard, or Large SUV
    "Compact SUV": "SUV Compact",
    "Small SUV": "SUV Compact",
    "Standard SUV": "SUV Standard",
    "Intermediate SUV": "SUV Standard",
    "Medium SUV": "SUV Standard",
    "Large SUV": "SUV Large",
    "Full-size SUV": "SUV Large",
    
    # Luxury mappings - need to check if sedan or SUV
    "Luxury": "NEEDS_MODEL_CHECK",  # Could be Luxury Sedan or Luxury SUV
    "Premium": "NEEDS_MODEL_CHECK",
    "Luxury Car": "Luxury Sedan",
    "Premium Car": "Luxury Sedan",
    "Luxury SUV": "Luxury SUV",
    "Premium SUV": "Luxury SUV",
}

def get_correct_category(vehicle_name: str, booking_category: str) -> str:
    """
    Get the correct Renty category for a vehicle
    
    Args:
        vehicle_name: Name of the vehicle (e.g., "Toyota Highlander")
        booking_category: Category from Booking.com API (e.g., "Luxury")
    
    Returns:
        Correct Renty category
    """
    # First, try exact match on vehicle name
    vehicle_clean = vehicle_name.strip()
    
    if vehicle_clean in CAR_MODEL_MAPPING:
        return CAR_MODEL_MAPPING[vehicle_clean]["renty_category"]
    
    # Try partial match (e.g., "Hyundai Elantra  " matches "Hyundai Elantra")
    for model_name, mapping in CAR_MODEL_MAPPING.items():
        if model_name.lower() in vehicle_clean.lower():
            return mapping["renty_category"]
    
    # Fall back to booking category if available
    if booking_category in BOOKING_CATEGORY_MAPPING:
        mapped = BOOKING_CATEGORY_MAPPING[booking_category]
        
        # If needs model check, make best guess
        if mapped == "NEEDS_MODEL_CHECK":
            # Check if it's an SUV
            if any(suv_indicator in vehicle_clean.upper() for suv_indicator in 
                   ["SUV", "CRUISER", "PATROL", "TAHOE", "HIGHLANDER", "PRADO", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "GLE", "Q7"]):
                # Determine size
                if any(large in vehicle_clean.upper() for large in 
                       ["LAND CRUISER", "PATROL", "TAHOE", "HIGHLANDER"]):
                    return "SUV Large"
                elif any(x in vehicle_clean for x in ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "GLE", "GLC", "Q3", "Q5", "Q7", "Q8"]):
                    return "Luxury SUV"
                else:
                    return "SUV Standard"
            else:
                # It's a sedan
                if booking_category in ["Luxury", "Premium"]:
                    return "Luxury Sedan"
                else:
                    return "Standard"
        
        return mapped
    
    # Default fallback based on booking category text
    if "luxury" in booking_category.lower() or "premium" in booking_category.lower():
        return "Luxury Sedan"
    elif "suv" in booking_category.lower():
        return "SUV Standard"
    else:
        return "Standard"

# Critical misclassifications fixed
FIXED_MISCLASSIFICATIONS = [
    {
        "vehicle": "Toyota Highlander",
        "api_says": "Luxury",
        "should_be": "SUV Large",
        "reason": "3-row mid-size/large SUV, not a sedan"
    },
    {
        "vehicle": "Toyota Land Cruiser Prado",
        "api_says": "Luxury",
        "should_be": "SUV Large",
        "reason": "Large SUV, not a sedan"
    },
    {
        "vehicle": "GAC GS3",
        "api_says": "Compact",
        "should_be": "SUV Compact",
        "reason": "Compact SUV/crossover, not a sedan"
    },
    {
        "vehicle": "Hyundai Creta",
        "api_says": "Compact",
        "should_be": "SUV Compact",
        "reason": "Subcompact SUV, not a sedan"
    },
    {
        "vehicle": "Toyota Fortuner",
        "api_says": "Standard",
        "should_be": "SUV Standard",
        "reason": "Mid-size SUV, not a sedan"
    }
]

# API Suppliers Available (from Booking.com API):
# - Alamo
# - Enterprise
# - Sixt
# 
# NOT available from this API:
# - Budget
# - Thrifty
# - Theeb (local Saudi competitor)

