"""
Real-time competitor pricing using Booking.com API via RapidAPI
API: booking-com.p.rapidapi.com
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from car_model_category_mapping import get_correct_category, CAR_MODEL_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingComCarRentalAPI:
    """Integration with Booking.com Car Rental API for competitor pricing"""
    
    def __init__(self):
        self.api_key = "2d4ad88e62mshfb8fb27c0b4e2f8p1fbb48jsn854faa573903"
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
        
        # Branch coordinates (Riyadh, Jeddah, Dammam airports)
        self.branch_coordinates = {
            "King Khalid Airport - Riyadh": {"lat": 24.9576, "lon": 46.6987},
            "Riyadh - King Khalid International Airport": {"lat": 24.9576, "lon": 46.6987},
            "Olaya District - Riyadh": {"lat": 24.7136, "lon": 46.6753},
            "Riyadh - City": {"lat": 24.7136, "lon": 46.6753},
            
            "King Abdulaziz Airport - Jeddah": {"lat": 21.6796, "lon": 39.1564},
            "Jeddah - King Abdulaziz International Airport": {"lat": 21.6796, "lon": 39.1564},
            "Jeddah City Center": {"lat": 21.5433, "lon": 39.1728},
            
            "King Fahd Airport - Dammam": {"lat": 26.4711, "lon": 49.7979},
            "Dammam - King Fahd International Airport": {"lat": 26.4711, "lon": 49.7979},
            "Al Khobar Business District": {"lat": 26.2788, "lon": 50.2081},
            
            "Mecca City Center": {"lat": 21.4225, "lon": 39.8262},
            "Medina Downtown": {"lat": 24.4672, "lon": 39.6111},
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
            "from_country": "ar",
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
                                          drop_off_date: datetime) -> Dict[str, List[Dict]]:
        """
        Get competitor prices organized by Renty categories
        
        Returns:
        {
            "Economy": [
                {"supplier": "Alamo", "vehicle": "Nissan Sunny", "price": 251.61, "per_day": 125.81},
                ...
            ],
            "Compact": [...],
            ...
        }
        """
        results = self.search_car_rentals(branch_name, pick_up_date, drop_off_date)
        
        if not results:
            return {}
        
        # Calculate rental duration in days
        duration_days = (drop_off_date - pick_up_date).days
        if duration_days < 1:
            duration_days = 1
        
        # Organize by category
        category_prices = {cat: [] for cat in self.category_mapping.keys()}
        
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
                    category_prices[correct_category].append({
                        "supplier": supplier_name,
                        "vehicle": vehicle_name,
                        "total_price": round(total_price, 2),
                        "per_day": round(per_day_price, 2),
                        "category_original": booking_category,
                        "category_corrected": correct_category
                    })
                else:
                    logger.warning(f"Unknown category '{correct_category}' for {vehicle_name}")
            except Exception as e:
                logger.warning(f"Error processing car result: {str(e)}")
                continue
        
        return category_prices
    
    def get_competitor_prices_for_dashboard(self, branch_name: str, 
                                           date: datetime) -> Dict[str, Dict]:
        """
        Get competitor prices formatted for dashboard display
        
        Returns format matching the dashboard's expected structure:
        {
            "Economy": {
                "avg_price": 150.0,
                "competitors": [
                    {"Competitor_Name": "Alamo", "Competitor_Price": 125.81, "Date": "2025-12-01"},
                    ...
                ]
            },
            ...
        }
        """
        # Search for 2-day rental (standard comparison)
        pick_up = date
        drop_off = date + timedelta(days=2)
        
        category_data = self.get_competitor_prices_by_category(branch_name, pick_up, drop_off)
        
        dashboard_data = {}
        date_str = date.strftime("%Y-%m-%d %H:%M")
        
        for category, prices in category_data.items():
            if not prices:
                dashboard_data[category] = {
                    "avg_price": None,
                    "competitors": []
                }
                continue
            
            # Get top 5 competitors by price
            sorted_prices = sorted(prices, key=lambda x: x['per_day'])[:5]
            
            competitors = [
                {
                    "Competitor_Name": p['supplier'],
                    "Competitor_Price": p['per_day'],
                    "Date": date_str,
                    "Vehicle": p['vehicle']
                }
                for p in sorted_prices
            ]
            
            avg_price = sum(p['per_day'] for p in sorted_prices) / len(sorted_prices)
            
            dashboard_data[category] = {
                "avg_price": round(avg_price, 2),
                "competitors": competitors
            }
        
        return dashboard_data


# Singleton instance
_api_instance = None

def get_api_instance():
    """Get or create BookingComCarRentalAPI instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = BookingComCarRentalAPI()
    return _api_instance


# Main function for dashboard integration
def get_competitor_prices_for_dashboard(branch_name: str, category: str, date: datetime) -> Dict:
    """
    Get competitor prices for a specific branch and category
    Compatible with existing dashboard interface
    """
    api = get_api_instance()
    
    # Get all categories for this branch
    all_data = api.get_competitor_prices_for_dashboard(branch_name, date)
    
    # Return data for specific category
    if category in all_data:
        data = all_data[category]
        return {
            'avg_price': data['avg_price'],
            'min_price': min([c['Competitor_Price'] for c in data['competitors']]) if data['competitors'] else None,
            'max_price': max([c['Competitor_Price'] for c in data['competitors']]) if data['competitors'] else None,
            'competitors': data['competitors'],
            'competitor_count': len(data['competitors'])
        }
    else:
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'competitors': [],
            'competitor_count': 0
        }

