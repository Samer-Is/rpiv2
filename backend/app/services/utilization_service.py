"""
Utilization Service
CHUNK 4: Computes fleet utilization per branch × category × date.

Business Logic:
- Utilization = Rented / (Rented + Ready)
- Status 140 = Ready (available for rent)
- Status 141 = Rented (currently on rental)
- Status 143 = Sold (excluded from active fleet)
- Other statuses (maintenance, etc.) are excluded from utilization calculation

The service uses configurable status mappings from appconfig.utilization_status_config
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pyodbc
import json
import logging

logger = logging.getLogger(__name__)


# Default status configuration
# These will be overridden by appconfig.utilization_status_config if available
DEFAULT_STATUS_CONFIG = {
    140: {'name': 'Ready', 'type': 'AVAILABLE'},       # Available for rent
    141: {'name': 'Rented', 'type': 'RENTED'},         # Currently rented
    143: {'name': 'Sold', 'type': 'EXCLUDED'},         # Sold - not in fleet
    144: {'name': 'Maintenance', 'type': 'EXCLUDED'},  # In maintenance
    145: {'name': 'Out Of Service', 'type': 'EXCLUDED'},
    146: {'name': 'Accident', 'type': 'EXCLUDED'},
    147: {'name': 'New', 'type': 'EXCLUDED'},          # New, not ready
    148: {'name': 'Replacement', 'type': 'EXCLUDED'},
    149: {'name': 'Ready To Sell', 'type': 'EXCLUDED'},
    150: {'name': 'Total Damage', 'type': 'EXCLUDED'},
    151: {'name': 'Sold To Insurance', 'type': 'EXCLUDED'},
    152: {'name': 'Stolen', 'type': 'EXCLUDED'},
    153: {'name': 'Has Been Circulated', 'type': 'EXCLUDED'},
    154: {'name': 'Preventive Maintenance', 'type': 'EXCLUDED'},
    155: {'name': 'Not Ready', 'type': 'EXCLUDED'},
    156: {'name': 'In-Use', 'type': 'RENTED'},
}


@dataclass
class UtilizationResult:
    """Result of utilization calculation"""
    branch_id: int
    category_id: int
    category_name: str
    calculation_date: date
    rented_count: int
    available_count: int
    total_active_fleet: int
    utilization: float  # 0.0 to 1.0


@dataclass
class FleetSnapshot:
    """Snapshot of fleet status at a point in time"""
    branch_id: int
    category_id: int
    status_id: int
    status_name: str
    status_type: str  # RENTED, AVAILABLE, EXCLUDED
    vehicle_count: int


class UtilizationService:
    """
    Service to compute fleet utilization from vehicle status data.
    
    Tables involved:
    - Fleet.Vehicles: Current vehicle status and location
    - Fleet.CarModels: Model to category mapping
    - Fleet.CarCategories: Category names
    - dbo.Lookups: Status names (LookupTypeId = 9 for Car Status)
    - appconfig.utilization_status_config: Configurable status mappings
    """
    
    def __init__(self, connection_string: str, tenant_id: int = 1):
        self.connection_string = connection_string
        self.tenant_id = tenant_id
        self._status_config = None
    
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
    
    def _load_status_config(self) -> Dict[int, Dict[str, str]]:
        """Load status configuration from database or use defaults"""
        if self._status_config is not None:
            return self._status_config
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Try to load from appconfig.utilization_status_config
            cursor.execute("""
                SELECT status_id, status_name, status_type
                FROM appconfig.utilization_status_config
                WHERE tenant_id = ? AND is_active = 1
            """, [self.tenant_id])
            
            rows = cursor.fetchall()
            
            if rows:
                self._status_config = {
                    row[0]: {'name': row[1], 'type': row[2]}
                    for row in rows
                }
                logger.info(f"Loaded {len(rows)} status configs from database")
            else:
                # Fall back to defaults
                self._status_config = DEFAULT_STATUS_CONFIG
                logger.info("Using default status configuration")
            
            return self._status_config
        except Exception as e:
            logger.warning(f"Error loading status config: {e}, using defaults")
            self._status_config = DEFAULT_STATUS_CONFIG
            return self._status_config
        finally:
            cursor.close()
            conn.close()
    
    def get_rented_status_ids(self) -> List[int]:
        """Get list of status IDs that count as 'rented'"""
        config = self._load_status_config()
        return [sid for sid, cfg in config.items() if cfg['type'] == 'RENTED']
    
    def get_available_status_ids(self) -> List[int]:
        """Get list of status IDs that count as 'available'"""
        config = self._load_status_config()
        return [sid for sid, cfg in config.items() if cfg['type'] == 'AVAILABLE']
    
    def get_utilization_for_branch_category(
        self,
        branch_id: int,
        category_id: int,
        calculation_date: Optional[date] = None
    ) -> Optional[UtilizationResult]:
        """
        Calculate utilization for a specific branch × category.
        
        Utilization = Rented / (Rented + Available)
        
        Note: This returns current utilization based on vehicle status.
        For historical utilization, we would need contract date ranges.
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            rented_ids = self.get_rented_status_ids()
            available_ids = self.get_available_status_ids()
            
            # Build placeholders for status IDs
            rented_placeholders = ','.join(['?' for _ in rented_ids])
            available_placeholders = ','.join(['?' for _ in available_ids])
            
            query = f"""
            SELECT 
                cm.CategoryId,
                MAX(cc.Name) as CategoryName,
                SUM(CASE WHEN v.StatusId IN ({rented_placeholders}) THEN 1 ELSE 0 END) as RentedCount,
                SUM(CASE WHEN v.StatusId IN ({available_placeholders}) THEN 1 ELSE 0 END) as AvailableCount,
                COUNT(DISTINCT v.Id) as TotalVehicles
            FROM Fleet.Vehicles v
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
            INNER JOIN Fleet.CarCategories cc ON cm.CategoryId = cc.Id
            WHERE v.TenantId = ?
              AND v.IsDeleted = 0
              AND v.VehicleBranchId = ?
              AND cm.CategoryId = ?
              AND v.StatusId IN ({rented_placeholders}, {available_placeholders})
            GROUP BY cm.CategoryId
            """
            
            params = (
                rented_ids + 
                available_ids + 
                [self.tenant_id, branch_id, category_id] + 
                rented_ids + available_ids
            )
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row is None or (row[2] + row[3]) == 0:
                logger.warning(f"No active fleet for branch {branch_id}, category {category_id}")
                return None
            
            rented = row[2] or 0
            available = row[3] or 0
            total_active = rented + available
            
            utilization = rented / total_active if total_active > 0 else 0.0
            
            return UtilizationResult(
                branch_id=branch_id,
                category_id=row[0],
                category_name=self._parse_json_name(row[1]),
                calculation_date=calculation_date,
                rented_count=rented,
                available_count=available,
                total_active_fleet=total_active,
                utilization=round(utilization, 4)
            )
        finally:
            cursor.close()
            conn.close()
    
    def get_all_utilizations(
        self,
        branch_ids: Optional[List[int]] = None,
        category_ids: Optional[List[int]] = None,
        calculation_date: Optional[date] = None
    ) -> List[UtilizationResult]:
        """
        Get utilization for all branch × category combinations.
        
        Args:
            branch_ids: Filter to specific branches (None = all MVP branches)
            category_ids: Filter to specific categories (None = all MVP categories)
            calculation_date: Date for calculation (default = today)
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            rented_ids = self.get_rented_status_ids()
            available_ids = self.get_available_status_ids()
            
            # Build filters
            branch_filter = ""
            category_filter = ""
            params = []
            
            # Add status IDs for CASE statements
            rented_placeholders = ','.join(['?' for _ in rented_ids])
            available_placeholders = ','.join(['?' for _ in available_ids])
            
            params.extend(rented_ids)
            params.extend(available_ids)
            params.append(self.tenant_id)
            
            if branch_ids:
                branch_placeholders = ','.join(['?' for _ in branch_ids])
                branch_filter = f"AND v.VehicleBranchId IN ({branch_placeholders})"
                params.extend(branch_ids)
            else:
                branch_filter = "AND v.VehicleBranchId IN (SELECT BranchId FROM dynamicpricing.TopBranches)"
            
            if category_ids:
                category_placeholders = ','.join(['?' for _ in category_ids])
                category_filter = f"AND cm.CategoryId IN ({category_placeholders})"
                params.extend(category_ids)
            else:
                category_filter = "AND cm.CategoryId IN (SELECT CategoryId FROM dynamicpricing.TopCategories)"
            
            # Add status IDs for WHERE clause
            params.extend(rented_ids)
            params.extend(available_ids)
            
            query = f"""
            SELECT 
                v.VehicleBranchId as BranchId,
                cm.CategoryId,
                MAX(cc.Name) as CategoryName,
                SUM(CASE WHEN v.StatusId IN ({rented_placeholders}) THEN 1 ELSE 0 END) as RentedCount,
                SUM(CASE WHEN v.StatusId IN ({available_placeholders}) THEN 1 ELSE 0 END) as AvailableCount
            FROM Fleet.Vehicles v
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
            INNER JOIN Fleet.CarCategories cc ON cm.CategoryId = cc.Id
            WHERE v.TenantId = ?
              AND v.IsDeleted = 0
              {branch_filter}
              {category_filter}
              AND v.StatusId IN ({rented_placeholders}, {available_placeholders})
            GROUP BY v.VehicleBranchId, cm.CategoryId
            ORDER BY v.VehicleBranchId, cm.CategoryId
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                rented = row[3] or 0
                available = row[4] or 0
                total_active = rented + available
                utilization = rented / total_active if total_active > 0 else 0.0
                
                results.append(UtilizationResult(
                    branch_id=row[0],
                    category_id=row[1],
                    category_name=self._parse_json_name(row[2]),
                    calculation_date=calculation_date,
                    rented_count=rented,
                    available_count=available,
                    total_active_fleet=total_active,
                    utilization=round(utilization, 4)
                ))
            
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_fleet_snapshot(
        self,
        branch_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> List[FleetSnapshot]:
        """
        Get detailed fleet status breakdown.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            config = self._load_status_config()
            
            branch_filter = f"AND v.VehicleBranchId = {branch_id}" if branch_id else ""
            category_filter = f"AND cm.CategoryId = {category_id}" if category_id else ""
            
            query = f"""
            SELECT 
                v.VehicleBranchId as BranchId,
                cm.CategoryId,
                v.StatusId,
                l.Text as StatusName,
                COUNT(*) as VehicleCount
            FROM Fleet.Vehicles v
            INNER JOIN Fleet.CarModels cm ON v.ModelId = cm.Id
            LEFT JOIN dbo.Lookups l ON v.StatusId = l.Id
            WHERE v.TenantId = ?
              AND v.IsDeleted = 0
              {branch_filter}
              {category_filter}
            GROUP BY v.VehicleBranchId, cm.CategoryId, v.StatusId, l.Text
            ORDER BY v.VehicleBranchId, cm.CategoryId, VehicleCount DESC
            """
            
            cursor.execute(query, [self.tenant_id])
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                status_id = row[2]
                status_type = config.get(status_id, {}).get('type', 'UNKNOWN')
                
                results.append(FleetSnapshot(
                    branch_id=row[0],
                    category_id=row[1],
                    status_id=status_id,
                    status_name=self._parse_json_name(row[3]) if row[3] else f"Status {status_id}",
                    status_type=status_type,
                    vehicle_count=row[4]
                ))
            
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_status_config_summary(self) -> Dict[str, Any]:
        """Get summary of current status configuration"""
        config = self._load_status_config()
        
        summary = {
            'rented_statuses': [],
            'available_statuses': [],
            'excluded_statuses': [],
            'total_configured': len(config)
        }
        
        for sid, cfg in config.items():
            entry = {'id': sid, 'name': cfg['name']}
            if cfg['type'] == 'RENTED':
                summary['rented_statuses'].append(entry)
            elif cfg['type'] == 'AVAILABLE':
                summary['available_statuses'].append(entry)
            else:
                summary['excluded_statuses'].append(entry)
        
        return summary


# Convenience function for quick testing
def get_utilization_service(tenant_id: int = 1) -> UtilizationService:
    """Create UtilizationService with default connection string"""
    conn_str = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=localhost;"
        "Database=eJarDbSTGLite;"
        "Trusted_Connection=yes;"
    )
    return UtilizationService(conn_str, tenant_id)


if __name__ == "__main__":
    # Quick test
    from datetime import date
    
    service = get_utilization_service()
    today = date.today()
    
    print("=" * 70)
    print("UTILIZATION SERVICE TEST")
    print(f"Date: {today}")
    print("=" * 70)
    
    # Print status config
    print("\nStatus Configuration:")
    config = service.get_status_config_summary()
    print(f"  Rented: {config['rented_statuses']}")
    print(f"  Available: {config['available_statuses']}")
    print(f"  Excluded: {len(config['excluded_statuses'])} statuses")
    
    # Get all utilizations
    print("\n" + "=" * 70)
    print("ALL UTILIZATIONS (MVP Branches × Categories)")
    print("=" * 70)
    
    results = service.get_all_utilizations()
    
    print(f"\n{'Branch':<8} {'Category':<25} {'Rented':>8} {'Avail':>8} {'Total':>8} {'Util':>8}")
    print("-" * 70)
    
    for r in results:
        print(f"{r.branch_id:<8} {r.category_name[:24]:<25} {r.rented_count:>8} {r.available_count:>8} {r.total_active_fleet:>8} {r.utilization:>7.1%}")
    
    # Test specific branch × category
    print("\n" + "=" * 70)
    print("SPECIFIC TEST: Branch 122 × Category 27 (Compact)")
    print("=" * 70)
    
    result = service.get_utilization_for_branch_category(122, 27)
    if result:
        print(f"  Rented: {result.rented_count}")
        print(f"  Available: {result.available_count}")
        print(f"  Total Active Fleet: {result.total_active_fleet}")
        print(f"  Utilization: {result.utilization:.1%}")
