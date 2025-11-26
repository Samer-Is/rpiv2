"""
Real-Time Competitor Web Scraper
Uses Selenium to scrape competitor prices with intelligent matching
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not installed. Run: pip install selenium")

from intelligent_matcher import IntelligentMatcher
from competitor_scraper_config import (
    COMPETITORS,
    SCRAPING_SETTINGS,
    CACHE_SETTINGS,
    FALLBACK_STRATEGY,
    LOGGING_SETTINGS
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOGGING_SETTINGS['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGGING_SETTINGS['log_file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CompetitorPriceScraper:
    """
    Real-time competitor price scraper with intelligent matching
    """
    
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required. Install with: pip install selenium")
        
        self.matcher = IntelligentMatcher()
        self.cache_dir = CACHE_SETTINGS['cache_dir']
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    # ========================================================================
    # MAIN SCRAPING METHOD
    # ========================================================================
    
    def scrape_competitors(
        self,
        renty_location: str,
        renty_category: str,
        pickup_date: datetime,
        return_date: datetime,
        branch_id: Optional[int] = None
    ) -> Dict[str, Dict]:
        """
        Scrape prices from all enabled competitors
        
        Args:
            renty_location: Renty branch location (e.g., "Riyadh - Airport")
            renty_category: Renty vehicle category (e.g., "SUV Standard")
            pickup_date: Pickup date
            return_date: Return date
            branch_id: Optional branch ID
            
        Returns:
            Dictionary with competitor prices and metadata
        """
        logger.info(f"Starting price scraping for {renty_category} at {renty_location}")
        
        results = {}
        enabled_competitors = {
            name: config for name, config in COMPETITORS.items() 
            if config['enabled']
        }
        
        if not enabled_competitors:
            logger.warning("No competitors enabled for scraping")
            return results
        
        # Check cache first
        cache_key = self._generate_cache_key(
            renty_location, renty_category, pickup_date, return_date
        )
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info("✓ Returning cached competitor prices")
            return cached_data
        
        # Scrape in parallel
        if SCRAPING_SETTINGS['parallel_scraping'] and len(enabled_competitors) > 1:
            results = self._scrape_parallel(
                enabled_competitors, renty_location, renty_category, 
                pickup_date, return_date
            )
        else:
            results = self._scrape_sequential(
                enabled_competitors, renty_location, renty_category, 
                pickup_date, return_date
            )
        
        # Cache results
        if results:
            self._cache_data(cache_key, results)
        
        return results
    
    # ========================================================================
    # PARALLEL & SEQUENTIAL SCRAPING
    # ========================================================================
    
    def _scrape_parallel(
        self, 
        competitors: Dict, 
        location: str, 
        category: str, 
        pickup: datetime, 
        return_date: datetime
    ) -> Dict:
        """Scrape multiple competitors in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(competitors)) as executor:
            future_to_competitor = {
                executor.submit(
                    self._scrape_single_competitor, 
                    name, config, location, category, pickup, return_date
                ): name
                for name, config in competitors.items()
            }
            
            for future in as_completed(future_to_competitor):
                competitor_name = future_to_competitor[future]
                try:
                    result = future.result(timeout=SCRAPING_SETTINGS['timeout'])
                    if result:
                        results[competitor_name] = result
                except Exception as e:
                    logger.error(f"Error scraping {competitor_name}: {str(e)}")
                    # Try to load from cache
                    cached = self._get_last_known_price(competitor_name, location, category)
                    if cached:
                        results[competitor_name] = cached
        
        return results
    
    def _scrape_sequential(
        self, 
        competitors: Dict, 
        location: str, 
        category: str, 
        pickup: datetime, 
        return_date: datetime
    ) -> Dict:
        """Scrape competitors one by one"""
        results = {}
        
        for name, config in competitors.items():
            try:
                result = self._scrape_single_competitor(
                    name, config, location, category, pickup, return_date
                )
                if result:
                    results[name] = result
            except Exception as e:
                logger.error(f"Error scraping {name}: {str(e)}")
                # Try to load from cache
                cached = self._get_last_known_price(name, location, category)
                if cached:
                    results[name] = cached
        
        return results
    
    # ========================================================================
    # SINGLE COMPETITOR SCRAPING
    # ========================================================================
    
    def _scrape_single_competitor(
        self,
        competitor_name: str,
        config: Dict,
        renty_location: str,
        renty_category: str,
        pickup_date: datetime,
        return_date: datetime
    ) -> Optional[Dict]:
        """
        Scrape a single competitor's website
        
        Returns:
            Dictionary with price, matched_category, matched_location, etc.
        """
        logger.info(f"Scraping {competitor_name}...")
        
        driver = None
        try:
            # Setup Selenium driver
            driver = self._setup_driver()
            
            # Navigate to competitor website
            search_url = self._build_search_url(
                config, renty_location, renty_category, pickup_date, return_date
            )
            
            logger.debug(f"Navigating to: {search_url}")
            driver.get(search_url)
            
            # Wait for page to load
            time.sleep(config['wait_time'])
            
            # IMPORTANT: This is a TEMPLATE
            # You need to customize the scraping logic for each competitor
            # based on their actual website structure
            
            price = self._extract_price_template(driver, config)
            matched_category = self._extract_category_template(driver, config)
            matched_location = self._extract_location_template(driver, config)
            
            if price:
                result = {
                    'competitor_name': competitor_name,
                    'price': price,
                    'matched_category': matched_category or renty_category,
                    'matched_location': matched_location or renty_location,
                    'currency': 'SAR',
                    'date_scraped': datetime.now().isoformat(),
                    'pickup_date': pickup_date.strftime('%Y-%m-%d'),
                    'return_date': return_date.strftime('%Y-%m-%d'),
                    'source_url': driver.current_url,
                    'scraping_success': True,
                    'error': None
                }
                
                logger.info(f"✓ {competitor_name}: {price} SAR")
                return result
            else:
                logger.warning(f"Could not extract price from {competitor_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {competitor_name}: {str(e)}")
            
            # Take screenshot for debugging
            if SCRAPING_SETTINGS['screenshot_on_error'] and driver:
                self._save_error_screenshot(driver, competitor_name)
            
            return None
            
        finally:
            if driver:
                driver.quit()
    
    # ========================================================================
    # SELENIUM DRIVER SETUP
    # ========================================================================
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if SCRAPING_SETTINGS['headless']:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f"user-agent={SCRAPING_SETTINGS['user_agent']}")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Disable images for faster loading
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(SCRAPING_SETTINGS['timeout'])
        
        return driver
    
    # ========================================================================
    # EXTRACTION TEMPLATES (TO BE CUSTOMIZED)
    # ========================================================================
    
    def _build_search_url(
        self, 
        config: Dict, 
        location: str, 
        category: str, 
        pickup: datetime, 
        return_date: datetime
    ) -> str:
        """
        Build search URL for competitor website
        NOTE: This is a template - needs customization per competitor
        """
        base_url = config['base_url']
        search_page = config['search_page']
        
        # Example URL structure (customize based on actual competitor site)
        url = f"{base_url}{search_page}"
        
        # Add query parameters (customize based on actual site)
        params = {
            'pickup': pickup.strftime('%Y-%m-%d'),
            'return': return_date.strftime('%Y-%m-%d'),
            'location': location,
            'category': category
        }
        
        # For now, return base URL
        # TODO: Customize URL building based on each competitor's structure
        return url
    
    def _extract_price_template(self, driver: webdriver.Chrome, config: Dict) -> Optional[float]:
        """
        Extract price from page
        NOTE: This is a TEMPLATE - must be customized for each competitor
        """
        try:
            # Try multiple selectors
            price_selectors = config['selectors']['price'].split(', ')
            
            for selector in price_selectors:
                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, selector.strip())
                    price_text = price_element.text
                    
                    # Extract numeric price
                    price = self._parse_price(price_text)
                    if price:
                        return price
                except NoSuchElementException:
                    continue
            
            logger.warning("Could not find price element with any selector")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting price: {str(e)}")
            return None
    
    def _extract_category_template(self, driver: webdriver.Chrome, config: Dict) -> Optional[str]:
        """Extract matched category from page"""
        try:
            category_selectors = config['selectors']['category'].split(', ')
            
            for selector in category_selectors:
                try:
                    cat_element = driver.find_element(By.CSS_SELECTOR, selector.strip())
                    return cat_element.text
                except NoSuchElementException:
                    continue
            
            return None
        except:
            return None
    
    def _extract_location_template(self, driver: webdriver.Chrome, config: Dict) -> Optional[str]:
        """Extract matched location from page"""
        try:
            location_selectors = config['selectors']['location'].split(', ')
            
            for selector in location_selectors:
                try:
                    loc_element = driver.find_element(By.CSS_SELECTOR, selector.strip())
                    return loc_element.text
                except NoSuchElementException:
                    continue
            
            return None
        except:
            return None
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        import re
        # Remove currency symbols and extract number
        numbers = re.findall(r'\d+\.?\d*', price_text.replace(',', ''))
        if numbers:
            return float(numbers[0])
        return None
    
    def _save_error_screenshot(self, driver: webdriver.Chrome, competitor_name: str):
        """Save screenshot when scraping fails"""
        try:
            screenshot_dir = "logs/screenshots"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            filename = f"{screenshot_dir}/{competitor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Could not save screenshot: {str(e)}")
    
    # ========================================================================
    # CACHING
    # ========================================================================
    
    def _generate_cache_key(
        self, 
        location: str, 
        category: str, 
        pickup: datetime, 
        return_date: datetime
    ) -> str:
        """Generate unique cache key"""
        key_string = f"{location}_{category}_{pickup.date()}_{return_date.date()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached competitor prices"""
        if not CACHE_SETTINGS['enabled']:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(cached_data['cache_timestamp'])
                if datetime.now() - cache_time < timedelta(seconds=CACHE_SETTINGS['ttl']):
                    logger.info("Cache hit - returning cached prices")
                    return cached_data['data']
            except Exception as e:
                logger.error(f"Error reading cache: {str(e)}")
        
        return None
    
    def _cache_data(self, cache_key: str, data: Dict):
        """Cache competitor prices"""
        if not CACHE_SETTINGS['enabled']:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_entry = {
                'cache_timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            logger.debug(f"Cached data: {cache_file}")
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
    
    def _get_last_known_price(
        self, 
        competitor_name: str, 
        location: str, 
        category: str
    ) -> Optional[Dict]:
        """Get last known price for fallback"""
        if not FALLBACK_STRATEGY['use_cached_on_error']:
            return None
        
        # Search for any cached file with this competitor/location/category
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    with open(filepath, 'r') as f:
                        cached_data = json.load(f)
                    
                    if competitor_name in cached_data.get('data', {}):
                        comp_data = cached_data['data'][competitor_name]
                        
                        # Add timestamp and warning
                        comp_data['is_cached'] = True
                        comp_data['cache_age'] = cached_data['cache_timestamp']
                        comp_data['warning'] = FALLBACK_STRATEGY['default_message']
                        
                        logger.info(f"✓ Using cached price for {competitor_name}")
                        return comp_data
        except Exception as e:
            logger.error(f"Error retrieving last known price: {str(e)}")
        
        return None


# ============================================================================
# TESTING
# ============================================================================

def test_scraper():
    """Test the scraper"""
    print("="*80)
    print("COMPETITOR SCRAPER - TEST")
    print("="*80)
    
    scraper = CompetitorPriceScraper()
    
    # Test scraping
    results = scraper.scrape_competitors(
        renty_location="Riyadh - King Khalid International Airport",
        renty_category="SUV Standard",
        pickup_date=datetime.now() + timedelta(days=1),
        return_date=datetime.now() + timedelta(days=3)
    )
    
    print("\nResults:")
    for competitor, data in results.items():
        print(f"\n{competitor}:")
        print(json.dumps(data, indent=2))
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_scraper()

