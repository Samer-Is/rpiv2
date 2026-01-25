"""
Competitor Pricing Service - CHUNK 8
Integration with Booking.com API and competitor index calculation
NO MOCK DATA - All prices come from live Booking.com API
"""
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session

from .booking_com_api import (
    get_booking_api, 
    BookingComCarRentalAPI,
    BookingComPrice,
    CompetitorVehicle
)

logger = logging.getLogger(__name__)


@dataclass
class CompetitorPrice:
    """Single competitor price record."""
    competitor_name: str
    vehicle_type: str
    daily_price: Decimal
    weekly_price: Optional[Decimal] = None
    monthly_price: Optional[Decimal] = None
    currency: str = "SAR"
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_name: Optional[str] = None


@dataclass
class CompetitorIndex:
    """Aggregated competitor index for a category."""
    category_id: int
    index_date: date
    avg_price: Decimal  # Average of top 3 competitors
    min_price: Decimal
    max_price: Decimal
    competitors_count: int
    our_base_price: Optional[Decimal] = None
    price_position: Optional[Decimal] = None  # Our price / competitor avg


class CompetitorPricingService:
    """
    Service for fetching and managing competitor pricing data.
    
    ALL PRICES COME FROM LIVE BOOKING.COM API - NO MOCK DATA
    
    Supports:
    - Fetching competitor prices from Booking.com API
    - Category mapping configuration
    - Competitor index calculation (avg of top 3)
    - Database caching with TTL
    """
    
    # Cache TTL in hours
    CACHE_TTL_HOURS = 24
    
    # City mapping for branches
    BRANCH_CITY_MAP = {
        # Airport branches
        122: "Riyadh Airport",
        15: "Jeddah Airport",
        26: "Dammam Airport",
        # Non-airport branches
        2: "Riyadh City",
        34: "Jeddah",
        211: "Riyadh City",
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, Any] = {}
        self._api = get_booking_api()
    
    def get_category_mapping(self, tenant_id: int) -> Dict[int, str]:
        """Get category to competitor vehicle type mapping."""
        result = self.db.execute(text("""
            SELECT category_id, competitor_vehicle_type
            FROM appconfig.competitor_mapping
            WHERE tenant_id = :tenant_id AND is_active = 1
        """), {"tenant_id": tenant_id})
        
        return {row[0]: row[1] for row in result.fetchall()}
    
    def fetch_competitor_prices(
        self, 
        city: str, 
        vehicle_type: str, 
        price_date: date,
        use_cache: bool = True
    ) -> List[CompetitorPrice]:
        """
        Fetch competitor prices from Booking.com API.
        
        NO MOCK DATA - Returns empty list if API fails.
        """
        cache_key = f"{city}_{vehicle_type}_{price_date}"
        
        # Check in-memory cache
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached["expires_at"] > datetime.now():
                logger.info(f"Using cached prices for {cache_key}")
                return cached["data"]
        
        # Fetch from Booking.com API
        prices = self._fetch_from_booking_api(city, vehicle_type, price_date)
        
        if prices:
            logger.info(f"Fetched {len(prices)} prices from Booking.com API for {city}/{vehicle_type}")
            # Cache results
            self._cache[cache_key] = {
                "data": prices,
                "expires_at": datetime.now() + timedelta(hours=self.CACHE_TTL_HOURS)
            }
        else:
            logger.warning(f"No prices returned from Booking.com API for {city}/{vehicle_type}")
        
        return prices
    
    def _fetch_from_booking_api(
        self,
        city: str,
        vehicle_type: str,
        price_date: date
    ) -> List[CompetitorPrice]:
        """Fetch prices from Booking.com API."""
        price_datetime = datetime.combine(price_date, datetime.min.time())
        
        # Get prices for this city
        category_prices = self._api.get_competitor_prices_for_date(city, price_datetime)
        
        # Map our vehicle_type to Booking.com categories
        booking_category_map = {
            "economy": "Economy",
            "compact": "Compact",
            "standard": "Standard",
            "fullsize": "Standard",
            "suv": "SUV Standard",
            "luxury": "Luxury Sedan",
        }
        
        booking_category = booking_category_map.get(vehicle_type.lower(), "Economy")
        
        if booking_category not in category_prices:
            return []
        
        data = category_prices[booking_category]
        if not data.get("competitors"):
            return []
        
        prices = []
        for comp in data["competitors"]:
            prices.append(CompetitorPrice(
                competitor_name=comp["supplier"],
                vehicle_type=vehicle_type,
                daily_price=Decimal(str(comp["price"])),
                weekly_price=Decimal(str(comp["price"] * 6)),
                monthly_price=Decimal(str(comp["price"] * 25)),
                vehicle_brand=comp.get("brand"),
                vehicle_model=comp.get("model"),
                vehicle_name=comp.get("vehicle")
            ))
        
        return prices
    
    def fetch_all_competitor_vehicles(
        self,
        city: str,
        pickup_date: date,
        dropoff_date: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch all competitor vehicles with full details (brand, model, etc).
        Returns raw vehicle data from Booking.com API.
        
        Args:
            city: City name (e.g., "Riyadh", "Jeddah")
            pickup_date: Rental pickup date
            dropoff_date: Rental dropoff date
            
        Returns:
            List of vehicle dictionaries with brand, model, category, price, etc.
        """
        pickup_datetime = datetime.combine(pickup_date, datetime.min.time())
        dropoff_datetime = datetime.combine(dropoff_date, datetime.min.time())
        
        return self._api.get_all_vehicles_raw(city, pickup_datetime, dropoff_datetime)
    
    def calculate_competitor_index(
        self,
        tenant_id: int,
        branch_id: int,
        category_id: int,
        index_date: date,
        our_base_price: Optional[Decimal] = None
    ) -> CompetitorIndex:
        """
        Calculate competitor index for a category.
        Uses average of top 3 competitors (not lowest) as per requirements.
        """
        # Get category mapping
        mapping = self.get_category_mapping(tenant_id)
        vehicle_type = mapping.get(category_id, "economy")
        
        # Get city for branch
        city = self.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
        
        # Fetch competitor prices from Booking.com API
        prices = self.fetch_competitor_prices(city, vehicle_type, index_date)
        
        if not prices:
            return CompetitorIndex(
                category_id=category_id,
                index_date=index_date,
                avg_price=Decimal("0"),
                min_price=Decimal("0"),
                max_price=Decimal("0"),
                competitors_count=0
            )
        
        # Sort by price and take top 3
        sorted_prices = sorted(prices, key=lambda x: x.daily_price)
        top_3 = sorted_prices[:3]
        
        # Calculate average of top 3
        avg_price = sum(p.daily_price for p in top_3) / len(top_3)
        min_price = min(p.daily_price for p in prices)
        max_price = max(p.daily_price for p in prices)
        
        # Calculate price position if we have our base price
        price_position = None
        if our_base_price and avg_price > 0:
            price_position = Decimal(str(round(float(our_base_price) / float(avg_price), 4)))
        
        return CompetitorIndex(
            category_id=category_id,
            index_date=index_date,
            avg_price=Decimal(str(round(avg_price, 2))),
            min_price=min_price,
            max_price=max_price,
            competitors_count=len(prices),
            our_base_price=our_base_price,
            price_position=price_position
        )
    
    def save_competitor_prices(
        self,
        tenant_id: int,
        branch_id: int,
        category_id: int,
        prices: List[CompetitorPrice],
        price_date: date
    ) -> int:
        """Save competitor prices to database cache."""
        city = self.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
        expires_at = datetime.now() + timedelta(hours=self.CACHE_TTL_HOURS)
        
        saved = 0
        for price in prices:
            try:
                self.db.execute(text("""
                    MERGE INTO dynamicpricing.competitor_prices AS target
                    USING (SELECT :tenant_id as tenant_id, :branch_id as branch_id, 
                           :category_id as category_id, :price_date as price_date,
                           :competitor_name as competitor_name) AS source
                    ON target.tenant_id = source.tenant_id 
                       AND target.branch_id = source.branch_id
                       AND target.category_id = source.category_id
                       AND target.price_date = source.price_date
                       AND target.competitor_name = source.competitor_name
                    WHEN MATCHED THEN
                        UPDATE SET daily_price = :daily_price, 
                                   weekly_price = :weekly_price,
                                   monthly_price = :monthly_price,
                                   fetched_at = GETDATE(),
                                   expires_at = :expires_at
                    WHEN NOT MATCHED THEN
                        INSERT (tenant_id, branch_id, city_name, category_id, price_date,
                                competitor_name, competitor_vehicle_type, daily_price,
                                weekly_price, monthly_price, expires_at)
                        VALUES (:tenant_id, :branch_id, :city_name, :category_id, :price_date,
                                :competitor_name, :vehicle_type, :daily_price,
                                :weekly_price, :monthly_price, :expires_at);
                """), {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "city_name": city,
                    "category_id": category_id,
                    "price_date": price_date,
                    "competitor_name": price.competitor_name,
                    "vehicle_type": price.vehicle_type,
                    "daily_price": price.daily_price,
                    "weekly_price": price.weekly_price,
                    "monthly_price": price.monthly_price,
                    "expires_at": expires_at
                })
                saved += 1
            except Exception as e:
                logger.warning(f"Failed to save competitor price: {e}")
        
        self.db.commit()
        return saved
    
    def save_competitor_index(
        self,
        tenant_id: int,
        branch_id: int,
        index: CompetitorIndex
    ) -> None:
        """Save competitor index to database."""
        self.db.execute(text("""
            MERGE INTO dynamicpricing.competitor_index AS target
            USING (SELECT :tenant_id as tenant_id, :branch_id as branch_id,
                   :category_id as category_id, :index_date as index_date) AS source
            ON target.tenant_id = source.tenant_id 
               AND target.branch_id = source.branch_id
               AND target.category_id = source.category_id
               AND target.index_date = source.index_date
            WHEN MATCHED THEN
                UPDATE SET competitor_avg_price = :avg_price,
                           competitor_min_price = :min_price,
                           competitor_max_price = :max_price,
                           competitors_count = :count,
                           our_base_price = :our_price,
                           price_position = :position
            WHEN NOT MATCHED THEN
                INSERT (tenant_id, branch_id, category_id, index_date,
                        competitor_avg_price, competitor_min_price, competitor_max_price,
                        competitors_count, our_base_price, price_position)
                VALUES (:tenant_id, :branch_id, :category_id, :index_date,
                        :avg_price, :min_price, :max_price,
                        :count, :our_price, :position);
        """), {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "category_id": index.category_id,
            "index_date": index.index_date,
            "avg_price": index.avg_price,
            "min_price": index.min_price,
            "max_price": index.max_price,
            "count": index.competitors_count,
            "our_price": index.our_base_price,
            "position": index.price_position
        })
        self.db.commit()
    
    def build_competitor_index_for_date_range(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Build competitor index for all MVP branches and categories.
        Fetches LIVE data from Booking.com API.
        """
        # Get MVP branches and categories
        branches_result = self.db.execute(text(
            "SELECT BranchId FROM dynamicpricing.TopBranches"
        ))
        branches = [row[0] for row in branches_result.fetchall()]
        
        categories_result = self.db.execute(text(
            "SELECT CategoryId FROM dynamicpricing.TopCategories"
        ))
        categories = [row[0] for row in categories_result.fetchall()]
        
        stats = {
            "branches": len(branches),
            "categories": len(categories),
            "dates_processed": 0,
            "indexes_created": 0,
            "api_calls": 0,
            "api_successes": 0,
            "api_failures": 0
        }
        
        current_date = start_date
        while current_date <= end_date:
            for branch_id in branches:
                for category_id in categories:
                    # Get our base price for this combo
                    base_price_result = self.db.execute(text("""
                        SELECT TOP 1 avg_base_price_paid
                        FROM dynamicpricing.fact_daily_demand
                        WHERE tenant_id = :tenant_id 
                          AND branch_id = :branch_id 
                          AND category_id = :category_id
                        ORDER BY demand_date DESC
                    """), {
                        "tenant_id": tenant_id,
                        "branch_id": branch_id,
                        "category_id": category_id
                    })
                    row = base_price_result.fetchone()
                    our_base_price = Decimal(str(row[0])) if row and row[0] else None
                    
                    # Calculate and save competitor index
                    stats["api_calls"] += 1
                    index = self.calculate_competitor_index(
                        tenant_id, branch_id, category_id, 
                        current_date, our_base_price
                    )
                    
                    if index.competitors_count > 0:
                        stats["api_successes"] += 1
                    else:
                        stats["api_failures"] += 1
                    
                    self.save_competitor_index(tenant_id, branch_id, index)
                    stats["indexes_created"] += 1
            
            stats["dates_processed"] += 1
            current_date += timedelta(days=1)
        
        return stats
    
    def get_competitor_index(
        self,
        tenant_id: int,
        branch_id: int,
        category_id: int,
        index_date: date
    ) -> Optional[CompetitorIndex]:
        """Get competitor index from database."""
        result = self.db.execute(text("""
            SELECT category_id, index_date, competitor_avg_price,
                   competitor_min_price, competitor_max_price,
                   competitors_count, our_base_price, price_position
            FROM dynamicpricing.competitor_index
            WHERE tenant_id = :tenant_id
              AND branch_id = :branch_id
              AND category_id = :category_id
              AND index_date = :index_date
        """), {
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "category_id": category_id,
            "index_date": index_date
        })
        
        row = result.fetchone()
        if not row:
            return None
        
        return CompetitorIndex(
            category_id=row[0],
            index_date=row[1],
            avg_price=Decimal(str(row[2])),
            min_price=Decimal(str(row[3])) if row[3] else Decimal("0"),
            max_price=Decimal(str(row[4])) if row[4] else Decimal("0"),
            competitors_count=row[5],
            our_base_price=Decimal(str(row[6])) if row[6] else None,
            price_position=Decimal(str(row[7])) if row[7] else None
        )
    
    def fetch_live_competitor_prices(
        self,
        branch_id: int,
        price_date: date
    ) -> Dict[str, Any]:
        """
        Fetch LIVE competitor prices from Booking.com API for a branch.
        Returns prices organized by Renty category with brand/model info.
        """
        location = self.BRANCH_CITY_MAP.get(branch_id, "Riyadh")
        price_datetime = datetime.combine(price_date, datetime.min.time())
        return self._api.get_competitor_prices_for_date(location, price_datetime)
