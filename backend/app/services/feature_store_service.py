"""
Feature Store Service - CHUNK 6
Builds and populates the fact_daily_demand table for ML training/inference
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FeatureStoreService:
    """
    Service to build and manage the feature store for dynamic pricing ML.
    
    Responsibilities:
    - Aggregate contract data into daily demand by branch×category
    - Join with weather, calendar, and event features
    - Compute lag features for time-series modeling
    - Apply TRAIN/VALIDATION split
    """
    
    # Training cutoff: data before this date is TRAIN, after is VALIDATION
    VALIDATION_CUTOFF = date(2024, 10, 1)  # Q4 2024+
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_feature_store(
        self,
        tenant_id: int = 1,
        start_date: date = date(2023, 1, 1),
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Build the complete feature store for a tenant.
        
        Steps:
        1. Aggregate contract data into daily demand
        2. Join with weather features
        3. Join with calendar/holiday features
        4. Join with event features
        5. Compute lag features
        6. Apply train/validation split
        
        Returns:
            Dict with build statistics
        """
        if end_date is None:
            end_date = date.today()
        
        logger.info(f"Building feature store for tenant {tenant_id} from {start_date} to {end_date}")
        
        # Step 1: Clear existing data for rebuild
        self._clear_existing_data(tenant_id, start_date, end_date)
        
        # Step 2: Insert base demand data
        rows_inserted = self._insert_base_demand(tenant_id, start_date, end_date)
        logger.info(f"Inserted {rows_inserted} base demand rows")
        
        # Step 3: Update weather features
        weather_updated = self._update_weather_features(tenant_id)
        logger.info(f"Updated {weather_updated} rows with weather features")
        
        # Step 4: Update calendar features
        calendar_updated = self._update_calendar_features(tenant_id)
        logger.info(f"Updated {calendar_updated} rows with calendar features")
        
        # Step 5: Update event features
        events_updated = self._update_event_features(tenant_id)
        logger.info(f"Updated {events_updated} rows with event features")
        
        # Step 6: Compute lag features
        lags_updated = self._compute_lag_features(tenant_id)
        logger.info(f"Updated {lags_updated} rows with lag features")
        
        # Step 7: Apply train/validation split
        split_stats = self._apply_split(tenant_id)
        logger.info(f"Split applied: {split_stats}")
        
        # Get final statistics
        stats = self._get_build_statistics(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "date_range": {"start": str(start_date), "end": str(end_date)},
            "rows_inserted": rows_inserted,
            "weather_updated": weather_updated,
            "calendar_updated": calendar_updated,
            "events_updated": events_updated,
            "lags_updated": lags_updated,
            "split_stats": split_stats,
            "final_stats": stats
        }
    
    def _clear_existing_data(self, tenant_id: int, start_date: date, end_date: date) -> int:
        """Clear existing data in date range for rebuild."""
        result = self.db.execute(text("""
            DELETE FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id 
              AND demand_date BETWEEN :start_date AND :end_date
        """), {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date})
        self.db.commit()
        return result.rowcount
    
    def _insert_base_demand(self, tenant_id: int, start_date: date, end_date: date) -> int:
        """
        Insert base demand data from contracts.
        Aggregates by date × branch × category for MVP scope.
        """
        result = self.db.execute(text("""
            INSERT INTO dynamicpricing.fact_daily_demand (
                tenant_id, demand_date, branch_id, category_id,
                executed_rentals_count, avg_base_price_paid, 
                min_base_price_paid, max_base_price_paid,
                day_of_week, day_of_month, week_of_year, month_of_year, quarter,
                is_weekend
            )
            SELECT 
                :tenant_id as tenant_id,
                CAST(c.[Start] AS DATE) as demand_date,
                c.BranchId as branch_id,
                cm.CategoryId as category_id,
                COUNT(*) as executed_rentals_count,
                AVG(c.DailyRateAmount) as avg_base_price_paid,
                MIN(c.DailyRateAmount) as min_base_price_paid,
                MAX(c.DailyRateAmount) as max_base_price_paid,
                DATEPART(WEEKDAY, c.[Start]) - 1 as day_of_week,  -- 0=Sun in SQL Server, adjust as needed
                DATEPART(DAY, c.[Start]) as day_of_month,
                DATEPART(WEEK, c.[Start]) as week_of_year,
                DATEPART(MONTH, c.[Start]) as month_of_year,
                DATEPART(QUARTER, c.[Start]) as quarter,
                CASE WHEN DATEPART(WEEKDAY, c.[Start]) IN (1, 7) THEN 1 ELSE 0 END as is_weekend
            FROM Rental.Contract c
            JOIN Fleet.Vehicles v ON c.VehicleId = v.Id
            JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
            WHERE c.TenantId = :tenant_id
              AND c.Discriminator = 'Contract'
              AND c.StatusId = 211  -- Completed
              AND CAST(c.[Start] AS DATE) BETWEEN :start_date AND :end_date
              AND c.BranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)
              AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)
            GROUP BY 
                CAST(c.[Start] AS DATE),
                c.BranchId,
                cm.CategoryId,
                DATEPART(WEEKDAY, c.[Start]),
                DATEPART(DAY, c.[Start]),
                DATEPART(WEEK, c.[Start]),
                DATEPART(MONTH, c.[Start]),
                DATEPART(QUARTER, c.[Start])
        """), {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date})
        self.db.commit()
        return result.rowcount
    
    def _update_weather_features(self, tenant_id: int) -> int:
        """
        Update weather features from weather_data table.
        Joins on date and branch location (via branch coordinates).
        """
        # First check if weather_data table has data
        check = self.db.execute(text("""
            SELECT COUNT(*) FROM dynamicpricing.weather_data
        """)).scalar()
        
        if check == 0:
            logger.warning("No weather data available, skipping weather features")
            return 0
        
        # Update weather features by joining on date and branch_id
        # weather_data columns: t_max, t_min, t_mean, precipitation_sum, wind_max
        result = self.db.execute(text("""
            UPDATE f
            SET 
                f.temperature_max = w.t_max,
                f.temperature_min = w.t_min,
                f.temperature_avg = w.t_mean,
                f.precipitation_mm = w.precipitation_sum,
                f.wind_speed_kmh = w.wind_max,
                f.updated_at = GETDATE()
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN dynamicpricing.weather_data w 
                ON f.demand_date = w.weather_date
                AND f.branch_id = w.branch_id
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        self.db.commit()
        return result.rowcount
    
    def _update_calendar_features(self, tenant_id: int) -> int:
        """
        Update calendar features from KSA holidays table.
        """
        # Check if holidays table exists and has data
        check = self.db.execute(text("""
            SELECT COUNT(*) FROM dynamicpricing.ksa_holidays
        """)).scalar()
        
        if check == 0:
            logger.warning("No holiday data available, skipping calendar features")
            return 0
        
        # Update public holiday flag
        # ksa_holidays columns: holiday_date, holiday_type, is_public_holiday
        result = self.db.execute(text("""
            UPDATE f
            SET 
                f.is_public_holiday = CASE WHEN h.id IS NOT NULL AND h.is_public_holiday = 1 THEN 1 ELSE f.is_public_holiday END,
                f.is_religious_holiday = CASE 
                    WHEN h.holiday_type IN ('religious', 'islamic') THEN 1 
                    ELSE f.is_religious_holiday
                END,
                f.updated_at = GETDATE()
            FROM dynamicpricing.fact_daily_demand f
            LEFT JOIN dynamicpricing.ksa_holidays h 
                ON f.demand_date = h.holiday_date
            WHERE f.tenant_id = :tenant_id
              AND h.id IS NOT NULL
        """), {"tenant_id": tenant_id})
        self.db.commit()
        return result.rowcount
    
    def _update_event_features(self, tenant_id: int) -> int:
        """
        Update event features from daily event signal table.
        """
        # Check if event signal table exists and has data
        try:
            check = self.db.execute(text("""
                SELECT COUNT(*) FROM dynamicpricing.ksa_daily_event_signal
            """)).scalar()
        except Exception:
            logger.warning("Event signal table not found, skipping event features")
            return 0
        
        if check == 0:
            logger.warning("No event data available, skipping event features")
            return 0
        
        # Update event features
        # ksa_daily_event_signal columns: event_date, gdelt_score
        result = self.db.execute(text("""
            UPDATE f
            SET 
                f.event_score = e.gdelt_score,
                f.has_major_event = CASE WHEN e.gdelt_score >= 3 THEN 1 ELSE 0 END,
                f.updated_at = GETDATE()
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN dynamicpricing.ksa_daily_event_signal e 
                ON f.demand_date = e.event_date
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        self.db.commit()
        return result.rowcount
    
    def _compute_lag_features(self, tenant_id: int) -> int:
        """
        Compute lag features for time-series analysis.
        - rentals_lag_1d: Yesterday's rentals (same branch/category)
        - rentals_lag_7d: Same day last week
        - rentals_rolling_7d_avg: 7-day moving average
        - rentals_rolling_30d_avg: 30-day moving average
        """
        # Compute 1-day lag
        self.db.execute(text("""
            UPDATE f
            SET f.rentals_lag_1d = prev.executed_rentals_count
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN dynamicpricing.fact_daily_demand prev
                ON f.tenant_id = prev.tenant_id
                AND f.branch_id = prev.branch_id
                AND f.category_id = prev.category_id
                AND prev.demand_date = DATEADD(DAY, -1, f.demand_date)
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        
        # Compute 7-day lag (same day last week)
        self.db.execute(text("""
            UPDATE f
            SET f.rentals_lag_7d = prev.executed_rentals_count
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN dynamicpricing.fact_daily_demand prev
                ON f.tenant_id = prev.tenant_id
                AND f.branch_id = prev.branch_id
                AND f.category_id = prev.category_id
                AND prev.demand_date = DATEADD(DAY, -7, f.demand_date)
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        
        # Compute 7-day rolling average
        self.db.execute(text("""
            UPDATE f
            SET f.rentals_rolling_7d_avg = sub.rolling_avg
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN (
                SELECT 
                    f1.id,
                    AVG(CAST(f2.executed_rentals_count AS FLOAT)) as rolling_avg
                FROM dynamicpricing.fact_daily_demand f1
                INNER JOIN dynamicpricing.fact_daily_demand f2
                    ON f1.tenant_id = f2.tenant_id
                    AND f1.branch_id = f2.branch_id
                    AND f1.category_id = f2.category_id
                    AND f2.demand_date BETWEEN DATEADD(DAY, -7, f1.demand_date) AND DATEADD(DAY, -1, f1.demand_date)
                WHERE f1.tenant_id = :tenant_id
                GROUP BY f1.id
            ) sub ON f.id = sub.id
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        
        # Compute 30-day rolling average
        result = self.db.execute(text("""
            UPDATE f
            SET f.rentals_rolling_30d_avg = sub.rolling_avg
            FROM dynamicpricing.fact_daily_demand f
            INNER JOIN (
                SELECT 
                    f1.id,
                    AVG(CAST(f2.executed_rentals_count AS FLOAT)) as rolling_avg
                FROM dynamicpricing.fact_daily_demand f1
                INNER JOIN dynamicpricing.fact_daily_demand f2
                    ON f1.tenant_id = f2.tenant_id
                    AND f1.branch_id = f2.branch_id
                    AND f1.category_id = f2.category_id
                    AND f2.demand_date BETWEEN DATEADD(DAY, -30, f1.demand_date) AND DATEADD(DAY, -1, f1.demand_date)
                WHERE f1.tenant_id = :tenant_id
                GROUP BY f1.id
            ) sub ON f.id = sub.id
            WHERE f.tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        
        self.db.commit()
        return result.rowcount
    
    def _apply_split(self, tenant_id: int) -> Dict[str, int]:
        """
        Apply TRAIN/VALIDATION split based on cutoff date.
        TRAIN: < 2024-10-01
        VALIDATION: >= 2024-10-01
        """
        # Set TRAIN
        train_result = self.db.execute(text("""
            UPDATE dynamicpricing.fact_daily_demand
            SET split_flag = 'TRAIN', updated_at = GETDATE()
            WHERE tenant_id = :tenant_id AND demand_date < :cutoff
        """), {"tenant_id": tenant_id, "cutoff": self.VALIDATION_CUTOFF})
        
        # Set VALIDATION
        val_result = self.db.execute(text("""
            UPDATE dynamicpricing.fact_daily_demand
            SET split_flag = 'VALIDATION', updated_at = GETDATE()
            WHERE tenant_id = :tenant_id AND demand_date >= :cutoff
        """), {"tenant_id": tenant_id, "cutoff": self.VALIDATION_CUTOFF})
        
        self.db.commit()
        
        return {
            "train_count": train_result.rowcount,
            "validation_count": val_result.rowcount
        }
    
    def _get_build_statistics(self, tenant_id: int) -> Dict[str, Any]:
        """Get statistics about the built feature store."""
        stats = {}
        
        # Total rows
        stats["total_rows"] = self.db.execute(text("""
            SELECT COUNT(*) FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).scalar()
        
        # Date range
        date_range = self.db.execute(text("""
            SELECT MIN(demand_date), MAX(demand_date)
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchone()
        stats["date_range"] = {"min": str(date_range[0]), "max": str(date_range[1])}
        
        # Split distribution
        split_dist = self.db.execute(text("""
            SELECT split_flag, COUNT(*) as cnt
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
            GROUP BY split_flag
        """), {"tenant_id": tenant_id}).fetchall()
        stats["split_distribution"] = {row[0]: row[1] for row in split_dist}
        
        # Target variable stats
        target_stats = self.db.execute(text("""
            SELECT 
                AVG(CAST(executed_rentals_count AS FLOAT)) as avg_rentals,
                MIN(executed_rentals_count) as min_rentals,
                MAX(executed_rentals_count) as max_rentals,
                STDEV(CAST(executed_rentals_count AS FLOAT)) as std_rentals
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchone()
        stats["target_stats"] = {
            "avg": float(target_stats[0]) if target_stats[0] else 0,
            "min": target_stats[1],
            "max": target_stats[2],
            "std": float(target_stats[3]) if target_stats[3] else 0
        }
        
        # Feature completeness (% non-null for key features)
        completeness = self.db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN temperature_avg IS NOT NULL THEN 1 ELSE 0 END) as weather_filled,
                SUM(CASE WHEN rentals_lag_1d IS NOT NULL THEN 1 ELSE 0 END) as lag1_filled,
                SUM(CASE WHEN rentals_rolling_7d_avg IS NOT NULL THEN 1 ELSE 0 END) as rolling7_filled
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchone()
        
        total = completeness[0] if completeness[0] > 0 else 1
        stats["feature_completeness"] = {
            "weather_pct": round(100 * completeness[1] / total, 2),
            "lag_1d_pct": round(100 * completeness[2] / total, 2),
            "rolling_7d_pct": round(100 * completeness[3] / total, 2)
        }
        
        # Branch and category coverage
        coverage = self.db.execute(text("""
            SELECT 
                COUNT(DISTINCT branch_id) as branches,
                COUNT(DISTINCT category_id) as categories
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchone()
        stats["coverage"] = {
            "branches": coverage[0],
            "categories": coverage[1]
        }
        
        return stats
    
    def get_training_data(
        self,
        tenant_id: int,
        split: str = "TRAIN"
    ) -> List[Dict[str, Any]]:
        """
        Get training or validation data for ML model.
        
        Args:
            tenant_id: Tenant ID
            split: 'TRAIN' or 'VALIDATION'
            
        Returns:
            List of feature dictionaries
        """
        result = self.db.execute(text("""
            SELECT 
                demand_date, branch_id, category_id,
                executed_rentals_count,
                avg_base_price_paid,
                utilization_contracts, utilization_bookings,
                temperature_avg, precipitation_mm, humidity_pct, wind_speed_kmh,
                is_weekend, is_public_holiday, is_religious_holiday,
                day_of_week, day_of_month, week_of_year, month_of_year, quarter,
                event_score, has_major_event,
                rentals_lag_1d, rentals_lag_7d, 
                rentals_rolling_7d_avg, rentals_rolling_30d_avg
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id AND split_flag = :split
            ORDER BY demand_date, branch_id, category_id
        """), {"tenant_id": tenant_id, "split": split})
        
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]
    
    def validate_feature_store(self, tenant_id: int) -> Dict[str, Any]:
        """
        Validate the feature store meets quality requirements.
        
        Checks:
        1. Row counts match expected
        2. Date ranges are correct
        3. Target variable is not flatline
        4. Missing rate is acceptable
        """
        validation = {"passed": True, "checks": []}
        
        # Check 1: Minimum row count
        total = self.db.execute(text("""
            SELECT COUNT(*) FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).scalar()
        
        min_expected = 1000  # At least 1000 rows for meaningful ML
        check1 = {
            "name": "minimum_rows",
            "passed": total >= min_expected,
            "value": total,
            "threshold": min_expected
        }
        validation["checks"].append(check1)
        if not check1["passed"]:
            validation["passed"] = False
        
        # Check 2: Target not flatline (std > 0)
        std = self.db.execute(text("""
            SELECT STDEV(CAST(executed_rentals_count AS FLOAT))
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).scalar()
        
        check2 = {
            "name": "target_variance",
            "passed": std is not None and float(std) > 0.1,
            "value": float(std) if std else 0,
            "threshold": 0.1
        }
        validation["checks"].append(check2)
        if not check2["passed"]:
            validation["passed"] = False
        
        # Check 3: Train/validation split exists
        split_counts = self.db.execute(text("""
            SELECT split_flag, COUNT(*) 
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
            GROUP BY split_flag
        """), {"tenant_id": tenant_id}).fetchall()
        
        has_train = any(row[0] == 'TRAIN' and row[1] > 0 for row in split_counts)
        has_val = any(row[0] == 'VALIDATION' and row[1] > 0 for row in split_counts)
        
        check3 = {
            "name": "split_exists",
            "passed": has_train and has_val,
            "value": {row[0]: row[1] for row in split_counts}
        }
        validation["checks"].append(check3)
        if not check3["passed"]:
            validation["passed"] = False
        
        # Check 4: Missing rate < 50% for key features
        missing_check = self.db.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN avg_base_price_paid IS NULL THEN 1 ELSE 0 END) as price_missing,
                SUM(CASE WHEN rentals_lag_1d IS NULL THEN 1 ELSE 0 END) as lag_missing
            FROM dynamicpricing.fact_daily_demand
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id}).fetchone()
        
        total = missing_check[0] if missing_check[0] > 0 else 1
        price_missing_pct = 100 * missing_check[1] / total
        lag_missing_pct = 100 * missing_check[2] / total
        
        check4 = {
            "name": "missing_rate",
            "passed": price_missing_pct < 50,
            "value": {
                "price_missing_pct": round(price_missing_pct, 2),
                "lag_missing_pct": round(lag_missing_pct, 2)
            },
            "threshold": 50
        }
        validation["checks"].append(check4)
        if not check4["passed"]:
            validation["passed"] = False
        
        return validation
