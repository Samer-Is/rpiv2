"""
Intelligent Category and Location Matcher
Uses fuzzy matching and keyword analysis to map Renty categories/locations to competitors
"""

from fuzzywuzzy import fuzz, process
from typing import List, Dict, Tuple, Optional
import re
from competitor_scraper_config import (
    LOCATION_MAPPING,
    CATEGORY_MAPPING,
    FUZZY_MATCH_SETTINGS
)


class IntelligentMatcher:
    """
    Intelligent matching system for categories and locations
    """
    
    def __init__(self):
        self.location_mapping = LOCATION_MAPPING
        self.category_mapping = CATEGORY_MAPPING
        self.location_threshold = FUZZY_MATCH_SETTINGS['location_threshold']
        self.category_threshold = FUZZY_MATCH_SETTINGS['category_threshold']
        
    # ========================================================================
    # LOCATION MATCHING
    # ========================================================================
    
    def match_location(
        self, 
        renty_location: str, 
        competitor_name: str, 
        available_locations: List[str]
    ) -> Optional[Tuple[str, int]]:
        """
        Match Renty location to competitor location
        
        Args:
            renty_location: Renty branch name (e.g., "Riyadh - King Khalid International Airport")
            competitor_name: Competitor name (e.g., "Hertz")
            available_locations: List of locations available on competitor site
            
        Returns:
            Tuple of (matched_location, confidence_score) or None
        """
        # Step 1: Try exact mapping first
        if renty_location in self.location_mapping:
            mapped_locations = self.location_mapping[renty_location].get(competitor_name, [])
            
            for mapped_loc in mapped_locations:
                for available_loc in available_locations:
                    if self._normalize_text(mapped_loc) == self._normalize_text(available_loc):
                        return (available_loc, 100)
            
            # Step 2: Try fuzzy matching with mapped locations
            for mapped_loc in mapped_locations:
                best_match = process.extractOne(
                    mapped_loc, 
                    available_locations, 
                    scorer=fuzz.token_sort_ratio
                )
                if best_match and best_match[1] >= self.location_threshold:
                    return (best_match[0], best_match[1])
        
        # Step 3: Try fuzzy matching with original Renty location
        best_match = process.extractOne(
            renty_location, 
            available_locations, 
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= self.location_threshold:
            return (best_match[0], best_match[1])
        
        # Step 4: Try keyword-based matching (city name, airport)
        location_keywords = self._extract_location_keywords(renty_location)
        for available_loc in available_locations:
            available_keywords = self._extract_location_keywords(available_loc)
            
            # Check if key identifiers match
            if location_keywords['city'] and available_keywords['city']:
                if location_keywords['city'] in available_keywords['city'] or \
                   available_keywords['city'] in location_keywords['city']:
                    
                    # Bonus points if both are airports
                    if location_keywords['is_airport'] == available_keywords['is_airport']:
                        confidence = 85
                    else:
                        confidence = 75
                    
                    return (available_loc, confidence)
        
        return None
    
    def _extract_location_keywords(self, location: str) -> Dict:
        """Extract key information from location string"""
        location_lower = location.lower()
        
        # Extract city
        cities = ['riyadh', 'jeddah', 'dammam', 'mecca', 'makkah', 'medina', 'madinah']
        city = None
        for c in cities:
            if c in location_lower:
                city = c
                break
        
        # Check if airport
        airport_keywords = ['airport', 'international', 'intl']
        is_airport = any(keyword in location_lower for keyword in airport_keywords)
        
        return {
            'city': city,
            'is_airport': is_airport,
            'original': location
        }
    
    # ========================================================================
    # CATEGORY MATCHING
    # ========================================================================
    
    def match_category(
        self, 
        renty_category: str, 
        competitor_name: str, 
        available_categories: List[str]
    ) -> Optional[Tuple[str, int]]:
        """
        Match Renty category to competitor category
        
        Args:
            renty_category: Renty category (e.g., "SUV Standard")
            competitor_name: Competitor name (e.g., "Hertz")
            available_categories: List of categories available on competitor site
            
        Returns:
            Tuple of (matched_category, confidence_score) or None
        """
        # Step 1: Try exact mapping first
        if renty_category in self.category_mapping:
            mapped_categories = self.category_mapping[renty_category].get(competitor_name, [])
            
            for mapped_cat in mapped_categories:
                for available_cat in available_categories:
                    if self._normalize_text(mapped_cat) == self._normalize_text(available_cat):
                        return (available_cat, 100)
            
            # Step 2: Try fuzzy matching with mapped categories
            for mapped_cat in mapped_categories:
                best_match = process.extractOne(
                    mapped_cat, 
                    available_categories, 
                    scorer=fuzz.token_sort_ratio
                )
                if best_match and best_match[1] >= self.category_threshold:
                    return (best_match[0], best_match[1])
            
            # Step 3: Try keyword matching
            category_keywords = self.category_mapping[renty_category]['keywords']
            best_score = 0
            best_category = None
            
            for available_cat in available_categories:
                available_lower = available_cat.lower()
                
                # Count matching keywords
                matching_keywords = sum(
                    1 for keyword in category_keywords 
                    if keyword in available_lower
                )
                
                if matching_keywords > 0:
                    score = (matching_keywords / len(category_keywords)) * 100
                    if score > best_score:
                        best_score = score
                        best_category = available_cat
            
            if best_category and best_score >= (self.category_threshold - 10):
                return (best_category, int(best_score))
        
        # Step 4: Try direct fuzzy matching as last resort
        best_match = process.extractOne(
            renty_category, 
            available_categories, 
            scorer=fuzz.token_sort_ratio
        )
        
        if best_match and best_match[1] >= self.category_threshold:
            return (best_match[0], best_match[1])
        
        return None
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove special characters, extra spaces, convert to lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = ' '.join(text.split())
        return text
    
    def get_category_keywords(self, renty_category: str) -> List[str]:
        """Get keyword list for a Renty category"""
        if renty_category in self.category_mapping:
            return self.category_mapping[renty_category]['keywords']
        return []
    
    def get_location_alternatives(self, renty_location: str, competitor_name: str) -> List[str]:
        """Get alternative location names for searching"""
        if renty_location in self.location_mapping:
            return self.location_mapping[renty_location].get(competitor_name, [])
        return []
    
    def add_location_mapping(
        self, 
        renty_location: str, 
        competitor_name: str, 
        competitor_location: str
    ):
        """
        Add a new location mapping (learning from user corrections)
        """
        if renty_location not in self.location_mapping:
            self.location_mapping[renty_location] = {}
        
        if competitor_name not in self.location_mapping[renty_location]:
            self.location_mapping[renty_location][competitor_name] = []
        
        if competitor_location not in self.location_mapping[renty_location][competitor_name]:
            self.location_mapping[renty_location][competitor_name].append(competitor_location)
            print(f"✓ Learned new mapping: {renty_location} → {competitor_name}: {competitor_location}")
    
    def add_category_mapping(
        self, 
        renty_category: str, 
        competitor_name: str, 
        competitor_category: str
    ):
        """
        Add a new category mapping (learning from user corrections)
        """
        if renty_category not in self.category_mapping:
            self.category_mapping[renty_category] = {
                "keywords": [],
                "examples": []
            }
        
        if competitor_name not in self.category_mapping[renty_category]:
            self.category_mapping[renty_category][competitor_name] = []
        
        if competitor_category not in self.category_mapping[renty_category][competitor_name]:
            self.category_mapping[renty_category][competitor_name].append(competitor_category)
            print(f"✓ Learned new mapping: {renty_category} → {competitor_name}: {competitor_category}")


# ============================================================================
# TESTING & VALIDATION
# ============================================================================

def test_matcher():
    """Test the intelligent matcher"""
    matcher = IntelligentMatcher()
    
    print("="*80)
    print("INTELLIGENT MATCHER - TEST RESULTS")
    print("="*80)
    
    # Test location matching
    print("\n1. LOCATION MATCHING TESTS")
    print("-"*80)
    
    test_locations = [
        ("Riyadh - King Khalid International Airport", "Hertz", 
         ["Riyadh Airport", "Jeddah City", "Dammam Airport"]),
        ("Jeddah - City", "Budget", 
         ["Jeddah City Center", "Riyadh Downtown", "Mecca City"]),
    ]
    
    for renty_loc, competitor, available in test_locations:
        result = matcher.match_location(renty_loc, competitor, available)
        if result:
            print(f"✓ {renty_loc} → {competitor}: {result[0]} (confidence: {result[1]}%)")
        else:
            print(f"✗ {renty_loc} → {competitor}: No match found")
    
    # Test category matching
    print("\n2. CATEGORY MATCHING TESTS")
    print("-"*80)
    
    test_categories = [
        ("Economy", "Hertz", ["Economy", "Compact", "Midsize", "SUV"]),
        ("SUV Standard", "Budget", ["Compact SUV", "Standard SUV", "Full-size SUV"]),
        ("Luxury Sedan", "Thrifty", ["Economy", "Standard", "Luxury", "Premium"]),
    ]
    
    for renty_cat, competitor, available in test_categories:
        result = matcher.match_category(renty_cat, competitor, available)
        if result:
            print(f"✓ {renty_cat} → {competitor}: {result[0]} (confidence: {result[1]}%)")
        else:
            print(f"✗ {renty_cat} → {competitor}: No match found")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_matcher()

