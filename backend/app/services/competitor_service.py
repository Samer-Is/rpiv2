"""
Competitor Pricing Service - CHUNK 8
Integration with Booking.com API and competitor index calculation
"""
import logging
import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session

from .booking_com_api import get_booking_api, BookingComCarRentalAPI

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
    
    Supports:
    - Fetching competitor prices (mock/real API)
    - Category mapping configuration
    - Competitor index calculation (avg of top 3)
    - Caching with TTL
    """
    
    # Cache TTL in hours
    CACHE_TTL_HOURS = 24
    
    # Mock competitor data for Saudi Arabia car rental market
    MOCK_COMPETITORS = {
        "Riyadh": {
            "economy": [
                {"name": "Budget", "daily": 150, "weekly": 900, "monthly": 3200},
                {"name": "Hertz", "daily": 165, "weekly": 990, "monthly": 3500},
                {"name": "Avis", "daily": 175, "weekly": 1050, "monthly": 3700},
                {"name": "Europcar", "daily": 160, "weekly": 960, "monthly": 3400},
                {"name": "Sixt", "daily": 155, "weekly": 930, "monthly": 3300},
            ],
            "compact": [
                {"name": "Budget", "daily": 180, "weekly": 1080, "monthly": 3800},
                {"name": "Hertz", "daily": 195, "weekly": 1170, "monthly": 4100},
                {"name": "Avis", "daily": 200, "weekly": 1200, "monthly": 4200},
                {"name": "Europcar", "daily": 185, "weekly": 1110, "monthly": 3900},
                {"name": "Sixt", "daily": 190, "weekly": 1140, "monthly": 4000},
            ],
            "standard": [
                {"name": "Budget", "daily": 220, "weekly": 1320, "monthly": 4600},
                {"name": "Hertz", "daily": 240, "weekly": 1440, "monthly": 5000},
                {"name": "Avis", "daily": 250, "weekly": 1500, "monthly": 5200},
                {"name": "Europcar", "daily": 230, "weekly": 1380, "monthly": 4800},
                {"name": "Sixt", "daily": 235, "weekly": 1410, "monthly": 4900},
            ],
            "fullsize": [
                {"name": "Budget", "daily": 280, "weekly": 1680, "monthly": 5800},
                {"name": "Hertz", "daily": 300, "weekly": 1800, "monthly": 6200},
                {"name": "Avis", "daily": 320, "weekly": 1920, "monthly": 6600},
                {"name": "Europcar", "daily": 290, "weekly": 1740, "monthly": 6000},
                {"name": "Sixt", "daily": 295, "weekly": 1770, "monthly": 6100},
            ],
            "suv": [
                {"name": "Budget", "daily": 350, "weekly": 2100, "monthly": 7200},
                {"name": "Hertz", "daily": 380, "weekly": 2280, "monthly": 7800},
                {"name": "Avis", "daily": 400, "weekly": 2400, "monthly": 8200},
                {"name": "Europcar", "daily": 360, "weekly": 2160, "monthly": 7400},
                {"name": "Sixt", "daily": 370, "weekly": 2220, "monthly": 7600},
            ],
            "luxury": [
                {"name": "Budget", "daily": 550, "weekly": 3300, "monthly": 11000},
                {"name": "Hertz", "daily": 600, "weekly": 3600, "monthly": 12000},
                {"name": "Avis", "daily": 650, "weekly": 3900, "monthly": 13000},
                {"name": "Europcar", "daily": 580, "weekly": 3480, "monthly": 11600},
                {"name": "Sixt", "daily": 590, "weekly": 3540, "monthly": 11800},
            ],
        },
        "Jeddah": {
            # Similar structure with slightly different prices
            "economy": [
                {"name": "Budget", "daily": 145, "weekly": 870, "monthly": 3100},
                {"name": "Hertz", "daily": 160, "weekly": 960, "monthly": 3400},
                {"name": "Avis", "daily": 170, "weekly": 1020, "monthly": 3600},
                {"name": "Europcar", "daily": 155, "weekly": 930, "monthly": 3300},
            ],
            "compact": [
                {"name": "Budget", "daily": 175, "weekly": 1050, "monthly": 3700},
                {"name": "Hertz", "daily": 190, "weekly": 1140, "monthly": 4000},
                {"name": "Avis", "daily": 195, "weekly": 1170, "monthly": 4100},
                {"name": "Europcar", "daily": 180, "weekly": 1080, "monthly": 3800},
            ],
            "standard": [
                {"name": "Budget", "daily": 215, "weekly": 1290, "monthly": 4500},
                {"name": "Hertz", "daily": 235, "weekly": 1410, "monthly": 4900},
                {"name": "Avis", "daily": 245, "weekly": 1470, "monthly": 5100},
                {"name": "Europcar", "daily": 225, "weekly": 1350, "monthly": 4700},
            ],
            "fullsize": [
                {"name": "Budget", "daily": 275, "weekly": 1650, "monthly": 5700},
                {"name": "Hertz", "daily": 295, "weekly": 1770, "monthly": 6100},
                {"name": "Avis", "daily": 315, "weekly": 1890, "monthly": 6500},
                {"name": "Europcar", "daily": 285, "weekly": 1710, "monthly": 5900},
            ],
            "suv": [
                {"name": "Budget", "daily": 345, "weekly": 2070, "monthly": 7100},
                {"name": "Hertz", "daily": 375, "weekly": 2250, "monthly": 7700},
                {"name": "Avis", "daily": 395, "weekly": 2370, "monthly": 8100},
                {"name": "Europcar", "daily": 355, "weekly": 2130, "monthly": 7300},
            ],
            "luxury": [
                {"name": "Budget", "daily": 540, "weekly": 3240, "monthly": 10800},
                {"name": "Hertz", "daily": 590, "weekly": 3540, "monthly": 11800},
                {"name": "Avis", "daily": 640, "weekly": 3840, "monthly": 12800},
                {"name": "Europcar", "daily": 570, "weekly": 3420, "monthly": 11400},
            ],
        },
        "Dammam": {
            # Similar structure
            "economy": [
                {"name": "Budget", "daily": 140, "weekly": 840, "monthly": 3000},
                {"name": "Hertz", "daily": 155, "weekly": 930, "monthly": 3300},
                {"name": "Avis", "daily": 165, "weekly": 990, "monthly": 3500},
            ],
            "compact": [
                {"name": "Budget", "daily": 170, "weekly": 1020, "monthly": 3600},
                {"name": "Hertz", "daily": 185, "weekly": 1110, "monthly": 3900},
                {"name": "Avis", "daily": 190, "weekly": 1140, "monthly": 4000},
            ],
            "standard": [
                {"name": "Budget", "daily": 210, "weekly": 1260, "monthly": 4400},
                {"name": "Hertz", "daily": 230, "weekly": 1380, "monthly": 4800},
                {"name": "Avis", "daily": 240, "weekly": 1440, "monthly": 5000},
            ],
            "fullsize": [
                {"name": "Budget", "daily": 270, "weekly": 1620, "monthly": 5600},
                {"name": "Hertz", "daily": 290, "weekly": 1740, "monthly": 6000},
                {"name": "Avis", "daily": 310, "weekly": 1860, "monthly": 6400},
            ],
            "suv": [
                {"name": "Budget", "daily": 340, "weekly": 2040, "monthly": 7000},
                {"name": "Hertz", "daily": 370, "weekly": 2220, "monthly": 7600},
                {"name": "Avis", "daily": 390, "weekly": 2340, "monthly": 8000},
            ],
            "luxury": [
                {"name": "Budget", "daily": 530, "weekly": 3180, "monthly": 10600},
                {"name": "Hertz", "daily": 580, "weekly": 3480, "monthly": 11600},
                {"name": "Avis", "daily": 630, "weekly": 3780, "monthly": 12600},
            ],
        },
    }
    
    # City mapping for branches
    BRANCH_CITY_MAP = {
        # Airport branches
        122: "Riyadh",   # Riyadh Airport
        15: "Jeddah",    # Jeddah Airport
        26: "Dammam",    # Dammam Airport
        # Non-airport branches
        2: "Riyadh",     # Riyadh City
        34: "Jeddah",    # Jeddah City
        211: "Riyadh",   # Riyadh Branch
    }
    
    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, Any] = {}
    
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
        use_cache: bool = True,
        use_live_api: bool = True
    ) -> List[CompetitorPrice]:
        """
        Fetch competitor prices for a city and vehicle type.
        
        Tries Booking.com API first, falls back to mock data if API fails.
        """
        cache_key = f"{city}_{vehicle_type}_{price_date}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached["expires_at"] > datetime.now():
                logger.info(f"Using cached prices for {cache_key}")
                return cached["data"]
        
        prices = []
        
        # Try live Booking.com API first
        if use_live_api:
            try:
                prices = self._fetch_from_booking_api(city, vehicle_type, price_date)
                if prices:
                    logger.info(f"Fetched {len(prices)} prices from Booking.com API for {city}/{vehicle_type}")
            except Exception as e:
                logger.warning(f"Booking.com API failed: {e}, falling back to mock data")
        
        # Fall back to mock data if API returned nothing
        if not prices:
            prices = self._fetch_mock_prices(city, vehicle_type, price_date)
            logger.info(f"Using mock prices for {city}/{vehicle_type}")
        
        # Cache results
        self._cache[cache_key] = {
            "data": prices,
            "expires_at": datetime.now() + timedelta(hours=self.CACHE_TTL_HOURS)
        }
        
        return prices
    
    def _fetch_from_booking_api(
        self,
        city: str,
        vehicle_type: str,
        price_date: date
    ) -> List[CompetitorPrice]:
        """Fetch prices from Booking.com API."""
        api = get_booking_api()
        
        # Convert date to datetime
        price_datetime = datetime.combine(price_date, datetime.min.time())
        
        # Get prices for this city
        category_prices = api.get_competitor_prices_for_date(city, price_datetime)
        
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
                weekly_price=Decimal(str(comp["price"] * 6)),  # Estimate weekly
                monthly_price=Decimal(str(comp["price"] * 25)),  # Estimate monthly
            ))
        
        return prices
    
    def _fetch_mock_prices(
        self, 
        city: str, 
        vehicle_type: str,
        price_date: date
    ) -> List[CompetitorPrice]:
        """Fetch mock competitor prices with seasonal adjustments."""
        city_data = self.MOCK_COMPETITORS.get(city, self.MOCK_COMPETITORS["Riyadh"])
        vehicle_data = city_data.get(vehicle_type, city_data.get("economy", []))
        
        # Apply seasonal adjustment based on date
        seasonal_factor = self._get_seasonal_factor(price_date)
        
        prices = []
        for comp in vehicle_data:
            prices.append(CompetitorPrice(
                competitor_name=comp["name"],
                vehicle_type=vehicle_type,
                daily_price=Decimal(str(round(comp["daily"] * seasonal_factor, 2))),
                weekly_price=Decimal(str(round(comp["weekly"] * seasonal_factor, 2))),
                monthly_price=Decimal(str(round(comp["monthly"] * seasonal_factor, 2))),
            ))
        
        return prices
    
    def _get_seasonal_factor(self, price_date: date) -> float:
        """Get seasonal price adjustment factor."""
        month = price_date.month
        
        # High season: summer (June-Aug), Ramadan/Eid periods, winter holidays
        if month in (6, 7, 8):  # Summer
            return 1.15
        elif month in (12, 1):  # Winter holidays
            return 1.10
        elif month in (3, 4):  # Spring (often Ramadan/Eid)
            return 1.20
        else:
            return 1.0
    
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
        
        # Fetch competitor prices
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
        
        Returns statistics about the build.
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
            "prices_cached": 0
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
                    index = self.calculate_competitor_index(
                        tenant_id, branch_id, category_id, 
                        current_date, our_base_price
                    )
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
        Fetch live competitor prices from Booking.com API for a branch.
        
        Returns prices organized by Renty category.
        """
        api = get_booking_api()
        
        # Get location for branch
        location = api.get_location_for_branch_id(branch_id)
        
        # Fetch from API
        price_datetime = datetime.combine(price_date, datetime.min.time())
        return api.get_competitor_prices_for_date(location, price_datetime)
