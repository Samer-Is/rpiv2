"""
STEP 2: Integrated Pricing Engine

Combines:
1. ML demand prediction model (from STEP 1)
2. Pricing rules (multipliers)
3. Real-time data inputs
→ Outputs optimized price for 1-2 days ahead
"""

import logging
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from pricing_rules import PricingRules
import config

logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger(__name__)


class DynamicPricingEngine:
    """
    Complete dynamic pricing engine.
    
    Workflow:
    1. Load ML model and features
    2. Prepare input features for target date
    3. Predict demand using ML model
    4. Apply pricing rules (multipliers)
    5. Return optimized price + explanation
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize pricing engine.
        
        Args:
            model_path: Path to trained model (defaults to ROBUST_v4)
        """
        if model_path is None:
            model_path = config.MODELS_DIR / 'demand_prediction_ROBUST_v4.pkl'
        
        logger.info("Initializing Dynamic Pricing Engine...")
        
        # Load ML model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        logger.info(f"  ✓ ML model loaded from {model_path}")
        
        # Load feature columns
        features_path = config.MODELS_DIR / 'feature_columns_ROBUST_v4.pkl'
        with open(features_path, 'rb') as f:
            self.feature_columns = pickle.load(f)
        logger.info(f"  ✓ Feature columns loaded ({len(self.feature_columns)} features)")
        
        # Initialize pricing rules
        self.pricing_rules = PricingRules(
            min_multiplier=0.80,  # Max 20% discount
            max_multiplier=2.50   # Max 150% premium
        )
        logger.info(f"  ✓ Pricing rules initialized")
        
        # Load historical data for context
        self._load_historical_context()
        
        logger.info("✓ Dynamic Pricing Engine ready")
    
    def _load_historical_context(self):
        """Load historical averages for comparison."""
        try:
            # Load training data to get branch averages
            df = pd.read_parquet(config.PROCESSED_DATA_DIR / 'training_data_enriched.parquet')
            
            # Calculate branch-level statistics
            self.branch_avg_demand = df.groupby('PickupBranchId').size() / df['Start'].dt.date.nunique()
            self.branch_avg_price = df.groupby('PickupBranchId')['DailyRateAmount'].mean()
            
            logger.info(f"  ✓ Historical context loaded ({len(self.branch_avg_demand)} branches)")
        except Exception as e:
            logger.warning(f"  ⚠ Could not load historical context: {e}")
            self.branch_avg_demand = pd.Series()
            self.branch_avg_price = pd.Series()
    
    def prepare_features(self, 
                        target_date: datetime,
                        branch_id: int,
                        city_id: int = 1,
                        country_id: int = 1,
                        is_airport: bool = False,
                        is_holiday: bool = False,
                        is_school_vacation: bool = False,
                        is_ramadan: bool = False,
                        is_umrah_season: bool = False,
                        is_major_event: bool = False,
                        days_to_holiday: int = -1,
                        days_from_holiday: int = -1,
                        holiday_duration: int = 0) -> pd.DataFrame:
        """
        Prepare features for ML model prediction.
        
        Args:
            target_date: Date to predict for (1-2 days ahead)
            branch_id: Branch ID
            city_id: City ID
            country_id: Country ID
            is_airport: Airport location flag
            is_holiday, is_school_vacation, is_major_event: External event flags
            days_to_holiday, days_from_holiday, holiday_duration: Holiday features
            
        Returns:
            DataFrame with features ready for prediction
        """
        # Create base features dictionary
        features = {}
        
        # Temporal features
        features['DayOfWeek'] = target_date.weekday()
        features['DayOfMonth'] = target_date.day
        features['WeekOfYear'] = target_date.isocalendar()[1]
        features['Month'] = target_date.month
        features['Quarter'] = (target_date.month - 1) // 3 + 1
        features['IsWeekend'] = 1 if target_date.weekday() in [5, 6] else 0
        features['DayOfYear'] = target_date.timetuple().tm_yday
        
        # Fourier features for seasonality
        t = (target_date - datetime(2023, 1, 1)).days
        for period, order in [(365, 2), (7, 2)]:
            for i in range(1, order + 1):
                features[f'sin_{period}_{i}'] = np.sin(2 * np.pi * i * t / period)
                features[f'cos_{period}_{i}'] = np.cos(2 * np.pi * i * t / period)
        
        # External features
        features['is_holiday'] = 1 if is_holiday else 0
        features['holiday_duration'] = holiday_duration
        features['is_school_vacation'] = 1 if is_school_vacation else 0
        features['is_ramadan'] = 1 if is_ramadan else 0
        features['is_umrah_season'] = 1 if is_umrah_season else 0
        features['is_major_event'] = 1 if is_major_event else 0
        features['days_to_holiday'] = days_to_holiday
        features['days_from_holiday'] = days_from_holiday
        features['is_long_holiday'] = 1 if holiday_duration >= 4 else 0
        features['near_holiday'] = 1 if 0 <= days_to_holiday <= 2 else 0
        features['post_holiday'] = 1 if 0 <= days_from_holiday <= 2 else 0
        features['is_weekend'] = features['IsWeekend']
        
        # Location features
        features['PickupBranchId'] = branch_id
        features['DropoffBranchId'] = branch_id  # Assume same for simplicity
        features['CityId'] = city_id
        features['CountryId'] = country_id
        features['IsAirport'] = 1 if is_airport else 0
        features['IsAirportBranch'] = 1 if is_airport else 0
        
        # Historical features (from loaded context)
        features['BranchHistoricalSize'] = self.branch_avg_demand.get(branch_id, 100)
        features['CitySize'] = 10000  # Placeholder
        features['BranchAvgPrice'] = self.branch_avg_price.get(branch_id, 200)
        features['CityAvgPrice'] = 200  # Placeholder
        
        # Other features (defaults)
        features['DailyRateAmount'] = features['BranchAvgPrice']
        features['RentalRateId'] = -1
        features['FleetSize'] = 0
        features['CapacityIndicator'] = 1.0
        features['VehicleId'] = -1
        features['StatusId'] = 0
        features['FinancialStatusId'] = 0
        features['CurrencyId'] = 1
        features['BookingId'] = -1
        features['ModelId'] = -1
        features['Year'] = 2024
        features['ContractDurationDays'] = 3
        
        # Ensure all required features present
        df = pd.DataFrame([features])
        
        # Add missing features with defaults
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Select only model features in correct order
        df = df[self.feature_columns]
        
        return df
    
    def predict_demand(self, features: pd.DataFrame) -> float:
        """
        Predict demand using ML model.
        
        Args:
            features: Prepared feature dataframe
            
        Returns:
            Predicted daily bookings
        """
        prediction = self.model.predict(features)[0]
        return max(1, prediction)  # Ensure positive
    
    def calculate_optimized_price(self,
                                 target_date: datetime,
                                 branch_id: int,
                                 base_price: float,
                                 available_vehicles: int,
                                 total_vehicles: int,
                                 city_id: int = 1,
                                 city_name: str = None,
                                 is_airport: bool = False,
                                 is_holiday: bool = False,
                                 is_school_vacation: bool = False,
                                 is_ramadan: bool = False,
                                 is_umrah_season: bool = False,
                                 is_hajj: bool = False,
                                 is_festival: bool = False,
                                 is_sports_event: bool = False,
                                 is_conference: bool = False,
                                 days_to_holiday: int = -1) -> Dict:
        """
        Complete pricing workflow: predict demand → apply rules → return price.
        
        Args:
            target_date: Date to price for (1-2 days ahead)
            branch_id: Branch ID
            base_price: Current/base price
            available_vehicles: Vehicles available
            total_vehicles: Total fleet size
            city_id, city_name, is_airport: Location info
            is_holiday, is_school_vacation, is_ramadan, is_umrah_season: General events
            is_hajj, is_festival, is_sports_event, is_conference: Specific events
            days_to_holiday: Days until holiday
            
        Returns:
            Dict with final price, demand prediction, multipliers, explanation
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"PRICING CALCULATION FOR {target_date.date()}")
        logger.info(f"{'='*80}")
        
        # Step 1: Prepare features
        logger.info("\n1. Preparing features...")
        # Combine separated events for model features (model still uses is_major_event)
        is_major_event = is_hajj or is_festival or is_sports_event or is_conference
        features = self.prepare_features(
            target_date=target_date,
            branch_id=branch_id,
            city_id=city_id,
            is_airport=is_airport,
            is_holiday=is_holiday,
            is_school_vacation=is_school_vacation,
            is_ramadan=is_ramadan,
            is_umrah_season=is_umrah_season,
            is_major_event=is_major_event,
            days_to_holiday=days_to_holiday
        )
        logger.info(f"   ✓ Features prepared ({len(features.columns)} features)")
        
        # Step 2: Predict demand
        logger.info("\n2. Predicting demand...")
        predicted_demand = self.predict_demand(features)
        average_demand = self.branch_avg_demand.get(branch_id, predicted_demand)
        logger.info(f"   ✓ Predicted demand: {predicted_demand:.1f} bookings")
        logger.info(f"   ✓ Historical average: {average_demand:.1f} bookings")
        
        # Step 3: Apply pricing rules
        logger.info("\n3. Applying pricing rules...")
        pricing_result = self.pricing_rules.calculate_final_price(
            base_price=base_price,
            predicted_demand=predicted_demand,
            average_demand=average_demand,
            available_vehicles=available_vehicles,
            total_vehicles=total_vehicles,
            is_holiday=is_holiday,
            is_school_vacation=is_school_vacation,
            is_ramadan=is_ramadan,
            is_umrah_season=is_umrah_season,
            is_hajj=is_hajj,
            is_festival=is_festival,
            is_sports_event=is_sports_event,
            is_conference=is_conference,
            is_weekend=(target_date.weekday() in [4, 5]),  # Fri-Sat in KSA
            city_name=city_name,
            is_airport=is_airport,
            days_to_holiday=days_to_holiday
        )
        logger.info(f"   ✓ Pricing rules applied")
        
        # Step 4: Compile result
        result = {
            'target_date': target_date.date(),
            'branch_id': branch_id,
            'predicted_demand': round(predicted_demand, 1),
            'average_demand': round(average_demand, 1),
            'demand_vs_average_pct': round((predicted_demand / average_demand - 1) * 100, 1) if average_demand > 0 else 0,
            **pricing_result
        }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"PRICING SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Base Price:    {result['base_price']:.2f} SAR")
        logger.info(f"Final Price:   {result['final_price']:.2f} SAR ({result['price_change_pct']:+.1f}%)")
        logger.info(f"Demand:        {result['predicted_demand']:.0f} bookings (vs avg {result['average_demand']:.0f})")
        logger.info(f"Multipliers:   Demand={result['demand_multiplier']}, Supply={result['supply_multiplier']}, Event={result['event_multiplier']}")
        logger.info(f"Explanation:   {result['explanation']}")
        logger.info(f"{'='*80}\n")
        
        return result


def main():
    """Demo the pricing engine."""
    logger.info("="*80)
    logger.info("DYNAMIC PRICING ENGINE - DEMONSTRATION")
    logger.info("="*80)
    
    # Initialize engine
    engine = DynamicPricingEngine()
    
    # Demo scenario: Price for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    
    logger.info("\n📊 SCENARIO: Regular Weekday Tomorrow")
    result = engine.calculate_optimized_price(
        target_date=tomorrow,
        branch_id=122,  # Top branch from EDA
        base_price=200.0,
        available_vehicles=60,
        total_vehicles=100,
        city_name="Riyadh",
        is_airport=True,
        is_holiday=False,
        is_school_vacation=False,
        is_hajj=False,
        is_festival=False,
        is_sports_event=False,
        is_conference=False
    )
    
    logger.info("\n" + "="*80)
    logger.info("ENGINE DEMONSTRATION COMPLETE")
    logger.info("="*80)
    logger.info("\n✓ Pricing engine ready for production use")
    logger.info("✓ Predicts demand 1-2 days ahead")
    logger.info("✓ Applies dynamic pricing rules")
    logger.info("✓ Provides explainable pricing decisions")


if __name__ == "__main__":
    main()

