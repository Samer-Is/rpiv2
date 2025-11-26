"""
STEP 2: Pricing Rules - Dynamic Pricing Multipliers

This module implements rule-based pricing multipliers based on:
1. Demand prediction (from ML model)
2. Supply/Utilization (from fleet data)
3. External factors (holidays, events, weekends)
4. Business constraints (min/max prices)

Pricing Formula:
BasePrice × DemandMultiplier × SupplyMultiplier × EventMultiplier = FinalPrice
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PricingRules:
    """
    Dynamic pricing rules engine.
    
    Applies multipliers based on demand, supply, and external factors.
    """
    
    def __init__(self, 
                 min_multiplier: float = 0.80,
                 max_multiplier: float = 2.50,
                 base_multiplier: float = 1.00):
        """
        Initialize pricing rules.
        
        Args:
            min_multiplier: Minimum allowed multiplier (e.g., 0.80 = 20% discount max)
            max_multiplier: Maximum allowed multiplier (e.g., 2.50 = 150% premium max)
            base_multiplier: Default multiplier when no adjustments
        """
        self.min_multiplier = min_multiplier
        self.max_multiplier = max_multiplier
        self.base_multiplier = base_multiplier
        
        logger.info(f"PricingRules initialized: min={min_multiplier}, max={max_multiplier}")
    
    def calculate_demand_multiplier(self, predicted_demand: float, 
                                   average_demand: float) -> float:
        """
        Calculate multiplier based on predicted demand vs average.
        
        Logic:
        - High demand (>150% of average) → increase price (+20% max)
        - Normal demand (75-150%) → neutral (0-10% adjustment)
        - Low demand (<75%) → decrease price (-15% max)
        
        Args:
            predicted_demand: Predicted bookings from ML model
            average_demand: Historical average bookings for this branch/date
            
        Returns:
            Demand multiplier (0.85 to 1.20)
        """
        if average_demand == 0:
            return self.base_multiplier
        
        demand_ratio = predicted_demand / average_demand
        
        if demand_ratio >= 1.5:  # Very high demand
            multiplier = 1.20
        elif demand_ratio >= 1.3:  # High demand
            multiplier = 1.15
        elif demand_ratio >= 1.1:  # Above average
            multiplier = 1.10
        elif demand_ratio >= 0.9:  # Normal
            multiplier = 1.00
        elif demand_ratio >= 0.75:  # Below average
            multiplier = 0.95
        else:  # Low demand
            multiplier = 0.85
        
        return multiplier
    
    def calculate_supply_multiplier(self, available_vehicles: int,
                                   total_vehicles: int) -> float:
        """
        Calculate multiplier based on fleet availability (utilization).
        
        Logic:
        - Low availability (<30% free) → increase price (+15% max)
        - Medium availability (30-60%) → slight increase (0-10%)
        - High availability (>60%) → decrease price (-10% max)
        
        Args:
            available_vehicles: Number of vehicles available
            total_vehicles: Total fleet size
            
        Returns:
            Supply multiplier (0.90 to 1.15)
        """
        if total_vehicles == 0:
            return self.base_multiplier
        
        availability_pct = (available_vehicles / total_vehicles) * 100
        
        if availability_pct < 20:  # Very low availability
            multiplier = 1.15
        elif availability_pct < 30:  # Low availability
            multiplier = 1.10
        elif availability_pct < 50:  # Medium-low
            multiplier = 1.05
        elif availability_pct < 70:  # Medium-high
            multiplier = 1.00
        else:  # High availability
            multiplier = 0.90
        
        return multiplier
    
    def calculate_event_multiplier(self, 
                                  is_holiday: bool = False,
                                  is_school_vacation: bool = False,
                                  is_ramadan: bool = False,
                                  is_umrah_season: bool = False,
                                  is_hajj: bool = False,
                                  is_festival: bool = False,
                                  is_sports_event: bool = False,
                                  is_conference: bool = False,
                                  is_weekend: bool = False,
                                  city_name: str = None,
                                  is_airport: bool = False,
                                  days_to_holiday: int = -1) -> float:
        """
        Calculate multiplier based on external events.
        
        Logic:
        - Major holiday → +15%
        - Hajj (in Mecca) → +30-45%
        - Ramadan (peak Umrah) → +12%
        - Umrah season → +10%
        - Festival (Riyadh/Jeddah Season) → +15-20%
        - Sports (F1) → +15-25%
        - Conference/Business → +8-12%
        - School vacation → +8%
        - Weekend → +5%
        - Airport → +10%
        - City-specific premiums apply
        - Multiple factors stack (but capped by max_multiplier)
        
        Args:
            is_holiday: True if holiday
            is_school_vacation: True if school vacation period
            is_ramadan: True if Ramadan period (holy month)
            is_umrah_season: True if peak Umrah season
            is_hajj: True if Hajj period (major pilgrimage)
            is_festival: True if festival (Riyadh/Jeddah Season)
            is_sports_event: True if sports event (F1, Saudi Cup)
            is_conference: True if business/conference event
            is_weekend: True if weekend (Friday/Saturday in KSA)
            city_name: City name for city-specific logic
            is_airport: True if airport location
            days_to_holiday: Days until next holiday (0-2 = pre-holiday surge)
            
        Returns:
            Event multiplier (1.00 to 1.60 for extreme cases)
        """
        multiplier = 1.00
        
        # HAJJ PREMIUM (highest priority, city-specific)
        if is_hajj and city_name and city_name.lower() in ['mecca', 'makkah']:
            multiplier *= 1.45  # 45% premium in Mecca during Hajj
        elif is_hajj:
            multiplier *= 1.20  # 20% premium elsewhere during Hajj season
        
        # FESTIVAL PREMIUM (city-specific)
        elif is_festival:
            if city_name and city_name.lower() in ['riyadh', 'jeddah']:
                multiplier *= 1.20  # 20% premium in host cities
            else:
                multiplier *= 1.10  # 10% premium elsewhere
        
        # SPORTS EVENT PREMIUM (city-specific)
        elif is_sports_event:
            if city_name and city_name.lower() in ['jeddah', 'riyadh']:
                multiplier *= 1.25  # 25% premium in host cities (F1 in Jeddah)
            else:
                multiplier *= 1.12  # 12% premium elsewhere
        
        # CONFERENCE/BUSINESS PREMIUM (city-specific)
        elif is_conference:
            if city_name and city_name.lower() in ['riyadh', 'jeddah']:
                multiplier *= 1.12  # 12% premium in major business cities
            else:
                multiplier *= 1.08  # 8% premium elsewhere
        
        # HOLIDAY PREMIUM
        elif is_holiday:
            multiplier *= 1.15  # 15% premium
        
        # PRE-HOLIDAY SURGE (varies by event type)
        elif 0 <= days_to_holiday <= 2:
            if is_hajj:
                multiplier *= 1.20  # Higher surge before Hajj
            elif is_festival or is_sports_event:
                multiplier *= 1.15  # Higher surge before major events
            else:
                multiplier *= 1.12  # Standard pre-holiday surge
        
        # RAMADAN PREMIUM (peak religious tourism)
        if is_ramadan:
            if city_name and city_name.lower() in ['mecca', 'makkah', 'medina', 'madinah']:
                multiplier *= 1.15  # 15% in holy cities during Ramadan
            else:
                multiplier *= 1.08  # 8% elsewhere
        
        # UMRAH SEASON PREMIUM (beyond Ramadan)
        if is_umrah_season and not is_ramadan and not is_hajj:
            if city_name and city_name.lower() in ['mecca', 'makkah', 'medina', 'madinah']:
                multiplier *= 1.12  # 12% in holy cities
            else:
                multiplier *= 1.05  # 5% elsewhere
        
        # SCHOOL VACATION PREMIUM
        if is_school_vacation:
            multiplier *= 1.08  # 8% premium
        
        # WEEKEND PREMIUM
        if is_weekend:
            multiplier *= 1.05  # 5% premium
        
        # AIRPORT PREMIUM
        if is_airport:
            multiplier *= 1.10  # 10% airport premium
        
        # Cap the multiplier (higher cap for extreme cases like Hajj in Mecca)
        multiplier = min(multiplier, 1.60)  # Max 60% for extreme combinations
        
        return multiplier
    
    def calculate_final_price(self,
                            base_price: float,
                            predicted_demand: float,
                            average_demand: float,
                            available_vehicles: int,
                            total_vehicles: int,
                            is_holiday: bool = False,
                            is_school_vacation: bool = False,
                            is_ramadan: bool = False,
                            is_umrah_season: bool = False,
                            is_hajj: bool = False,
                            is_festival: bool = False,
                            is_sports_event: bool = False,
                            is_conference: bool = False,
                            is_weekend: bool = False,
                            city_name: str = None,
                            is_airport: bool = False,
                            days_to_holiday: int = -1) -> Dict:
        """
        Calculate final dynamic price with all multipliers.
        
        Args:
            base_price: Base daily rate
            predicted_demand: ML model prediction
            average_demand: Historical average
            available_vehicles: Vehicles available
            total_vehicles: Total fleet size
            is_holiday, is_school_vacation, is_major_event, is_weekend: Event flags
            days_to_holiday: Days until holiday
            
        Returns:
            Dict with final_price, multipliers breakdown, and explanation
        """
        # Calculate individual multipliers
        demand_mult = self.calculate_demand_multiplier(predicted_demand, average_demand)
        supply_mult = self.calculate_supply_multiplier(available_vehicles, total_vehicles)
        event_mult = self.calculate_event_multiplier(
            is_holiday, is_school_vacation, is_ramadan, is_umrah_season, 
            is_hajj, is_festival, is_sports_event, is_conference,
            is_weekend, city_name, is_airport, days_to_holiday
        )
        
        # Combined multiplier
        combined_mult = demand_mult * supply_mult * event_mult
        
        # Apply min/max constraints
        final_mult = np.clip(combined_mult, self.min_multiplier, self.max_multiplier)
        
        # Calculate final price
        final_price = base_price * final_mult
        
        # Generate explanation
        explanation = self._generate_explanation(
            demand_mult, supply_mult, event_mult, final_mult,
            predicted_demand, average_demand,
            available_vehicles, total_vehicles,
            is_holiday, is_school_vacation, is_ramadan, is_umrah_season, 
            is_hajj, is_festival, is_sports_event, is_conference, is_weekend,
            city_name, is_airport
        )
        
        return {
            'base_price': base_price,
            'final_price': round(final_price, 2),
            'demand_multiplier': round(demand_mult, 2),
            'supply_multiplier': round(supply_mult, 2),
            'event_multiplier': round(event_mult, 2),
            'combined_multiplier': round(combined_mult, 2),
            'final_multiplier': round(final_mult, 2),
            'price_change_pct': round((final_mult - 1.00) * 100, 1),
            'explanation': explanation
        }
    
    def _generate_explanation(self, demand_mult, supply_mult, event_mult, final_mult,
                            predicted_demand, average_demand,
                            available_vehicles, total_vehicles,
                            is_holiday, is_school_vacation, is_ramadan, is_umrah_season, 
                            is_hajj, is_festival, is_sports_event, is_conference, is_weekend,
                            city_name, is_airport) -> str:
        """Generate human-readable pricing explanation."""
        reasons = []
        
        # Demand explanation
        if predicted_demand > average_demand * 1.3:
            reasons.append(f"High demand expected ({predicted_demand:.0f} vs avg {average_demand:.0f})")
        elif predicted_demand < average_demand * 0.75:
            reasons.append(f"Low demand expected ({predicted_demand:.0f} vs avg {average_demand:.0f})")
        
        # Supply explanation
        if total_vehicles > 0:
            avail_pct = (available_vehicles / total_vehicles) * 100
            if avail_pct < 30:
                reasons.append(f"Low vehicle availability ({avail_pct:.0f}% free)")
            elif avail_pct > 70:
                reasons.append(f"High vehicle availability ({avail_pct:.0f}% free)")
        
        # Event explanations (prioritized)
        if is_hajj:
            if city_name and city_name.lower() in ['mecca', 'makkah']:
                reasons.append("Hajj season in Mecca (PEAK)")
            else:
                reasons.append("Hajj season")
        if is_festival:
            if city_name and city_name.lower() in ['riyadh', 'jeddah']:
                reasons.append(f"Festival in {city_name}")
            else:
                reasons.append("Festival period")
        if is_sports_event:
            if city_name and city_name.lower() in ['jeddah', 'riyadh']:
                reasons.append(f"Sports event in {city_name}")
            else:
                reasons.append("Sports event")
        if is_conference:
            reasons.append("Business/Conference event")
        if is_holiday:
            reasons.append("Holiday period")
        if is_ramadan:
            if city_name and city_name.lower() in ['mecca', 'makkah', 'medina', 'madinah']:
                reasons.append(f"Ramadan in {city_name}")
            else:
                reasons.append("Ramadan")
        if is_school_vacation:
            reasons.append("School vacation")
        if is_umrah_season:
            reasons.append("Umrah season")
        if is_weekend:
            reasons.append("Weekend")
        if is_airport:
            reasons.append("Airport location")
        
        # Final verdict
        if final_mult > 1.30:
            verdict = "PEAK pricing applied"
        elif final_mult > 1.10:
            verdict = "Premium pricing applied"
        elif final_mult < 0.95:
            verdict = "Discount pricing applied"
        else:
            verdict = "Standard pricing"
        
        if reasons:
            return f"{verdict}: {', '.join(reasons)}"
        else:
            return verdict


def demonstrate_pricing_rules():
    """Demonstrate pricing rules with examples."""
    logger.info("="*80)
    logger.info("PRICING RULES DEMONSTRATION")
    logger.info("="*80)
    
    pricing = PricingRules(min_multiplier=0.80, max_multiplier=2.50)
    base_price = 200.0  # SAR per day
    
    # Scenario 1: Normal day, normal demand
    logger.info("\n📊 Scenario 1: Normal Day")
    result = pricing.calculate_final_price(
        base_price=base_price,
        predicted_demand=100,
        average_demand=100,
        available_vehicles=50,
        total_vehicles=100,
        is_holiday=False,
        is_weekend=False
    )
    logger.info(f"  Base Price: {result['base_price']} SAR")
    logger.info(f"  Final Price: {result['final_price']} SAR ({result['price_change_pct']:+.1f}%)")
    logger.info(f"  Multipliers: Demand={result['demand_multiplier']}, Supply={result['supply_multiplier']}, Event={result['event_multiplier']}")
    logger.info(f"  Reason: {result['explanation']}")
    
    # Scenario 2: Holiday with high demand
    logger.info("\n📊 Scenario 2: Holiday - High Demand")
    result = pricing.calculate_final_price(
        base_price=base_price,
        predicted_demand=150,
        average_demand=100,
        available_vehicles=20,
        total_vehicles=100,
        is_holiday=True,
        is_weekend=False
    )
    logger.info(f"  Base Price: {result['base_price']} SAR")
    logger.info(f"  Final Price: {result['final_price']} SAR ({result['price_change_pct']:+.1f}%)")
    logger.info(f"  Multipliers: Demand={result['demand_multiplier']}, Supply={result['supply_multiplier']}, Event={result['event_multiplier']}")
    logger.info(f"  Reason: {result['explanation']}")
    
    # Scenario 3: Low demand, high availability
    logger.info("\n📊 Scenario 3: Low Demand Day")
    result = pricing.calculate_final_price(
        base_price=base_price,
        predicted_demand=60,
        average_demand=100,
        available_vehicles=80,
        total_vehicles=100,
        is_holiday=False,
        is_weekend=False
    )
    logger.info(f"  Base Price: {result['base_price']} SAR")
    logger.info(f"  Final Price: {result['final_price']} SAR ({result['price_change_pct']:+.1f}%)")
    logger.info(f"  Multipliers: Demand={result['demand_multiplier']}, Supply={result['supply_multiplier']}, Event={result['event_multiplier']}")
    logger.info(f"  Reason: {result['explanation']}")
    
    # Scenario 4: Weekend + School Vacation
    logger.info("\n📊 Scenario 4: Weekend + School Vacation")
    result = pricing.calculate_final_price(
        base_price=base_price,
        predicted_demand=120,
        average_demand=100,
        available_vehicles=40,
        total_vehicles=100,
        is_holiday=False,
        is_school_vacation=True,
        is_weekend=True
    )
    logger.info(f"  Base Price: {result['base_price']} SAR")
    logger.info(f"  Final Price: {result['final_price']} SAR ({result['price_change_pct']:+.1f}%)")
    logger.info(f"  Multipliers: Demand={result['demand_multiplier']}, Supply={result['supply_multiplier']}, Event={result['event_multiplier']}")
    logger.info(f"  Reason: {result['explanation']}")
    
    logger.info("\n" + "="*80)
    logger.info("PRICING RULES DEMONSTRATION COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    demonstrate_pricing_rules()

