"""
Weather Service
CHUNK 5: Fetches weather data from Open-Meteo API

Sources:
- Historical weather: https://archive-api.open-meteo.com/v1/archive
- Forecast weather: https://api.open-meteo.com/v1/forecast

Features engineered:
- t_mean_next_24h: Average temperature
- t_max_next_24h: Maximum temperature  
- wind_mean_next_24h: Average wind speed
- visibility_min_next_24h: Minimum visibility (estimated from cloud cover)
- bad_weather_score: 0-1 scale based on rain/wind/visibility
- extreme_heat_flag: 1 if max temp > 43°C

Supports:
- Historical mode (for training data backfill)
- Forecast mode (for production 30-day window)
"""
import requests
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pyodbc
import logging
import time

logger = logging.getLogger(__name__)

# Open-Meteo API endpoints
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"

# Weather variables to fetch
HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m", 
    "wind_speed_10m",
    "precipitation",
    "cloud_cover",
    "weather_code"
]

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
    "weather_code"
]


@dataclass
class WeatherFeatures:
    """Weather features for a single date and location"""
    weather_date: date
    city_name: str
    latitude: float
    longitude: float
    t_mean: float
    t_max: float
    t_min: float
    wind_max: float
    precipitation_sum: float
    weather_code: int
    bad_weather_score: float  # 0-1 scale
    extreme_heat_flag: int    # 1 if t_max > 43°C
    

class WeatherService:
    """
    Service to fetch and store weather data from Open-Meteo API.
    
    Supports:
    - Historical data (for training backfill)
    - Forecast data (for production 30-day window)
    """
    
    def __init__(self, connection_string: str, tenant_id: int = 1):
        self.connection_string = connection_string
        self.tenant_id = tenant_id
        self._retry_delay = 1  # seconds between retries
        self._max_retries = 3
        
    def _get_connection(self):
        return pyodbc.connect(self.connection_string)
    
    def _fetch_with_retry(self, url: str, params: dict) -> Optional[dict]:
        """Fetch from API with retry logic"""
        for attempt in range(self._max_retries):
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                else:
                    logger.error(f"All {self._max_retries} attempts failed")
                    return None
        return None
    
    def _calculate_bad_weather_score(
        self, 
        precipitation: float,
        wind_max: float, 
        weather_code: int
    ) -> float:
        """
        Calculate bad weather score (0-1) based on conditions.
        
        Weather codes:
        - 0: Clear sky
        - 1-3: Mainly clear, partly cloudy, overcast
        - 45-48: Fog
        - 51-55: Drizzle
        - 61-65: Rain
        - 66-67: Freezing rain
        - 71-77: Snow
        - 80-82: Rain showers
        - 85-86: Snow showers
        - 95-99: Thunderstorm
        """
        score = 0.0
        
        # Precipitation factor (0-0.4)
        if precipitation > 0:
            if precipitation > 20:
                score += 0.4
            elif precipitation > 10:
                score += 0.3
            elif precipitation > 5:
                score += 0.2
            else:
                score += 0.1
        
        # Wind factor (0-0.3)
        if wind_max > 50:  # km/h
            score += 0.3
        elif wind_max > 30:
            score += 0.2
        elif wind_max > 20:
            score += 0.1
        
        # Weather code factor (0-0.3)
        if weather_code >= 95:  # Thunderstorm
            score += 0.3
        elif weather_code >= 61:  # Rain/snow
            score += 0.2
        elif weather_code >= 45:  # Fog/drizzle
            score += 0.1
        
        return min(score, 1.0)
    
    def get_branch_locations(self) -> List[Dict[str, Any]]:
        """Get branch locations from branch_city_mapping"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT branch_id, city_name, latitude, longitude
                FROM appconfig.branch_city_mapping
                WHERE tenant_id = ? AND is_active = 1
            """, [self.tenant_id])
            
            locations = []
            for row in cursor.fetchall():
                locations.append({
                    "branch_id": row[0],
                    "city_name": row[1],
                    "latitude": float(row[2]),
                    "longitude": float(row[3])
                })
            return locations
        finally:
            cursor.close()
            conn.close()
    
    def fetch_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date
    ) -> List[WeatherFeatures]:
        """
        Fetch historical weather data from Open-Meteo Archive API.
        
        Note: Archive API has a 100-day limit per request.
        """
        results = []
        
        # Split into chunks if date range > 100 days
        current_start = start_date
        while current_start <= end_date:
            chunk_end = min(current_start + timedelta(days=99), end_date)
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": current_start.isoformat(),
                "end_date": chunk_end.isoformat(),
                "daily": ",".join(DAILY_VARIABLES),
                "timezone": "Asia/Riyadh"
            }
            
            data = self._fetch_with_retry(ARCHIVE_API_URL, params)
            
            if data and "daily" in data:
                daily = data["daily"]
                times = daily.get("time", [])
                
                for i, time_str in enumerate(times):
                    weather_date = date.fromisoformat(time_str)
                    t_max = daily["temperature_2m_max"][i] or 0
                    t_min = daily["temperature_2m_min"][i] or 0
                    t_mean = daily["temperature_2m_mean"][i] or 0
                    precip = daily["precipitation_sum"][i] or 0
                    wind_max = daily["wind_speed_10m_max"][i] or 0
                    weather_code = daily["weather_code"][i] or 0
                    
                    bad_score = self._calculate_bad_weather_score(
                        precip, wind_max, weather_code
                    )
                    extreme_heat = 1 if t_max > 43 else 0
                    
                    results.append(WeatherFeatures(
                        weather_date=weather_date,
                        city_name="",  # Will be set by caller
                        latitude=latitude,
                        longitude=longitude,
                        t_mean=t_mean,
                        t_max=t_max,
                        t_min=t_min,
                        wind_max=wind_max,
                        precipitation_sum=precip,
                        weather_code=weather_code,
                        bad_weather_score=bad_score,
                        extreme_heat_flag=extreme_heat
                    ))
            
            current_start = chunk_end + timedelta(days=1)
            time.sleep(0.5)  # Rate limiting
        
        return results
    
    def fetch_forecast_weather(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 16  # Open-Meteo free tier limit
    ) -> List[WeatherFeatures]:
        """
        Fetch forecast weather data from Open-Meteo Forecast API.
        
        Note: Free tier supports up to 16 days forecast.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(DAILY_VARIABLES),
            "forecast_days": forecast_days,
            "timezone": "Asia/Riyadh"
        }
        
        data = self._fetch_with_retry(FORECAST_API_URL, params)
        results = []
        
        if data and "daily" in data:
            daily = data["daily"]
            times = daily.get("time", [])
            
            for i, time_str in enumerate(times):
                weather_date = date.fromisoformat(time_str)
                t_max = daily["temperature_2m_max"][i] or 0
                t_min = daily["temperature_2m_min"][i] or 0
                t_mean = daily["temperature_2m_mean"][i] or 0
                precip = daily["precipitation_sum"][i] or 0
                wind_max = daily["wind_speed_10m_max"][i] or 0
                weather_code = daily["weather_code"][i] or 0
                
                bad_score = self._calculate_bad_weather_score(
                    precip, wind_max, weather_code
                )
                extreme_heat = 1 if t_max > 43 else 0
                
                results.append(WeatherFeatures(
                    weather_date=weather_date,
                    city_name="",
                    latitude=latitude,
                    longitude=longitude,
                    t_mean=t_mean,
                    t_max=t_max,
                    t_min=t_min,
                    wind_max=wind_max,
                    precipitation_sum=precip,
                    weather_code=weather_code,
                    bad_weather_score=bad_score,
                    extreme_heat_flag=extreme_heat
                ))
        
        return results
    
    def ensure_weather_table_exists(self):
        """Create weather_data table if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'dynamicpricing' AND TABLE_NAME = 'weather_data'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    CREATE TABLE dynamicpricing.weather_data (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        tenant_id INT NOT NULL,
                        branch_id INT NOT NULL,
                        city_name NVARCHAR(100) NOT NULL,
                        weather_date DATE NOT NULL,
                        latitude DECIMAL(10, 6) NOT NULL,
                        longitude DECIMAL(10, 6) NOT NULL,
                        t_mean DECIMAL(5, 2),
                        t_max DECIMAL(5, 2),
                        t_min DECIMAL(5, 2),
                        wind_max DECIMAL(5, 2),
                        precipitation_sum DECIMAL(8, 2),
                        weather_code INT,
                        bad_weather_score DECIMAL(3, 2),
                        extreme_heat_flag INT DEFAULT 0,
                        data_source NVARCHAR(20) DEFAULT 'open-meteo',
                        is_forecast BIT DEFAULT 0,
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME DEFAULT GETDATE(),
                        CONSTRAINT UQ_weather_branch_date UNIQUE (tenant_id, branch_id, weather_date)
                    )
                """)
                
                # Create index for faster lookups
                cursor.execute("""
                    CREATE INDEX IX_weather_date_branch 
                    ON dynamicpricing.weather_data (tenant_id, weather_date, branch_id)
                """)
                
                conn.commit()
                logger.info("Created dynamicpricing.weather_data table")
            
            return True
        except Exception as e:
            logger.error(f"Error creating weather table: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    
    def upsert_weather_data(
        self, 
        branch_id: int,
        city_name: str,
        features: List[WeatherFeatures],
        is_forecast: bool = False
    ) -> int:
        """
        Insert or update weather data in the database.
        Returns count of rows affected.
        """
        if not features:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        count = 0
        
        try:
            for f in features:
                cursor.execute("""
                    MERGE INTO dynamicpricing.weather_data AS target
                    USING (SELECT ? as tenant_id, ? as branch_id, ? as weather_date) AS source
                    ON target.tenant_id = source.tenant_id 
                       AND target.branch_id = source.branch_id 
                       AND target.weather_date = source.weather_date
                    WHEN MATCHED THEN
                        UPDATE SET
                            city_name = ?,
                            latitude = ?,
                            longitude = ?,
                            t_mean = ?,
                            t_max = ?,
                            t_min = ?,
                            wind_max = ?,
                            precipitation_sum = ?,
                            weather_code = ?,
                            bad_weather_score = ?,
                            extreme_heat_flag = ?,
                            is_forecast = ?,
                            updated_at = GETDATE()
                    WHEN NOT MATCHED THEN
                        INSERT (tenant_id, branch_id, city_name, weather_date, latitude, longitude,
                                t_mean, t_max, t_min, wind_max, precipitation_sum, weather_code,
                                bad_weather_score, extreme_heat_flag, is_forecast)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, [
                    # MERGE source
                    self.tenant_id, branch_id, f.weather_date,
                    # UPDATE values
                    city_name, f.latitude, f.longitude, f.t_mean, f.t_max, f.t_min,
                    f.wind_max, f.precipitation_sum, f.weather_code,
                    f.bad_weather_score, f.extreme_heat_flag, is_forecast,
                    # INSERT values
                    self.tenant_id, branch_id, city_name, f.weather_date, f.latitude, f.longitude,
                    f.t_mean, f.t_max, f.t_min, f.wind_max, f.precipitation_sum, f.weather_code,
                    f.bad_weather_score, f.extreme_heat_flag, is_forecast
                ])
                count += 1
            
            conn.commit()
            logger.info(f"Upserted {count} weather records for branch {branch_id}")
            return count
        except Exception as e:
            logger.error(f"Error upserting weather data: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def backfill_historical_weather(
        self,
        start_date: date,
        end_date: date,
        branch_ids: Optional[List[int]] = None
    ) -> Dict[int, int]:
        """
        Backfill historical weather data for all or specific branches.
        Returns dict of branch_id -> rows inserted.
        """
        self.ensure_weather_table_exists()
        
        locations = self.get_branch_locations()
        if branch_ids:
            locations = [l for l in locations if l["branch_id"] in branch_ids]
        
        results = {}
        for loc in locations:
            logger.info(f"Fetching weather for {loc['city_name']} ({loc['branch_id']})")
            
            features = self.fetch_historical_weather(
                loc["latitude"],
                loc["longitude"],
                start_date,
                end_date
            )
            
            count = self.upsert_weather_data(
                loc["branch_id"],
                loc["city_name"],
                features,
                is_forecast=False
            )
            results[loc["branch_id"]] = count
            
            time.sleep(1)  # Rate limiting between branches
        
        return results
    
    def update_forecast_weather(
        self,
        branch_ids: Optional[List[int]] = None
    ) -> Dict[int, int]:
        """
        Fetch and store forecast weather data for all or specific branches.
        Returns dict of branch_id -> rows inserted.
        """
        self.ensure_weather_table_exists()
        
        locations = self.get_branch_locations()
        if branch_ids:
            locations = [l for l in locations if l["branch_id"] in branch_ids]
        
        results = {}
        for loc in locations:
            logger.info(f"Fetching forecast for {loc['city_name']} ({loc['branch_id']})")
            
            features = self.fetch_forecast_weather(
                loc["latitude"],
                loc["longitude"]
            )
            
            count = self.upsert_weather_data(
                loc["branch_id"],
                loc["city_name"],
                features,
                is_forecast=True
            )
            results[loc["branch_id"]] = count
            
            time.sleep(0.5)  # Rate limiting
        
        return results
    
    def get_weather_for_date_range(
        self,
        branch_id: int,
        start_date: date,
        end_date: date
    ) -> List[WeatherFeatures]:
        """Get stored weather data for a branch and date range"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT weather_date, city_name, latitude, longitude,
                       t_mean, t_max, t_min, wind_max, precipitation_sum,
                       weather_code, bad_weather_score, extreme_heat_flag
                FROM dynamicpricing.weather_data
                WHERE tenant_id = ? AND branch_id = ?
                  AND weather_date BETWEEN ? AND ?
                ORDER BY weather_date
            """, [self.tenant_id, branch_id, start_date, end_date])
            
            results = []
            for row in cursor.fetchall():
                results.append(WeatherFeatures(
                    weather_date=row[0],
                    city_name=row[1],
                    latitude=float(row[2]),
                    longitude=float(row[3]),
                    t_mean=float(row[4] or 0),
                    t_max=float(row[5] or 0),
                    t_min=float(row[6] or 0),
                    wind_max=float(row[7] or 0),
                    precipitation_sum=float(row[8] or 0),
                    weather_code=row[9] or 0,
                    bad_weather_score=float(row[10] or 0),
                    extreme_heat_flag=row[11] or 0
                ))
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_weather_summary(self) -> Dict[str, Any]:
        """Get summary statistics of weather data in database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT branch_id) as branch_count,
                    MIN(weather_date) as min_date,
                    MAX(weather_date) as max_date,
                    SUM(CASE WHEN is_forecast = 1 THEN 1 ELSE 0 END) as forecast_rows,
                    SUM(CASE WHEN is_forecast = 0 THEN 1 ELSE 0 END) as historical_rows
                FROM dynamicpricing.weather_data
                WHERE tenant_id = ?
            """, [self.tenant_id])
            
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                return {
                    "total_rows": row[0],
                    "branch_count": row[1],
                    "min_date": row[2].isoformat() if row[2] else None,
                    "max_date": row[3].isoformat() if row[3] else None,
                    "forecast_rows": row[4],
                    "historical_rows": row[5]
                }
            else:
                return {
                    "total_rows": 0,
                    "branch_count": 0,
                    "min_date": None,
                    "max_date": None,
                    "forecast_rows": 0,
                    "historical_rows": 0
                }
        except Exception as e:
            logger.warning(f"Error getting weather summary: {e}")
            return {"error": str(e)}
        finally:
            cursor.close()
            conn.close()
