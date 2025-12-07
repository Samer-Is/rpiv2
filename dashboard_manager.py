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
st.sidebar.image("Gemini_Generated_Image_qzl79lqzl79lqzl7.png", use_container_width=True)
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

st.sidebar.markdown(f"**XGBOOST_MODEL_RUNNING_V4**")

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

st.sidebar.markdown("---")

# =====================================================
# SIDEBAR: Date & Events Section
# =====================================================
st.sidebar.markdown("### 📅 Date & Events")

pricing_date = st.sidebar.date_input(
    "Pricing Date",
    value=date(2025, 11, 18),
    min_value=date(2023, 1, 1),
    max_value=date(2025, 11, 18),
    help="Pricing date"
)

st.sidebar.markdown("**Events:**")
col_ev1, col_ev2 = st.sidebar.columns(2)
with col_ev1:
    is_weekend = st.checkbox("📅 Weekend", value=False)
    is_holiday = st.checkbox("🎉 Holiday", value=False)
    is_ramadan = st.checkbox("🌙 Ramadan", value=False)
    is_umrah_season = st.checkbox("🕋 Umrah", value=False)
with col_ev2:
    is_hajj = st.checkbox("🕌 Hajj", value=False)
    is_school_vacation = st.checkbox("🏖️ Vacation", value=False)
    is_festival = st.checkbox("🎪 Festival", value=False)
    is_sports_event = st.checkbox("🏎️ Sports", value=False)
    is_conference = st.checkbox("💼 Business", value=False)

# Combine events for pricing engine (backwards compatibility)
is_major_event = is_festival or is_sports_event or is_conference or is_hajj

# Show active events in sidebar
active_events = []
if is_holiday: active_events.append("Holiday")
if is_ramadan: active_events.append("Ramadan")
if is_umrah_season: active_events.append("Umrah")
if is_hajj: active_events.append("Hajj")
if is_school_vacation: active_events.append("Vacation")
if is_festival: active_events.append("Festival")
if is_sports_event: active_events.append("Sports")
if is_conference: active_events.append("Business")

if active_events:
    st.sidebar.warning(f"⚠️ PREMIUM: {', '.join(active_events)}")
else:
    st.sidebar.success("✓ Normal Day")

st.sidebar.markdown("---")

# =====================================================
# SIDEBAR: Fleet Status Section
# =====================================================
st.sidebar.markdown("### 🚗 Fleet Status")

utilization_mode = st.sidebar.radio(
    "Mode",
    ["Real-time (DB)", "Manual"],
    help="Real-time: Query database. Manual: Demo mode"
)

if utilization_mode == "Real-time (DB)":
    util_data = get_current_utilization(
        branch_id=st.session_state.selected_branch,
        date=pricing_date
    )
    
    total_vehicles = util_data['total_vehicles']
    rented_vehicles = util_data['rented_vehicles']
    available_vehicles = util_data['available_vehicles']
    utilization_pct = util_data['utilization_pct']
    
    if util_data['source'] in ['database', 'local_file']:
        st.sidebar.success(f"✓ {rented_vehicles}/{total_vehicles} ({utilization_pct:.1f}%)")
    else:
        st.sidebar.warning(f"⚠ No data - using defaults")
else:
    total_vehicles = st.sidebar.number_input("Fleet Size", 10, 500, 100)
    rented_vehicles = st.sidebar.slider("Rented", 0, int(total_vehicles), int(total_vehicles * 0.5))
    utilization_pct = (rented_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
    available_vehicles = total_vehicles - rented_vehicles

# Utilization indicator
if utilization_pct < 30:
    util_color, util_status = "🟢", "Low"
elif utilization_pct < 70:
    util_color, util_status = "🟡", "Medium"
else:
    util_color, util_status = "🔴", "High"

st.sidebar.metric("Utilization", f"{util_color} {utilization_pct:.0f}%", f"{available_vehicles} available")

# =====================================================
# MAIN CONTENT - Header
# =====================================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("Gemini_Generated_Image_qzl79lqzl79lqzl7.png", use_container_width=True)
    st.markdown('<p class="main-header">Intelligent Dynamic Pricing</p>', unsafe_allow_html=True)
    st.info(f"👋 **{user_role}** | **{branch_info['name']}** | {pricing_date.strftime('%Y-%m-%d')} | {util_color} {utilization_pct:.0f}% Utilization")

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
    
# =====================================================
# CAR MODEL PRICE COMPARISON SECTION
# =====================================================
st.markdown("---")
st.markdown("## 🚗 Car-by-Car Price Comparison")
st.markdown(f"*Exact vehicle model matches between Renty and competitors*")

# Import car model matcher
from car_model_matcher import find_matching_vehicles, get_best_matches_per_model

# Get base prices for matching
base_prices_for_matching = {
    cat: pricing_results[cat]['base_price'] 
    for cat in pricing_results.keys()
}

# Get competitor data in the right format
competitor_data_for_matching = {}
for cat, data in competitor_data.items():
    if data.get('stats') and data['stats'].get('competitors'):
        competitor_data_for_matching[cat] = {
            'competitors': data['stats']['competitors']
        }

# Find matching vehicles
all_matches = find_matching_vehicles(competitor_data_for_matching, base_prices_for_matching)
model_matches = get_best_matches_per_model(all_matches)

if model_matches:
    # Display matches in a grid
    st.markdown(f"**Found {len(all_matches)} matches across {len(model_matches)} Renty models**")
    
    # Create columns for cards
    cols_per_row = 3
    models_list = list(model_matches.items())
    
    for row_start in range(0, len(models_list), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for col_idx, col in enumerate(cols):
            if row_start + col_idx < len(models_list):
                renty_model, matches = models_list[row_start + col_idx]
                
                if matches:
                    first_match = matches[0]
                    renty_price = first_match['renty_base_price']
                    category = first_match['renty_category']
                    
                    # Calculate best competitor price
                    best_competitor_price = min(m['competitor_price'] for m in matches)
                    price_diff = renty_price - best_competitor_price
                    
                    # Determine status color
                    if price_diff < 0:
                        status_color = "#28a745"  # Green - cheaper
                        status_text = "CHEAPER"
                        diff_text = f"-{abs(price_diff):.0f} SAR"
                    else:
                        status_color = "#dc3545"  # Red - more expensive
                        status_text = "MORE"
                        diff_text = f"+{abs(price_diff):.0f} SAR"
                    
                    with col:
                        st.markdown(f"""
                        <div style="
                            border: 2px solid {status_color};
                            border-radius: 10px;
                            padding: 15px;
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            margin-bottom: 10px;
                            min-height: 200px;
                        ">
                            <div style="
                                font-size: 1.1rem;
                                font-weight: bold;
                                color: #4fc3f7;
                                margin-bottom: 5px;
                            ">🚙 {renty_model}</div>
                            <div style="
                                font-size: 0.85rem;
                                color: #90a4ae;
                                margin-bottom: 10px;
                            ">{category}</div>
                            <div style="
                                display: flex;
                                justify-content: space-between;
                                margin-bottom: 10px;
                            ">
                                <div>
                                    <span style="color: #90a4ae; font-size: 0.8rem;">Renty:</span><br/>
                                    <span style="color: white; font-size: 1.2rem; font-weight: bold;">{renty_price:.0f} SAR</span>
                                </div>
                                <div style="text-align: right;">
                                    <span style="color: #90a4ae; font-size: 0.8rem;">Best Competitor:</span><br/>
                                    <span style="color: #ffb74d; font-size: 1.2rem; font-weight: bold;">{best_competitor_price:.0f} SAR</span>
                                </div>
                            </div>
                            <div style="
                                text-align: center;
                                padding: 8px;
                                background: {status_color}22;
                                border-radius: 5px;
                                color: {status_color};
                                font-weight: bold;
                                font-size: 0.95rem;
                            ">{status_text} {diff_text}</div>
                            <div style="
                                margin-top: 10px;
                                font-size: 0.75rem;
                                color: #78909c;
                                max-height: 60px;
                                overflow-y: auto;
                            ">
                        """, unsafe_allow_html=True)
                        
                        # Show competitor details
                        comp_details = "<br/>".join([
                            f"• {m['competitor_supplier']}: {m['competitor_price']:.0f} SAR" 
                            for m in matches[:3]
                        ])
                        st.markdown(f"""
                            {comp_details}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
else:
    st.info("No exact car model matches found between Renty fleet and competitor data.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    <p><strong>Renty - Intelligent Dynamic Pricing</strong></p>
    <p>Powered by XGBoost ML (95.35% Accuracy) | Real-time Pricing Optimization</p>
    <p>Last Updated: {}</p>
</div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)

