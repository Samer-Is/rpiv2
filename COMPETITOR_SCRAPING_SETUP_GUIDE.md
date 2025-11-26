# 🌐 Real-Time Competitor Price Scraping - Setup Guide

## Date: November 26, 2025
## Status: READY TO CONFIGURE

---

## 📋 OVERVIEW

This system provides **real-time competitor price scraping** with:
- ✅ Intelligent category matching (Renty → Competitor categories)
- ✅ Smart location mapping (Branch → Competitor locations)
- ✅ Parallel scraping (3 competitors simultaneously)
- ✅ Automatic caching (10 minutes TTL)
- ✅ Fallback to last known prices on failure
- ✅ Selenium-based scraping (handles JavaScript)

---

## 🚀 INSTALLATION

### Step 1: Install Required Packages

```bash
pip install -r requirements.txt
```

This installs:
- `selenium==4.15.2` - Web automation
- `webdriver-manager==4.0.1` - Auto-manage ChromeDriver
- `fuzzywuzzy==0.18.0` - Fuzzy string matching
- `python-Levenshtein==0.23.0` - Fast string comparison

### Step 2: Install Chrome/Chromium

Selenium requires Chrome browser and ChromeDriver:

**Windows:**
- Download Chrome: https://www.google.com/chrome/
- ChromeDriver auto-managed by `webdriver-manager`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
```

**Mac:**
```bash
brew install --cask google-chrome
```

---

## ⚙️ CONFIGURATION

### 🔍 Step 1: Find Competitor Websites

You need to identify the actual Saudi Arabia car rental websites for:

#### **Option A: Research Required**
1. **Hertz Saudi Arabia**
   - Search: "Hertz car rental Riyadh Saudi Arabia"
   - Find official booking page
   - Note the URL structure

2. **Budget Saudi Arabia**
   - Search: "Budget car rental Saudi Arabia"
   - Find booking/search page
   - Document the form structure

3. **Thrifty Saudi Arabia**
   - Search: "Thrifty car rental KSA"
   - Locate search functionality
   - Note CSS selectors for prices

#### **Option B: Alternative Competitors**
If Hertz/Budget/Thrifty don't operate in Saudi Arabia, find local competitors:
- Yelo (yelo.sa)
- Theeb (theebrent.com)
- Lumi (lumirentacar.com)
- Or major international brands operating locally

---

### 📝 Step 2: Configure `competitor_scraper_config.py`

Open `competitor_scraper_config.py` and update:

#### **2.1 Update Website URLs**

```python
COMPETITORS = {
    "Hertz": {
        "base_url": "https://www.hertz.com.sa",  # ← UPDATE THIS
        "search_page": "/reservations",          # ← AND THIS
        # ... rest of config
    }
}
```

#### **2.2 Inspect Websites & Update CSS Selectors**

For each competitor:

1. **Open their website** in Chrome
2. **Right-click on price** → "Inspect"
3. **Find CSS selector** (e.g., `.price-amount`, `#daily-rate`)
4. **Update in config:**

```python
"selectors": {
    "price": ".price-amount, .rate-per-day",      # ← Add actual selectors
    "category": ".car-class, .vehicle-type",      # ← Update
    "location": ".pickup-location, .branch-name", # ← Update
}
```

#### **2.3 Configure Location Mappings**

Map your Renty branches to competitor locations:

```python
LOCATION_MAPPING = {
    "Riyadh - King Khalid International Airport": {
        "Hertz": ["Riyadh Airport", "King Khalid Intl"],
        "Budget": ["Riyadh - RUH Airport"],
        "Thrifty": ["King Khalid Airport"]
    },
    # Add all your branches...
}
```

---

### 🧪 Step 3: Test the Scraper

#### **3.1 Test Intelligent Matcher**

```bash
python intelligent_matcher.py
```

Expected output:
```
✓ Riyadh - King Khalid International Airport → Hertz: Riyadh Airport (confidence: 100%)
✓ SUV Standard → Budget: Standard SUV (confidence: 95%)
```

#### **3.2 Test Web Scraper**

```bash
python competitor_web_scraper.py
```

This will attempt to scrape one competitor and show:
- ✅ Success: Price found
- ⚠️ Warning: Needs configuration
- ❌ Error: Check logs

---

## 🔧 CUSTOMIZATION

### Customize Scraping Logic for Each Competitor

Edit `competitor_web_scraper.py` methods:

#### **1. Build Search URL**

```python
def _build_search_url(self, config, location, category, pickup, return_date):
    # Example for a competitor with query parameters
    base_url = config['base_url']
    
    # Build URL with actual parameters
    url = f"{base_url}/search?pickup_location={location}"
    url += f"&pickup_date={pickup.strftime('%Y-%m-%d')}"
    url += f"&return_date={return_date.strftime('%Y-%m-%d')}"
    url += f"&category={category}"
    
    return url
```

#### **2. Extract Price**

```python
def _extract_price_hertz(self, driver):
    # Custom extraction logic for Hertz
    try:
        # Wait for price element
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".price-amount"))
        )
        
        # Get price
        price_element = driver.find_element(By.CSS_SELECTOR, ".price-amount")
        price_text = price_element.text
        
        # Parse (e.g., "SAR 340/day" → 340)
        return self._parse_price(price_text)
    except:
        return None
```

#### **3. Handle Forms/Dropdowns**

If competitor requires filling forms:

```python
def _fill_search_form(self, driver, location, category, dates):
    # Fill pickup location
    location_input = driver.find_element(By.ID, "pickup-location")
    location_input.send_keys(location)
    
    # Select dates
    pickup_input = driver.find_element(By.ID, "pickup-date")
    pickup_input.send_keys(dates['pickup'].strftime('%m/%d/%Y'))
    
    # Select category
    category_dropdown = driver.find_element(By.ID, "car-class")
    category_dropdown.click()
    # ... select option ...
    
    # Submit search
    search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    search_button.click()
```

---

## 🎯 DASHBOARD INTEGRATION

### Update Dashboard to Use Real-Time Scraping

The dashboard will automatically scrape when:
- Branch selection changes
- Date changes
- Category changes (implicitly when viewing prices)

**Loading Indicator:**
```
🔄 Fetching live competitor prices... (5-15 seconds)
```

**Success:**
```
✓ Hertz: 340 SAR (fetched 2 seconds ago)
✓ Budget: 335 SAR (fetched 3 seconds ago)
✓ Thrifty: 345 SAR (fetched 2 seconds ago)
```

**Fallback:**
```
⚠️ Hertz: 340 SAR (last known: Nov 26, 10:30 AM)
   Unable to fetch current prices. Showing cached data.
```

---

## 🛡️ LEGAL & ETHICAL CONSIDERATIONS

### ⚠️ IMPORTANT LEGAL NOTICE

Before scraping competitor websites:

1. **Check Terms of Service**
   - Read each competitor's ToS
   - Look for anti-scraping clauses
   - Respect robots.txt

2. **Get Permission (Recommended)**
   - Email competitors for permission
   - Explain use case (price comparison for customers)
   - Document approval

3. **Use Rate Limiting**
   - Don't overload their servers
   - Cache results (10 minutes default)
   - Scrape during off-peak hours

4. **Consider Alternatives**
   - Check for official APIs
   - Use authorized data providers
   - Manual price checking

### robots.txt Check

Before scraping, check:
```
https://www.competitor.com/robots.txt
```

If it says:
```
User-agent: *
Disallow: /search
```
→ DO NOT scrape `/search` page

---

## 🐛 TROUBLESHOOTING

### Issue 1: "Selenium not found"
**Solution:**
```bash
pip install selenium webdriver-manager
```

### Issue 2: "ChromeDriver not found"
**Solution:**
```bash
pip install webdriver-manager
# It will auto-download ChromeDriver
```

### Issue 3: "Price not extracted"
**Diagnosis:**
1. Check screenshot in `logs/screenshots/`
2. Verify CSS selectors are correct
3. Check if site uses JavaScript (needs wait)

**Solution:**
```python
# Add explicit wait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".price"))
)
```

### Issue 4: "CAPTCHA detected"
**Solutions:**
- Use `time.sleep()` to appear more human
- Rotate user agents
- Use residential proxies
- Consider CAPTCHA solving services (2captcha, Anti-Captcha)

### Issue 5: "Scraping too slow"
**Optimizations:**
- Enable parallel scraping: `parallel_scraping: True`
- Disable images: Already configured
- Use headless mode: Already enabled
- Increase cache TTL: `cache_duration: 1800` (30 min)

---

## 📊 MONITORING & LOGS

### View Logs

```bash
tail -f logs/competitor_scraper.log
```

### Check Cache

```bash
ls -lh data/cache/competitor_prices/
```

### Success Metrics

Monitor in logs:
- **Cache Hit Rate:** `% of requests served from cache`
- **Scraping Success Rate:** `% of successful scrapes`
- **Average Scraping Time:** `seconds per competitor`

---

## 🔄 MAINTENANCE

### Weekly Tasks

1. **Verify Scraping Still Works**
   - Competitors update websites regularly
   - CSS selectors may change
   - Test each competitor manually

2. **Update Category Mappings**
   - New vehicle categories may appear
   - Add to `CATEGORY_MAPPING`

3. **Clear Old Cache**
   ```bash
   find data/cache/competitor_prices/ -mtime +7 -delete
   ```

### Monthly Tasks

1. **Review robots.txt**
   - Check if scraping rules changed
   
2. **Update Competitor List**
   - New competitors in market
   - Defunct competitors to remove

3. **Performance Review**
   - Check logs for errors
   - Optimize slow scrapers
   - Update selectors if needed

---

## 📚 RESOURCES

### Selenium Documentation
- https://selenium-python.readthedocs.io/

### CSS Selectors Guide
- https://www.w3schools.com/cssref/css_selectors.asp

### Web Scraping Best Practices
- https://www.scrapingbee.com/blog/web-scraping-best-practices/

### Legal Guidelines
- https://benbernardblog.com/web-scraping-and-crawling-are-perfectly-legal-right/

---

## ✅ CHECKLIST

Before going live:

- [ ] Competitor websites identified
- [ ] Configuration file updated
- [ ] CSS selectors tested and working
- [ ] Location mappings configured
- [ ] Category mappings configured
- [ ] Intelligent matcher tested
- [ ] Web scraper tested for all competitors
- [ ] Legal review completed (ToS, robots.txt)
- [ ] Permission obtained (if required)
- [ ] Dashboard integration tested
- [ ] Error handling verified
- [ ] Caching working correctly
- [ ] Fallback strategy tested
- [ ] Logs reviewed
- [ ] Team trained on monitoring

---

## 🎉 NEXT STEPS

Once configured:

1. **Start Small**
   - Test with 1 competitor first
   - Verify accuracy of scraped prices
   - Check for any blocking/errors

2. **Expand Gradually**
   - Add second competitor
   - Then third
   - Monitor performance

3. **Monitor & Optimize**
   - Watch logs for issues
   - Adjust cache duration
   - Fine-tune selectors

4. **Maintain & Update**
   - Weekly checks
   - Update when competitors change sites
   - Add new competitors as needed

---

**Status:** Framework ready, needs site-specific configuration
**Estimated Setup Time:** 4-8 hours (depends on competitor website complexity)
**Maintenance:** 2-4 hours/month

**Ready to configure?** Start with Step 1: Find competitor websites!

