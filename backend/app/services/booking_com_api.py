"""
Real-time competitor pricing using Booking.com API via RapidAPI
API: booking-com.p.rapidapi.com

Integrated into Dynamic Pricing Tool - CHUNK 8
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)


# Car model to category mapping for accurate classification
CAR_MODEL_MAPPING = {
    # Economy - Small, fuel-efficient cars
    "Nissan Sunny": "Economy",
    "Toyota Yaris": "Economy",
    "Hyundai Accent": "Economy",
    "Kia Rio": "Economy",
    "Chevrolet Spark": "Economy",
    "Mitsubishi Mirage": "Economy",
    "Suzuki Swift": "Economy",
    "Honda City": "Economy",
    "Nissan Micra": "Economy",
    "Renault Symbol": "Economy",
    
    # Compact - Slightly larger economy cars
    "Toyota Corolla": "Compact",
    "Hyundai Elantra": "Compact",
    "Kia Cerato": "Compact",
    "Honda Civic": "Compact",
    "Mazda 3": "Compact",
    "Nissan Sentra": "Compact",
    "Chevrolet Cruze": "Compact",
    "Volkswagen Jetta": "Compact",
    "Mitsubishi Lancer": "Compact",
    "Kia Forte": "Compact",
    
    # Standard - Mid-size sedans
    "Toyota Camry": "Standard",
    "Honda Accord": "Standard",
    "Hyundai Sonata": "Standard",
    "Kia Optima": "Standard",
    "Nissan Altima": "Standard",
    "Mazda 6": "Standard",
    "Chevrolet Malibu": "Standard",
    "Ford Fusion": "Standard",
    "Volkswagen Passat": "Standard",
    "Kia K5": "Standard",
    
    # SUV Compact - Small SUVs/Crossovers
    "Hyundai Tucson": "SUV Compact",
    "Kia Sportage": "SUV Compact",
    "Toyota RAV4": "SUV Compact",
    "Honda CR-V": "SUV Compact",
    "Nissan Rogue": "SUV Compact",
    "Mazda CX-5": "SUV Compact",
    "Mitsubishi Outlander": "SUV Compact",
    "Ford Escape": "SUV Compact",
    "Chevrolet Equinox": "SUV Compact",
    "Jeep Compass": "SUV Compact",
    
    # SUV Standard - Mid-size SUVs
    "Toyota Fortuner": "SUV Standard",
    "Hyundai Santa Fe": "SUV Standard",
    "Kia Sorento": "SUV Standard",
    "Nissan Pathfinder": "SUV Standard",
    "Ford Explorer": "SUV Standard",
    "Chevrolet Traverse": "SUV Standard",
    "Honda Pilot": "SUV Standard",
    "Jeep Grand Cherokee": "SUV Standard",
    "Mitsubishi Pajero": "SUV Standard",
    "Toyota 4Runner": "SUV Standard",
    
    # SUV Large - Full-size SUVs
    "Toyota Land Cruiser": "SUV Large",
    "Nissan Patrol": "SUV Large",
    "Chevrolet Tahoe": "SUV Large",
    "GMC Yukon": "SUV Large",
    "Ford Expedition": "SUV Large",
    "Cadillac Escalade": "SUV Large",
    "Lexus LX": "SUV Large",
    "Infiniti QX80": "SUV Large",
    "Lincoln Navigator": "SUV Large",
    
    # Luxury Sedan
    "Mercedes-Benz E-Class": "Luxury Sedan",
    "BMW 5 Series": "Luxury Sedan",
    "Audi A6": "Luxury Sedan",
    "Lexus ES": "Luxury Sedan",
    "Mercedes-Benz S-Class": "Luxury Sedan",
    "BMW 7 Series": "Luxury Sedan",
    "Audi A8": "Luxury Sedan",
    "Lexus LS": "Luxury Sedan",
    "Genesis G80": "Luxury Sedan",
    "Genesis G90": "Luxury Sedan",
    
    # Luxury SUV
    "Mercedes-Benz GLE": "Luxury SUV",
    "BMW X5": "Luxury SUV",
    "Audi Q7": "Luxury SUV",
    "Porsche Cayenne": "Luxury SUV",
    "Range Rover": "Luxury SUV",
    "Range Rover Sport": "Luxury SUV",
    "Mercedes-Benz GLS": "Luxury SUV",
    "BMW X7": "Luxury SUV",
    "Audi Q8": "Luxury SUV",
    "Bentley Bentayga": "Luxury SUV",
}


def get_correct_category(vehicle_name: str, booking_category: str) -> str:
    """
    Get the correct Renty category for a vehicle.
    First tries exact model match, then falls back to booking category mapping.
    """
    # Check for exact model match
    for model, category in CAR_MODEL_MAPPING.items():
        if model.lower() in vehicle_name.lower():
            return category
    
    # Fall back to booking category mapping
    booking_to_renty = {
        "Mini": "Economy",
        "Economy": "Economy",
        "Compact": "Compact",
        "Intermediate": "Standard",
        "Standard": "Standard",
        "Fullsize": "Standard",
        "Full-size": "Standard",
        "Compact SUV": "SUV Compact",
        "SUV": "SUV Standard",
        "Intermediate SUV": "SUV Standard",
        "Standard SUV": "SUV Standard",
        "Large SUV": "SUV Large",
        "Premium SUV": "SUV Large",
        "Luxury": "Luxury Sedan",
        "Premium": "Luxury Sedan",
        "Luxury Car": "Luxury Sedan",
        "Luxury SUV": "Luxury SUV",
    }
    
    return booking_to_renty.get(booking_category, "Standard")


@dataclass
class BookingComPrice:
    """Price data from Booking.com API"""
    supplier: str
    vehicle: str
    total_price: Decimal
    per_day_price: Decimal
    category_original: str
    category_corrected: str
    currency: str = "SAR"


class BookingComCarRentalAPI:
    """Integration with Booking.com Car Rental API for competitor pricing"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "2d4ad88e62mshfb8fb27c0b4e2f8p1fbb48jsn854faa573903"
        self.api_host = "booking-com.p.rapidapi.com"
        self.base_url = f"https://{self.api_host}/v1/car-rental"
        
        # Map Renty categories to Booking.com categories
        self.category_mapping = {
            "Economy": ["Economy", "Mini"],
            "Compact": ["Compact", "Economy"],
            "Standard": ["Standard", "Intermediate", "Fullsize"],
            "SUV Compact": ["Compact SUV", "SUV"],
            "SUV Standard": ["Standard SUV", "SUV", "Intermediate SUV"],
            "SUV Large": ["Large SUV", "Premium SUV", "SUV"],
            "Luxury Sedan": ["Luxury", "Premium", "Luxury Car"],
            "Luxury SUV": ["Luxury SUV", "Premium SUV", "Luxury"]
        }
        
        # Branch coordinates (Riyadh, Jeddah, Dammam airports and cities)
        self.branch_coordinates = {
            # Riyadh
            "King Khalid Airport - Riyadh": {"lat": 24.9576, "lon": 46.6987},
            "Riyadh - King Khalid International Airport": {"lat": 24.9576, "lon": 46.6987},
            "Riyadh Airport": {"lat": 24.9576, "lon": 46.6987},
            "Olaya District - Riyadh": {"lat": 24.7136, "lon": 46.6753},
            "Riyadh - City": {"lat": 24.7136, "lon": 46.6753},
            "Riyadh City": {"lat": 24.7136, "lon": 46.6753},
            "Riyadh": {"lat": 24.7136, "lon": 46.6753},
            
            # Jeddah
            "King Abdulaziz Airport - Jeddah": {"lat": 21.6796, "lon": 39.1564},
            "Jeddah - King Abdulaziz International Airport": {"lat": 21.6796, "lon": 39.1564},
            "Jeddah Airport": {"lat": 21.6796, "lon": 39.1564},
            "Jeddah City Center": {"lat": 21.5433, "lon": 39.1728},
            "Jeddah": {"lat": 21.5433, "lon": 39.1728},
            
            # Dammam
            "King Fahd Airport - Dammam": {"lat": 26.4711, "lon": 49.7979},
            "Dammam - King Fahd International Airport": {"lat": 26.4711, "lon": 49.7979},
            "Dammam Airport": {"lat": 26.4711, "lon": 49.7979},
            "Al Khobar Business District": {"lat": 26.2788, "lon": 50.2081},
            "Dammam": {"lat": 26.4711, "lon": 49.7979},
            
            # Other cities
            "Mecca City Center": {"lat": 21.4225, "lon": 39.8262},
            "Medina Downtown": {"lat": 24.4672, "lon": 39.6111},
        }
        
        # Map branch IDs to city names for coordinate lookup
        self.branch_id_to_location = {
            122: "Riyadh Airport",
            2: "Riyadh City",
            211: "Riyadh City",
            15: "Jeddah Airport",
            34: "Jeddah",
            26: "Dammam Airport",
        }
    
    def _get_coordinates(self, branch_name: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a branch, with fuzzy matching"""
        # Exact match
        if branch_name in self.branch_coordinates:
            return self.branch_coordinates[branch_name]
        
        # Fuzzy match - check if branch name contains key
        for key, coords in self.branch_coordinates.items():
            if key.lower() in branch_name.lower() or branch_name.lower() in key.lower():
                return coords
        
        # Default to Riyadh
        logger.warning(f"Branch '{branch_name}' not found, using Riyadh as default")
        return {"lat": 24.9576, "lon": 46.6987}
    
    def get_location_for_branch_id(self, branch_id: int) -> str:
        """Get location name for a branch ID"""
        return self.branch_id_to_location.get(branch_id, "Riyadh")
    
    def search_car_rentals(self, branch_name: str, pick_up_date: datetime, 
                          drop_off_date: datetime) -> List[Dict]:
        """
        Search for car rentals at a specific location and date range
        
        Returns list of car rental options with pricing
        """
        coords = self._get_coordinates(branch_name)
        if not coords:
            logger.error(f"Could not find coordinates for branch: {branch_name}")
            return []
        
        url = f"{self.base_url}/search"
        
        headers = {
            "x-rapidapi-host": self.api_host,
            "x-rapidapi-key": self.api_key
        }
        
        # Format datetime as "YYYY-MM-DD HH:MM:SS"
        pick_up_str = pick_up_date.strftime("%Y-%m-%d 10:00:00")
        drop_off_str = drop_off_date.strftime("%Y-%m-%d 10:00:00")
        
        params = {
            "pick_up_latitude": coords["lat"],
            "pick_up_longitude": coords["lon"],
            "drop_off_latitude": coords["lat"],
            "drop_off_longitude": coords["lon"],
            "pick_up_datetime": pick_up_str,
            "drop_off_datetime": drop_off_str,
            "currency": "SAR",
            "locale": "en-gb",
            "from_country": "it",  # Use 'it' as Booking.com doesn't support 'sa'
            "sort_by": "recommended"
        }
        
        try:
            logger.info(f"Searching car rentals for {branch_name} ({coords['lat']}, {coords['lon']})")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'search_results' in data:
                    results = data['search_results']
                    logger.info(f"Found {len(results)} car rental options for {branch_name}")
                    return results
                else:
                    logger.warning(f"No search_results in API response for {branch_name}")
                    return []
            else:
                logger.error(f"API returned status {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching car rentals: {str(e)}")
            return []
    
    def get_competitor_prices_by_category(self, branch_name: str, 
                                          pick_up_date: datetime,
                                          drop_off_date: datetime) -> Dict[str, List[BookingComPrice]]:
        """
        Get competitor prices organized by Renty categories
        
        Returns dict of category -> list of BookingComPrice
        """
        results = self.search_car_rentals(branch_name, pick_up_date, drop_off_date)
        
        if not results:
            return {}
        
        # Calculate rental duration in days
        duration_days = (drop_off_date - pick_up_date).days
        if duration_days < 1:
            duration_days = 1
        
        # Organize by category
        category_prices: Dict[str, List[BookingComPrice]] = {
            cat: [] for cat in self.category_mapping.keys()
        }
        
        for car in results:
            try:
                # Extract data
                vehicle_info = car.get('vehicle_info', {})
                pricing_info = car.get('pricing_info', {})
                supplier_info = car.get('supplier_info', {})
                
                booking_category = vehicle_info.get('group', '')
                vehicle_name = vehicle_info.get('v_name', 'Unknown')
                total_price = pricing_info.get('price', 0)
                supplier_name = supplier_info.get('name', 'Unknown')
                
                # Calculate per-day price
                per_day_price = total_price / duration_days if total_price > 0 else 0
                
                # Map to Renty category using accurate car-by-car mapping
                correct_category = get_correct_category(vehicle_name, booking_category)
                
                # Add to the correct category
                if correct_category in category_prices:
                    category_prices[correct_category].append(BookingComPrice(
                        supplier=supplier_name,
                        vehicle=vehicle_name,
                        total_price=Decimal(str(round(total_price, 2))),
                        per_day_price=Decimal(str(round(per_day_price, 2))),
                        category_original=booking_category,
                        category_corrected=correct_category
                    ))
                else:
                    logger.warning(f"Unknown category '{correct_category}' for {vehicle_name}")
            except Exception as e:
                logger.warning(f"Error processing car result: {str(e)}")
                continue
        
        return category_prices
    
    def get_competitor_prices_for_date(self, branch_name: str, 
                                       price_date: datetime) -> Dict[str, Dict]:
        """
        Get competitor prices for a specific date (2-day rental comparison)
        
        Returns format:
        {
            "Economy": {
                "avg_price": 150.0,
                "min_price": 125.0,
                "max_price": 175.0,
                "competitors": [
                    {"supplier": "Alamo", "vehicle": "Nissan Sunny", "price": 125.81},
                    ...
                ]
            },
            ...
        }
        """
        # Search for 2-day rental (standard comparison)
        pick_up = price_date
        drop_off = price_date + timedelta(days=2)
        
        category_data = self.get_competitor_prices_by_category(branch_name, pick_up, drop_off)
        
        result = {}
        
        for category, prices in category_data.items():
            if not prices:
                result[category] = {
                    "avg_price": None,
                    "min_price": None,
                    "max_price": None,
                    "competitors": [],
                    "competitor_count": 0
                }
                continue
            
            # Deduplicate by supplier - keep LOWEST price per supplier
            supplier_best_prices: Dict[str, BookingComPrice] = {}
            for p in prices:
                if p.supplier not in supplier_best_prices or p.per_day_price < supplier_best_prices[p.supplier].per_day_price:
                    supplier_best_prices[p.supplier] = p
            
            # Get top 4 suppliers by price
            sorted_prices = sorted(supplier_best_prices.values(), key=lambda x: x.per_day_price)[:4]
            
            per_day_prices = [float(p.per_day_price) for p in sorted_prices]
            
            result[category] = {
                "avg_price": round(sum(per_day_prices) / len(per_day_prices), 2),
                "min_price": round(min(per_day_prices), 2),
                "max_price": round(max(per_day_prices), 2),
                "competitors": [
                    {
                        "supplier": p.supplier,
                        "vehicle": p.vehicle,
                        "price": float(p.per_day_price)
                    }
                    for p in sorted_prices
                ],
                "competitor_count": len(sorted_prices)
            }
        
        return result


# Singleton instance
_api_instance: Optional[BookingComCarRentalAPI] = None


def get_booking_api() -> BookingComCarRentalAPI:
    """Get or create BookingComCarRentalAPI instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = BookingComCarRentalAPI()
    return _api_instance
