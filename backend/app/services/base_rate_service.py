"""
Base Rate Service
CHUNK 3: Returns daily/weekly/monthly base prices for branch × category combinations.

Business Logic:
- Prices are stored per Model, not per Category
- We aggregate prices at Category level for dynamic pricing
- BranchId NULL = default rates (applies to all branches)
- Branch-specific rates override defaults (not implemented in YELO currently)
- Period types: Daily (1-6 days), Weekly (7-27 days), Monthly (28+ days)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pyodbc
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class BasePriceResult:
    """Result of base price lookup"""
    branch_id: int
    category_id: int
    category_name: str
    effective_date: date
    daily_rate: Decimal
    weekly_rate: Decimal
    monthly_rate: Decimal
    model_count: int
    source: str  # 'branch_specific' or 'default'


@dataclass
class ModelPrice:
    """Price for a specific model"""
    model_id: int
    model_name: str
    category_id: int
    category_name: str
    daily_rate: Optional[Decimal]
    weekly_rate: Optional[Decimal]
    monthly_rate: Optional[Decimal]
    effective_from: datetime
    effective_until: Optional[datetime]


class BaseRateService:
    """
    Service to retrieve base rental rates from the Renty database.
    
    Tables involved:
    - Rental.RentalRates: Rate definitions with ModelId, BranchId, Start/End dates
    - Rental.RentalRatesSchemaPeriods: Period definitions (Daily, Weekly, Monthly)
    - Rental.RentalRatesSchemaPeriodsDetails: Actual rate values
    - Rental.CarModels: Model to Category mapping
    """
    
    def __init__(self, connection_string: str, tenant_id: int = 1):
        self.connection_string = connection_string
        self.tenant_id = tenant_id
    
    def _get_connection(self):
        """Create database connection"""
        return pyodbc.connect(self.connection_string)
    
    def _parse_json_name(self, json_str: str, lang: str = 'en') -> str:
        """Parse JSON name field and return the specified language"""
        try:
            data = json.loads(json_str)
            return data.get(lang, data.get('en', str(json_str)))
        except (json.JSONDecodeError, TypeError):
            return str(json_str)
    
    def get_base_prices_for_category(
        self,
        branch_id: int,
        category_id: int,
        effective_date: date
    ) -> Optional[BasePriceResult]:
        """
        Get aggregated base prices for a branch × category combination.
        
        Uses average prices across all models in the category.
        Falls back to default rates if no branch-specific rates exist.
        
        Args:
            branch_id: Branch ID
            category_id: Car category ID
            effective_date: Date for which to get prices
            
        Returns:
            BasePriceResult with daily/weekly/monthly rates, or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # First try branch-specific rates
            result = self._query_prices(cursor, category_id, effective_date, branch_id)
            source = 'branch_specific'
            
            # Fall back to default rates if no branch-specific rates
            if result is None or result['model_count'] == 0:
                result = self._query_prices(cursor, category_id, effective_date, branch_id=None)
                source = 'default'
            
            if result is None or result['model_count'] == 0:
                logger.warning(f"No prices found for branch={branch_id}, category={category_id}, date={effective_date}")
                return None
            
            return BasePriceResult(
                branch_id=branch_id,
                category_id=category_id,
                category_name=self._parse_json_name(result['category_name']),
                effective_date=effective_date,
                daily_rate=result['daily_rate'] or Decimal('0'),
                weekly_rate=result['weekly_rate'] or Decimal('0'),
                monthly_rate=result['monthly_rate'] or Decimal('0'),
                model_count=result['model_count'],
                source=source
            )
        finally:
            cursor.close()
            conn.close()
    
    def _query_prices(
        self,
        cursor,
        category_id: int,
        effective_date: date,
        branch_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Query prices from the database.
        
        Returns aggregated daily/weekly/monthly rates for the category.
        """
        # Build branch condition
        if branch_id is not None:
            branch_condition = "rr.BranchId = ?"
            params = [self.tenant_id, category_id, effective_date, effective_date, branch_id]
        else:
            branch_condition = "rr.BranchId IS NULL"
            params = [self.tenant_id, category_id, effective_date, effective_date]
        
        query = f"""
        WITH CategoryPrices AS (
            SELECT 
                cm.CarCategoryId,
                cm.CarCategoryName,
                rr.ModelId,
                sp.[From] as MinDays,
                sp.[To] as MaxDays,
                spd.Rate
            FROM Rental.RentalRates rr
            INNER JOIN Rental.RentalRatesSchemaPeriods sp 
                ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
            INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
                ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
            INNER JOIN Rental.CarModels cm 
                ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
            WHERE rr.TenantId = ?
              AND rr.IsActive = 1
              AND cm.CarCategoryId = ?
              AND rr.Start <= ?
              AND (rr.[End] IS NULL OR rr.[End] >= ?)
              AND {branch_condition}
        )
        SELECT 
            CarCategoryId,
            MAX(CarCategoryName) as CarCategoryName,
            COUNT(DISTINCT ModelId) as ModelCount,
            AVG(CASE WHEN MinDays = 1 AND (MaxDays = 6 OR MaxDays IS NULL AND MinDays = 1) THEN Rate END) as DailyRate,
            AVG(CASE WHEN MinDays = 7 AND MaxDays = 27 THEN Rate END) as WeeklyRate,
            AVG(CASE WHEN MinDays = 28 AND MaxDays IS NULL THEN Rate END) as MonthlyRate
        FROM CategoryPrices
        GROUP BY CarCategoryId
        """
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return {
            'category_id': row[0],
            'category_name': row[1],
            'model_count': row[2] or 0,
            'daily_rate': row[3],
            'weekly_rate': row[4],
            'monthly_rate': row[5]
        }
    
    def get_model_prices(
        self,
        category_id: int,
        effective_date: date,
        branch_id: Optional[int] = None
    ) -> List[ModelPrice]:
        """
        Get prices for all models in a category.
        
        Args:
            category_id: Car category ID
            effective_date: Date for which to get prices
            branch_id: Optional branch ID (None for default rates)
            
        Returns:
            List of ModelPrice objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Build branch condition
            if branch_id is not None:
                branch_condition = "rr.BranchId = ?"
                params = [self.tenant_id, category_id, effective_date, effective_date, branch_id]
            else:
                branch_condition = "rr.BranchId IS NULL"
                params = [self.tenant_id, category_id, effective_date, effective_date]
            
            query = f"""
            SELECT 
                rr.ModelId,
                cm.CarModelName,
                cm.CarCategoryId,
                cm.CarCategoryName,
                MAX(CASE WHEN sp.[From] = 1 AND (sp.[To] = 6 OR sp.[To] IS NULL AND sp.[From] = 1) THEN spd.Rate END) as DailyRate,
                MAX(CASE WHEN sp.[From] = 7 AND sp.[To] = 27 THEN spd.Rate END) as WeeklyRate,
                MAX(CASE WHEN sp.[From] = 28 AND sp.[To] IS NULL THEN spd.Rate END) as MonthlyRate,
                MAX(rr.Start) as EffectiveFrom,
                MAX(rr.[End]) as EffectiveUntil
            FROM Rental.RentalRates rr
            INNER JOIN Rental.RentalRatesSchemaPeriods sp 
                ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
            INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
                ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
            INNER JOIN Rental.CarModels cm 
                ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
            WHERE rr.TenantId = ?
              AND rr.IsActive = 1
              AND cm.CarCategoryId = ?
              AND rr.Start <= ?
              AND (rr.[End] IS NULL OR rr.[End] >= ?)
              AND {branch_condition}
            GROUP BY rr.ModelId, cm.CarModelName, cm.CarCategoryId, cm.CarCategoryName
            ORDER BY cm.CarModelName
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(ModelPrice(
                    model_id=row[0],
                    model_name=self._parse_json_name(row[1]),
                    category_id=row[2],
                    category_name=self._parse_json_name(row[3]),
                    daily_rate=row[4],
                    weekly_rate=row[5],
                    monthly_rate=row[6],
                    effective_from=row[7],
                    effective_until=row[8]
                ))
            
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_all_category_prices(
        self,
        effective_date: date,
        category_ids: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get base prices for all (or specified) categories.
        
        Args:
            effective_date: Date for which to get prices
            category_ids: Optional list of category IDs to filter
            
        Returns:
            Dictionary mapping category_id to price info
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            category_filter = ""
            params = [self.tenant_id, effective_date, effective_date]
            
            if category_ids:
                placeholders = ','.join(['?' for _ in category_ids])
                category_filter = f"AND cm.CarCategoryId IN ({placeholders})"
                params.extend(category_ids)
            
            query = f"""
            WITH CategoryPrices AS (
                SELECT 
                    cm.CarCategoryId,
                    cm.CarCategoryName,
                    rr.ModelId,
                    sp.[From] as MinDays,
                    sp.[To] as MaxDays,
                    spd.Rate
                FROM Rental.RentalRates rr
                INNER JOIN Rental.RentalRatesSchemaPeriods sp 
                    ON rr.SchemaId = sp.RentalRatesSchemaId AND rr.TenantId = sp.TenantId
                INNER JOIN Rental.RentalRatesSchemaPeriodsDetails spd 
                    ON sp.Id = spd.RentalRatesSchemaPeriodId AND rr.Id = spd.RentalRateId
                INNER JOIN Rental.CarModels cm 
                    ON rr.ModelId = cm.ModelId AND rr.TenantId = cm.TenantId
                WHERE rr.TenantId = ?
                  AND rr.IsActive = 1
                  AND rr.BranchId IS NULL  -- Default rates only
                  AND rr.Start <= ?
                  AND (rr.[End] IS NULL OR rr.[End] >= ?)
                  {category_filter}
            )
            SELECT 
                CarCategoryId,
                MAX(CarCategoryName) as CarCategoryName,
                COUNT(DISTINCT ModelId) as ModelCount,
                AVG(CASE WHEN MinDays = 1 AND (MaxDays = 6 OR MaxDays IS NULL AND MinDays = 1) THEN Rate END) as DailyRate,
                AVG(CASE WHEN MinDays = 7 AND MaxDays = 27 THEN Rate END) as WeeklyRate,
                AVG(CASE WHEN MinDays = 28 AND MaxDays IS NULL THEN Rate END) as MonthlyRate
            FROM CategoryPrices
            GROUP BY CarCategoryId
            ORDER BY CarCategoryId
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = {}
            for row in rows:
                category_id = row[0]
                results[category_id] = {
                    'category_id': category_id,
                    'category_name': self._parse_json_name(row[1]),
                    'model_count': row[2] or 0,
                    'daily_rate': float(row[3]) if row[3] else None,
                    'weekly_rate': float(row[4]) if row[4] else None,
                    'monthly_rate': float(row[5]) if row[5] else None
                }
            
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_mvp_category_prices(self, effective_date: date) -> Dict[int, Dict[str, Any]]:
        """
        Get base prices for MVP categories only.
        
        MVP Categories (from dynamicpricing.TopCategories):
        - 1: Economy
        - 2: Small Sedan
        - 3: Intermediate Sedan
        - 13: Intermediate SUV
        - 27: Compact
        - 29: Economy SUV
        """
        mvp_categories = [1, 2, 3, 13, 27, 29]
        return self.get_all_category_prices(effective_date, mvp_categories)


# Convenience function for quick testing
def get_base_rate_service(tenant_id: int = 1) -> BaseRateService:
    """Create BaseRateService with default connection string"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=eJarDbSTGLite;"
        "Trusted_Connection=yes;"
    )
    return BaseRateService(conn_str, tenant_id)


if __name__ == "__main__":
    # Quick test
    from datetime import date
    
    service = get_base_rate_service()
    simulation_date = date(2025, 5, 31)
    
    print("=" * 70)
    print("BASE RATE SERVICE TEST")
    print(f"Simulation Date: {simulation_date}")
    print("=" * 70)
    
    # Test MVP category prices
    prices = service.get_mvp_category_prices(simulation_date)
    print("\nMVP Category Prices:")
    for cat_id, info in prices.items():
        print(f"  {cat_id}: {info['category_name']}")
        print(f"      Daily: {info['daily_rate']:.2f} SAR" if info['daily_rate'] else "      Daily: N/A")
        print(f"      Weekly: {info['weekly_rate']:.2f} SAR" if info['weekly_rate'] else "      Weekly: N/A")
        print(f"      Monthly: {info['monthly_rate']:.2f} SAR" if info['monthly_rate'] else "      Monthly: N/A")
        print(f"      Models: {info['model_count']}")
    
    # Test specific branch × category
    print("\n" + "=" * 70)
    print("Branch × Category Test (Branch 122, Category 27)")
    print("=" * 70)
    result = service.get_base_prices_for_category(122, 27, simulation_date)
    if result:
        print(f"  Category: {result.category_name}")
        print(f"  Daily Rate: {result.daily_rate:.2f} SAR")
        print(f"  Weekly Rate: {result.weekly_rate:.2f} SAR")
        print(f"  Monthly Rate: {result.monthly_rate:.2f} SAR")
        print(f"  Source: {result.source}")
        print(f"  Models: {result.model_count}")
    else:
        print("  No prices found!")
