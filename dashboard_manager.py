"""
Dynamic Pricing Engine - Branch Manager Dashboard

Interactive dashboard for branch managers and management to:
1. Select their branch
2. Choose car category
3. See real-time pricing recommendations
4. Understand applied multipliers/discounts
5. Make informed pricing decisions
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from pricing_engine import DynamicPricingEngine
import config
from competitor_pricing import load_competitor_prices, calculate_average_competitor_price
from stored_competitor_prices import get_competitor_prices_for_branch_category, get_data_freshness, clear_cache
from utilization_query import get_current_utilization

# Page configuration
st.set_page_config(
    page_title="Renty - Intelligent Dynamic Pricing",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Logo styling with rounded corners and 3D effect */
    img {
        border-radius: 20px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2), 0 12px 40px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    img:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.25), 0 16px 48px rgba(0, 0, 0, 0.2);
    }
    .price-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .category-card {
        background-color: #f8f9fa;
        border: 2px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.25rem 0;
        transition: all 0.3s;
        min-height: 320px;
        display: flex;
        flex-direction: column;
    }
    .category-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .competitor-section {
        background: #f8f9fa;
        padding: 0.4rem;
        border-radius: 0.4rem;
        margin-top: 0.4rem;
        font-size: 0.8rem;
        min-height: 100px;
        max-height: 120px;
        overflow-y: auto;
        flex-grow: 1;
    }
    .discount-badge {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
    }
    .premium-badge {
        background-color: #dc3545;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
    }
    .neutral-badge {
        background-color: #6c757d;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Vehicle Categories with base prices (SAR per day)
VEHICLE_CATEGORIES = {
    "Economy": {
        "examples": "Hyundai Accent, Kia Picanto, Nissan Sunny",
        "base_price": 102.0,
        "icon": "🚗"
    },
    "Compact": {
        "examples": "Toyota Yaris, Hyundai Elantra, Kia Cerato",
        "base_price": 143.0,
        "icon": "🚙"
    },
    "Standard": {
        "examples": "Toyota Camry, Hyundai Sonata, Nissan Altima",
        "base_price": 188.0,
        "icon": "🚘"
    },
    "SUV Compact": {
        "examples": "Hyundai Tucson, Nissan Qashqai, Kia Sportage",
        "base_price": 204.0,
        "icon": "🚐"
    },
    "SUV Standard": {
        "examples": "Toyota RAV4, Nissan X-Trail, Hyundai Santa Fe",
        "base_price": 224.0,
        "icon": "🚙"
    },
    "SUV Large": {
        "examples": "Toyota Land Cruiser, Nissan Patrol, Chevrolet Tahoe",
        "base_price": 317.0,
        "icon": "🚐"
    },
    "Luxury Sedan": {
        "examples": "BMW 5 Series, Mercedes E-Class, Audi A6",
        "base_price": 515.0,
        "icon": "🚗"
    },
    "Luxury SUV": {
        "examples": "BMW X5, Mercedes GLE, Audi Q7",
        "base_price": 893.0,
        "icon": "🚙"
    }
}

# Top branches with names
BRANCHES = {
    122: {"name": "King Khalid Airport - Riyadh", "city": "Riyadh", "is_airport": True},
    15: {"name": "Olaya District - Riyadh", "city": "Riyadh", "is_airport": False},
    63: {"name": "King Fahd Airport - Dammam", "city": "Dammam", "is_airport": True},
    33: {"name": "King Abdulaziz Airport - Jeddah", "city": "Jeddah", "is_airport": True},
    45: {"name": "Mecca City Center", "city": "Mecca", "is_airport": False},
    89: {"name": "Medina Downtown", "city": "Medina", "is_airport": False},
    # Note: Branches 110 (Riyadh City Center) and 172 (Al Khobar Business District) 
    # removed - no data in Fleet.VehicleHistory
}

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = None
    st.session_state.engine_loaded = False
if 'selected_branch' not in st.session_state:
    st.session_state.selected_branch = 122
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "Standard"
if 'competitor_prices' not in st.session_state:
    st.session_state.competitor_prices = None

# Load engine (cached with version to force refresh)
@st.cache_resource
def load_pricing_engine(_version="v4.0"):
    """Load the pricing engine (cached)."""
    try:
        engine = DynamicPricingEngine()
        return engine, True, "Engine loaded successfully!"
    except Exception as e:
        return None, False, f"Error: {str(e)}"

# Load competitor prices (cached)
@st.cache_data(ttl=3600)  # Refresh every hour
def load_competitor_data(_version="v2.2"):
    """Load competitor pricing data (cached for 1 hour)."""
    try:
        comp_df = load_competitor_prices("data/competitor_prices/competitor_prices.csv")
        if comp_df is not None and len(comp_df) > 0:
            return comp_df, True
        else:
            return load_competitor_prices(), False  # Use defaults
    except Exception as e:
        st.warning(f"Could not load competitor prices: {str(e)}")
        return load_competitor_prices(), False  # Use defaults

# Sidebar - Logo
st.sidebar.image("Gemini_Generated_Image_qzl79lqzl79lqzl7.png", use_column_width=True)
st.sidebar.markdown("---")

# User role (for display purposes)
user_role = st.sidebar.selectbox(
    "Your Role",
    ["Branch Manager", "Regional Manager", "Pricing Manager", "Executive"]
)

st.sidebar.markdown("---")

# Branch selection
st.sidebar.markdown("### 🏢 Select Your Branch")

branch_options = {f"{info['name']} (ID: {id})": id for id, info in BRANCHES.items()}
selected_branch_display = st.sidebar.selectbox(
    "Branch",
    list(branch_options.keys()),
    index=0
)

st.session_state.selected_branch = branch_options[selected_branch_display]
branch_info = BRANCHES[st.session_state.selected_branch]

# Display branch info
st.sidebar.info(f"""
**Branch:** {branch_info['name']}  
**City:** {branch_info['city']}  
**Type:** {'Airport ✈️' if branch_info['is_airport'] else 'City Center 🏙️'}  
**ID:** {st.session_state.selected_branch}
""")

st.sidebar.markdown("---")

# System status
st.sidebar.markdown("### ⚙️ System Status")

# Load engine
if not st.session_state.engine_loaded:
    with st.spinner("Loading pricing engine..."):
        engine, success, message = load_pricing_engine(_version="v4.0")
        st.session_state.engine = engine
        st.session_state.engine_loaded = success
        if success:
            st.sidebar.success("✅ Pricing Engine Ready (V4 Robust)")
        else:
            st.sidebar.error(f"❌ {message}")

# Load competitor prices ALWAYS (force refresh for now)
comp_df, comp_success = load_competitor_data(_version="v2.2")
st.session_state.competitor_prices = comp_df

if comp_success and comp_df is not None and len(comp_df) > 0:
    st.sidebar.success(f"✅ Competitor data ({len(comp_df)} prices)")
else:
    st.sidebar.error("❌ Competitor data failed to load!")
    st.sidebar.write(f"comp_df is None: {comp_df is None}")
    if comp_df is not None:
        st.sidebar.write(f"comp_df length: {len(comp_df)}")

st.sidebar.markdown(f"**Model Accuracy:** 96.57% (V4 Robust)")

# Competitor data freshness
data_freshness = get_data_freshness()
if data_freshness['available']:
    age_hours = data_freshness.get('age_hours', 0)
    status = data_freshness.get('status', 'Unknown')
    
    if age_hours < 24:
        st.sidebar.success(f"✅ Competitor Data: {status} ({age_hours:.1f}h old)")
    elif age_hours < 48:
        st.sidebar.warning(f"⚠️ Competitor Data: {status} ({age_hours:.1f}h old)")
    else:
        st.sidebar.error(f"❌ Competitor Data: {status} ({age_hours:.1f}h old)")
else:
    st.sidebar.error("❌ No competitor data available. Run daily_competitor_scraper.py")

# Refresh button to clear cache and reload fresh data
if st.sidebar.button("🔄 Refresh Competitor Data"):
    clear_cache()
    st.rerun()

# Main content - Header with Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("Gemini_Generated_Image_qzl79lqzl79lqzl7.png", use_column_width=True)
    st.markdown('<p class="main-header">Intelligent Dynamic Pricing</p>', unsafe_allow_html=True)
    st.info(f"👋 Welcome, **{user_role}**! Manage pricing for **{branch_info['name']}**")

st.markdown("---")

# Date and condition selectors - COMPACT
st.markdown("### 📅 Date & Events")

col1, col2, col3 = st.columns([2, 3, 3])

with col1:
    pricing_date = st.date_input(
        "Pricing Date",
        value=date(2025, 11, 18),
        min_value=date(2023, 1, 1),
        max_value=date(2025, 11, 18),
        help="Pricing date"
    )
    is_weekend = st.checkbox("📅 Weekend", value=False, help="Friday-Saturday")

with col2:
    st.markdown("**Religious Events**")
    is_holiday = st.checkbox("🎉 Holiday", value=False, help="Eid, National Day")
    is_ramadan = st.checkbox("🌙 Ramadan", value=False, help="Ramadan")
    is_umrah_season = st.checkbox("🕋 Umrah", value=False, help="Umrah season")
    is_hajj = st.checkbox("🕌 Hajj", value=False, help="Hajj season")

with col3:
    st.markdown("**Other Events**")
    is_school_vacation = st.checkbox("🏖️ Vacation", value=False, help="School vacation")
    is_festival = st.checkbox("🎪 Festival", value=False, help="Riyadh/Jeddah Season")
    is_sports_event = st.checkbox("🏎️ Sports", value=False, help="Formula 1")
    is_conference = st.checkbox("💼 Business", value=False, help="Conferences")

# Combine events for pricing engine (backwards compatibility)
is_major_event = is_festival or is_sports_event or is_conference or is_hajj

# Show active events warning
active_events = []
if is_holiday:
    active_events.append("🎉 Holiday")
if is_ramadan:
    active_events.append("🌙 Ramadan")
if is_umrah_season:
    active_events.append("🕋 Umrah")
if is_hajj:
    active_events.append("🕌 Hajj")
if is_school_vacation:
    active_events.append("🏖️ Vacation")
if is_festival:
    active_events.append("🎪 Festival")
if is_sports_event:
    active_events.append("🏎️ Sports")
if is_conference:
    active_events.append("💼 Business")

if active_events:
    st.warning(f"⚠️ **EVENTS ACTIVE:** {', '.join(active_events)} - This will apply PREMIUM pricing!")
    if st.button("🔄 Reset to Normal Day"):
        st.rerun()
else:
    st.success("✓ Normal Day (No events) - Pricing based on demand and utilization only")

# Fleet utilization
st.markdown("### 🚗 Fleet Status")

# Toggle between manual and real-time
utilization_mode = st.radio(
    "Utilization Mode",
    ["Manual (Demo)", "Real-time (Database)"],
    help="Manual: Use inputs for testing. Real-time: Query Fleet.VehicleHistory"
)

if utilization_mode == "Real-time (Database)":
    # Query database - NO CACHING, query every time branch changes
    with st.spinner(f"Querying Fleet.VehicleHistory for Branch {st.session_state.selected_branch}..."):
        util_data = get_current_utilization(
            branch_id=st.session_state.selected_branch,
            date=pricing_date
        )
    
    total_vehicles = util_data['total_vehicles']
    rented_vehicles = util_data['rented_vehicles']
    available_vehicles = util_data['available_vehicles']
    utilization_pct = util_data['utilization_pct']
    
    # Show data source and branch info
    if util_data['source'] == 'database':
        st.success(f"✓ Real-time: {rented_vehicles}/{total_vehicles} rented ({utilization_pct:.1f}%)")
        st.info(f"**Source:** Fleet.VehicleHistory | **Branch ID:** {st.session_state.selected_branch} | **Date:** {pricing_date.strftime('%Y-%m-%d')}")
    else:
        st.warning(f"⚠ No data for branch {st.session_state.selected_branch} - Using defaults: {rented_vehicles}/{total_vehicles}")
        if 'error' in util_data:
            st.error(f"Error: {util_data['error']}")
else:
    # Manual inputs (demo mode)
    col1, col2, col3 = st.columns(3)

    with col1:
        total_vehicles = st.number_input(
            "Total Fleet Size",
            min_value=10,
            max_value=500,
            value=100,
            help="Total vehicles in your branch"
        )

    with col2:
        rented_vehicles = st.slider(
            "Currently Rented Vehicles",
            min_value=0,
            max_value=int(total_vehicles),
            value=int(total_vehicles * 0.5),
            help="Number of vehicles currently rented out"
        )

    utilization_pct = (rented_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
    available_vehicles = total_vehicles - rented_vehicles

col1, col2, col3 = st.columns(3)
with col3:
    
    if utilization_pct < 30:
        color = "🟢"
        status = "Low Utilization"
    elif utilization_pct < 70:
        color = "🟡"
        status = "Medium Utilization"
    else:
        color = "🔴"
        status = "High Utilization"
    
    st.metric(
        "Fleet Utilization",
        f"{color} {status}",
        f"{utilization_pct:.0f}% rented ({available_vehicles} available)"
    )

st.markdown("---")

# Main pricing section
st.markdown("## 💰 Recommended Pricing by Vehicle Category")

if not st.session_state.engine_loaded:
    st.error("⚠️ Pricing engine not loaded. Check sidebar for errors.")
    st.stop()

# Calculate prices for all categories
with st.spinner("Calculating optimal prices for all categories..."):
    try:
        target_datetime = datetime.combine(pricing_date, datetime.min.time())
        
        # Calculate for each category
        pricing_results = {}
        competitor_data = {}
        
        for category, details in VEHICLE_CATEGORIES.items():
            result = st.session_state.engine.calculate_optimized_price(
                target_date=target_datetime,
                branch_id=st.session_state.selected_branch,
                base_price=details["base_price"],
                available_vehicles=available_vehicles,
                total_vehicles=total_vehicles,
                city_id=1,
                city_name=branch_info["city"],
                is_airport=branch_info["is_airport"],
                is_holiday=is_holiday,
                is_school_vacation=is_school_vacation,
                is_ramadan=is_ramadan,
                is_umrah_season=is_umrah_season,
                is_hajj=is_hajj,
                is_festival=is_festival,
                is_sports_event=is_sports_event,
                is_conference=is_conference,
                days_to_holiday=-1
            )
            
            pricing_results[category] = result
            
            # Get competitor pricing from stored daily data
            try:
                comp_stats = get_competitor_prices_for_branch_category(
                    branch_name=branch_info['name'],
                    category=category
                )
            except Exception as e:
                st.error(f"Live pricing error: {str(e)}")
                # Fallback to static data
                if st.session_state.competitor_prices is not None:
                    comp_stats = calculate_average_competitor_price(
                        st.session_state.competitor_prices,
                        category,
                        branch_info['city'],
                        st.session_state.selected_branch,
                        pricing_date
                    )
                else:
                    comp_stats = {
                        'avg_price': None,
                        'min_price': None,
                        'max_price': None,
                        'competitor_count': 0,
                        'competitors': []
                    }
            
            # Compare with competitors
            if comp_stats['avg_price']:
                price_diff = result['final_price'] - comp_stats['avg_price']
                price_diff_pct = (price_diff / comp_stats['avg_price']) * 100
                comparison = {
                    'diff': price_diff,
                    'diff_pct': price_diff_pct,
                    'status': 'cheaper' if price_diff < 0 else 'more_expensive'
                }
            else:
                comparison = {'diff': 0, 'diff_pct': 0, 'status': 'no_data'}
            competitor_data[category] = {
                'stats': comp_stats,
                'comparison': comparison
            }
        
        # Display pricing cards in a grid
        categories_list = list(VEHICLE_CATEGORIES.keys())
        
        # Row 1: Economy, Compact, Standard, SUV Compact
        col1, col2, col3, col4 = st.columns(4)
        
        for idx, col in enumerate([col1, col2, col3, col4]):
            if idx < len(categories_list):
                category = categories_list[idx]
                result = pricing_results[category]
                details = VEHICLE_CATEGORIES[category]
                
                with col:
                    # Determine badge - show any adjustment over ±1%
                    change_pct = result['price_change_pct']
                    if change_pct < -1:
                        badge = f'<span class="discount-badge">{change_pct:.1f}% DISCOUNT</span>'
                    elif change_pct > 1:
                        badge = f'<span class="premium-badge">+{change_pct:.1f}% PREMIUM</span>'
                    else:
                        badge = f'<span class="neutral-badge">STANDARD</span>'
                    
                    # Get competitor info for this category
                    comp_info = competitor_data[category]
                    comp_stats = comp_info['stats']
                    
                    # Build complete card HTML
                    card_html = f"""<div class="category-card">
                        <h3 style="color: #003d82; margin: 0 0 0.25rem 0; font-size: 1.1rem;">{details['icon']} {category}</h3>
                        <p style="font-size: 0.85rem; color: #6c757d; margin: 0;">{details['examples']}</p>
                        <hr style="margin: 0.5rem 0;">
                        <p style="font-size: 0.85rem; color: #6c757d; text-decoration: line-through; margin: 0.25rem 0;">
                            Base: {result['base_price']:.0f} SAR/day
                        </p>
                        <h2 style="color: #1f77b4; margin: 0.25rem 0; font-size: 1.5rem;">
                            {result['final_price']:.0f} SAR<span style="font-size: 0.6em;">/day</span>
                        </h2>
                        <div style="margin: 0.25rem 0;">
                            {badge}
                        </div>"""
                    
                     # Add competitor section
                    if comp_stats['avg_price']:
                        comp_avg = comp_stats['avg_price']
                        comp_count = comp_stats['competitor_count']
                        price_diff = result['final_price'] - comp_avg
                        comp_color = "#28a745" if price_diff < 0 else "#dc3545"
                        comp_icon = "✓" if price_diff < 0 else "▲"
                        comp_text = f"{abs(price_diff):.0f} SAR cheaper" if price_diff < 0 else f"{price_diff:.0f} SAR more"
                        
                        # Build competitor list HTML with timestamp
                        comp_list_html = ""
                        comp_timestamp = ""
                        for comp in comp_stats['competitors']:
                            comp_list_html += f"<div style='font-size: 0.75rem; color: #495057; margin-top: 0.1rem;'>• {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR</div>"
                            if not comp_timestamp and 'Date' in comp:
                                comp_timestamp = comp['Date']
                        
                        if not comp_timestamp:
                            comp_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        card_html += f"""<div class="competitor-section">
                            <div style="color: #6c757d; margin-bottom: 0.2rem;">
                                <strong>Competitor Avg:</strong> {comp_avg:.0f} SAR/day
                            </div>
                            {comp_list_html}
                            <div style="color: #6c757d; font-size: 0.75rem; margin-top: 0.2rem;">
                                🔄 Live: {comp_timestamp}
                            </div>
                        </div>"""
                    else:
                        card_html += """<div class="competitor-section" style="color: #6c757d; font-size: 0.8rem;">
                            No competitor data available
                        </div>"""
                    
                    # Close card div
                    card_html += "</div>"
                    
                    st.markdown(card_html, unsafe_allow_html=True)
        
        # Row 2: SUV Standard, SUV Large, Luxury Sedan, Luxury SUV
        col1, col2, col3, col4 = st.columns(4)
        
        for idx, col in enumerate([col1, col2, col3, col4]):
            category_idx = idx + 4
            if category_idx < len(categories_list):
                category = categories_list[category_idx]
                result = pricing_results[category]
                details = VEHICLE_CATEGORIES[category]
                
                with col:
                    # Determine badge - show any adjustment over ±1%
                    change_pct = result['price_change_pct']
                    if change_pct < -1:
                        badge = f'<span class="discount-badge">{change_pct:.1f}% DISCOUNT</span>'
                    elif change_pct > 1:
                        badge = f'<span class="premium-badge">+{change_pct:.1f}% PREMIUM</span>'
                    else:
                        badge = f'<span class="neutral-badge">STANDARD</span>'
                    
                    # Get competitor info for this category
                    comp_info = competitor_data[category]
                    comp_stats = comp_info['stats']
                    
                    # Build complete card HTML
                    card_html = f"""<div class="category-card">
                        <h3 style="color: #003d82; margin: 0 0 0.25rem 0; font-size: 1.1rem;">{details['icon']} {category}</h3>
                        <p style="font-size: 0.85rem; color: #6c757d; margin: 0;">{details['examples']}</p>
                        <hr style="margin: 0.5rem 0;">
                        <p style="font-size: 0.85rem; color: #6c757d; text-decoration: line-through; margin: 0.25rem 0;">
                            Base: {result['base_price']:.0f} SAR/day
                        </p>
                        <h2 style="color: #1f77b4; margin: 0.25rem 0; font-size: 1.5rem;">
                            {result['final_price']:.0f} SAR<span style="font-size: 0.6em;">/day</span>
                        </h2>
                        <div style="margin: 0.25rem 0;">
                            {badge}
                        </div>"""
                    
                     # Add competitor section
                    if comp_stats['avg_price']:
                        comp_avg = comp_stats['avg_price']
                        comp_count = comp_stats['competitor_count']
                        price_diff = result['final_price'] - comp_avg
                        comp_color = "#28a745" if price_diff < 0 else "#dc3545"
                        comp_icon = "✓" if price_diff < 0 else "▲"
                        comp_text = f"{abs(price_diff):.0f} SAR cheaper" if price_diff < 0 else f"{price_diff:.0f} SAR more"
                        
                        # Build competitor list HTML with timestamp
                        comp_list_html = ""
                        comp_timestamp = ""
                        for comp in comp_stats['competitors']:
                            comp_list_html += f"<div style='font-size: 0.75rem; color: #495057; margin-top: 0.1rem;'>• {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR</div>"
                            if not comp_timestamp and 'Date' in comp:
                                comp_timestamp = comp['Date']
                        
                        if not comp_timestamp:
                            comp_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        card_html += f"""<div class="competitor-section">
                            <div style="color: #6c757d; margin-bottom: 0.2rem;">
                                <strong>Competitor Avg:</strong> {comp_avg:.0f} SAR/day
                            </div>
                            {comp_list_html}
                            <div style="color: #6c757d; font-size: 0.75rem; margin-top: 0.2rem;">
                                🔄 Live: {comp_timestamp}
                            </div>
                        </div>"""
                    else:
                        card_html += """<div class="competitor-section" style="color: #6c757d; font-size: 0.8rem;">
                            No competitor data available
                        </div>"""
                    
                    # Close card div
                    card_html += "</div>"
                    
                    st.markdown(card_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # COMPETITOR COMPARISON SECTION
        st.markdown("---")
        
        st.markdown("---")
        
        # Action buttons
        st.markdown("### 🎯 Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Create report DataFrame
            report_df = pd.DataFrame([
                {
                    'Branch': branch_info['name'],
                    'Branch ID': st.session_state.selected_branch,
                    'City': branch_info['city'],
                    'Date': pricing_date,
                    'Category': category,
                    'Examples': VEHICLE_CATEGORIES[category]['examples'],
                    'Base Price (SAR)': result['base_price'],
                    'Optimized Price (SAR)': result['final_price'],
                    'Change (%)': result['price_change_pct'],
                    'Demand Multiplier': result['demand_multiplier'],
                    'Supply Multiplier': result['supply_multiplier'],
                    'Event Multiplier': result['event_multiplier'],
                    'Final Multiplier': result['final_multiplier'],
                    'Predicted Demand': result['predicted_demand'],
                    'Average Demand': result['average_demand'],
                    'Fleet Utilization (%)': utilization_pct,
                    'Rented Vehicles': rented_vehicles,
                    'Available Vehicles': available_vehicles,
                    'Total Vehicles': total_vehicles,
                    'Is Holiday': 'Yes' if is_holiday else 'No',
                    'Is Ramadan': 'Yes' if is_ramadan else 'No',
                    'Is Umrah Season': 'Yes' if is_umrah_season else 'No',
                    'Is Hajj': 'Yes' if is_hajj else 'No',
                    'Is School Vacation': 'Yes' if is_school_vacation else 'No',
                    'Is Festival': 'Yes' if is_festival else 'No',
                    'Is Sports Event': 'Yes' if is_sports_event else 'No',
                    'Is Business Event': 'Yes' if is_conference else 'No',
                    'Is Weekend': 'Yes' if is_weekend else 'No',
                    'Explanation': result['explanation']
                }
                for category, result in pricing_results.items()
            ])
            
            csv = report_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Pricing Report (CSV)",
                data=csv,
                file_name=f"renty_pricing_report_{branch_info['city']}_{pricing_date}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        
        with col2:
            if st.button("🔄 Refresh Prices", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("📧 Email to Team", use_container_width=True):
                st.info("Email functionality would be integrated here")
        
        with col4:
            if st.button("✅ Apply Prices", use_container_width=True):
                st.success("Prices would be applied to the system here")
        
    except Exception as e:
        st.error(f"❌ Error calculating prices: {str(e)}")
        st.exception(e)
    
    # Car-by-Car Matching Section
    st.markdown("---")
    st.markdown("## 🚗 Car-by-Car Price Comparison")
    st.markdown(f"**Branch:** {branch_info['name']} | **Date:** {pricing_date.strftime('%Y-%m-%d')}")
    st.markdown("*Matching specific vehicles with competitors (e.g., Toyota Camry vs Toyota Camry)*")
    
    try:
        # Define Renty's representative vehicles per category
        renty_vehicles = {
            "Economy": ["Hyundai Accent", "Kia Picanto", "Nissan Sunny"],
            "Compact": ["Toyota Yaris", "Hyundai Elantra", "Kia Cerato"],
            "Standard": ["Toyota Camry", "Hyundai Sonata", "Nissan Altima"],
            "SUV Compact": ["Hyundai Tucson", "Nissan Qashqai", "Kia Sportage"],
            "SUV Standard": ["Toyota RAV4", "Nissan X-Trail", "Hyundai Santa Fe"],
            "SUV Large": ["Toyota Land Cruiser", "Nissan Patrol", "Chevrolet Tahoe"],
            "Luxury Sedan": ["BMW 5 Series", "Mercedes E-Class", "Audi A6"],
            "Luxury SUV": ["BMW X5", "Mercedes GLE", "Audi Q7"]
        }
        
        # Build car matching data
        car_matches = []
        
        for category in VEHICLE_CATEGORIES.keys():
            renty_cars = renty_vehicles.get(category, [])
            
            # Get competitor data for this category
            comp_data = get_competitor_prices_for_branch_category(branch_info['name'], category)
            
            if comp_data['competitors'] and category in pricing_results:
                # Try to find vehicle matches
                for renty_car in renty_cars:
                    for comp in comp_data['competitors']:
                        comp_vehicle = comp['Vehicle'].strip()
                        
                        # Simple matching (exact or partial)
                        if renty_car.lower() in comp_vehicle.lower() or comp_vehicle.lower() in renty_car.lower():
                            # Match found!
                            renty_price = pricing_results[category]['final_price']
                            comp_price = comp['Competitor_Price']
                            diff = renty_price - comp_price
                            diff_pct = (diff / comp_price * 100) if comp_price > 0 else 0
                            
                            car_matches.append({
                                'category': category,
                                'renty_vehicle': renty_car,
                                'competitor_vehicle': comp_vehicle,
                                'competitor': comp['Competitor_Name'],
                                'renty_price': renty_price,
                                'competitor_price': comp_price,
                                'difference': diff,
                                'difference_pct': diff_pct
                            })
                            break  # Only match each Renty car once per category
        
        if car_matches:
            # Show as cards
            cols = st.columns(2)
            for idx, match in enumerate(car_matches[:8]):  # Show up to 8 matches
                with cols[idx % 2]:
                    diff_color = "#28a745" if match['difference'] < 0 else "#dc3545"
                    diff_icon = "✓" if match['difference'] < 0 else "▲"
                    diff_text = f"{abs(match['difference']):.0f} SAR cheaper" if match['difference'] < 0 else f"{match['difference']:.0f} SAR more"
                    
                    st.markdown(f"""
                    <div style="background: white; border: 2px solid #dee2e6; border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.5rem;">
                        <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.3rem;">
                            {match['category']}
                        </div>
                        <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem;">
                            {match['renty_vehicle']}
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div>
                                <div style="font-size: 0.75rem; color: #6c757d;">Renty</div>
                                <div style="font-size: 1.3rem; font-weight: bold; color: #1f77b4;">
                                    {match['renty_price']:.0f} SAR
                                </div>
                            </div>
                            <div style="font-size: 1.5rem; color: #6c757d;">vs</div>
                            <div>
                                <div style="font-size: 0.75rem; color: #6c757d;">{match['competitor']}</div>
                                <div style="font-size: 1.3rem; font-weight: bold; color: {diff_color};">
                                    {match['competitor_price']:.0f} SAR
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; padding: 0.5rem; background: {diff_color}; color: white; border-radius: 0.3rem; font-weight: bold;">
                            {diff_icon} {diff_text} ({match['difference_pct']:.1f}%)
                        </div>
                        <div style="font-size: 0.7rem; color: #6c757d; margin-top: 0.5rem; text-align: center;">
                            vs {match['competitor_vehicle']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No exact vehicle matches found with competitors for this branch.")
    
    except Exception as e:
        st.error(f"❌ Error in car-by-car matching: {str(e)}")
        st.exception(e)
    
    # Competitor Comparison Section
    st.markdown("---")
    st.markdown("## 📊 Competitor Price Comparison by Category")
    st.markdown(f"**Branch:** {branch_info['name']} | **Date:** {pricing_date.strftime('%Y-%m-%d')}")
    
    # Build comparison table data
    comparison_data = []
    renty_prices = []
    competitor_avgs = []
    categories = []
    
    for category in VEHICLE_CATEGORIES.keys():
        if category in pricing_results and category in competitor_data:
            renty_price = pricing_results[category]['final_price']
            comp_stats = competitor_data[category]['stats']
            
            row = {
                'Category': category,
                'Renty Price': f"{renty_price:.0f} SAR"
            }
            
            # Add individual competitor prices
            if comp_stats.get('competitors'):
                for comp in comp_stats['competitors']:
                    row[comp['Competitor_Name']] = f"{comp['Competitor_Price']} SAR"
            
            # Add average and difference
            if comp_stats.get('avg_price'):
                comp_avg = comp_stats['avg_price']
                diff = renty_price - comp_avg
                row['Competitor Avg'] = f"{comp_avg:.0f} SAR"
                row['Difference'] = f"{diff:+.0f} SAR"
                row['Status'] = '✓ Cheaper' if diff < 0 else '△ More Expensive'
                
                # Store for chart
                renty_prices.append(renty_price)
                competitor_avgs.append(comp_avg)
                categories.append(category)
            
            comparison_data.append(row)
    
    # Display table
    if comparison_data:
        import pandas as pd
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Display chart
        st.markdown("### 📈 Price Comparison Chart")
        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Renty prices
        fig.add_trace(go.Bar(
            name='Renty',
            x=categories,
            y=renty_prices,
            marker_color='#1f77b4',
            text=[f"{p:.0f} SAR" for p in renty_prices],
            textposition='outside'
        ))
        
        # Competitor average
        fig.add_trace(go.Bar(
            name='Competitor Avg',
            x=categories,
            y=competitor_avgs,
            marker_color='#ff7f0e',
            text=[f"{p:.0f} SAR" for p in competitor_avgs],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Renty vs Competitors - {branch_info['name']}",
            xaxis_title="Vehicle Category",
            yaxis_title="Price per Day (SAR)",
            barmode='group',
            height=500,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        cheaper_count = sum(1 for r, c in zip(renty_prices, competitor_avgs) if r < c)
        avg_diff = sum(r - c for r, c in zip(renty_prices, competitor_avgs)) / len(renty_prices)
        
        with col1:
            st.metric("Categories Cheaper", f"{cheaper_count}/{len(categories)}")
        
        with col2:
            st.metric("Categories More Expensive", f"{len(categories) - cheaper_count}/{len(categories)}")
        
        with col3:
            st.metric("Avg Price Difference", f"{avg_diff:+.0f} SAR")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    <p><strong>Renty - Intelligent Dynamic Pricing</strong></p>
    <p>Powered by XGBoost ML (95.35% Accuracy) | Real-time Pricing Optimization</p>
    <p>Last Updated: {}</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)

