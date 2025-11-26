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
from live_competitor_pricing import get_competitor_prices_for_dashboard, compare_with_competitors as compare_live, compare_with_competitors
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
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .category-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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
        "base_price": 150.0,
        "icon": "🚗"
    },
    "Compact": {
        "examples": "Toyota Yaris, Hyundai Elantra, Kia Cerato",
        "base_price": 180.0,
        "icon": "🚙"
    },
    "Standard": {
        "examples": "Toyota Camry, Hyundai Sonata, Nissan Altima",
        "base_price": 220.0,
        "icon": "🚘"
    },
    "SUV Compact": {
        "examples": "Hyundai Tucson, Nissan Qashqai, Kia Sportage",
        "base_price": 280.0,
        "icon": "🚐"
    },
    "SUV Standard": {
        "examples": "Toyota RAV4, Nissan X-Trail, Hyundai Santa Fe",
        "base_price": 350.0,
        "icon": "🚙"
    },
    "SUV Large": {
        "examples": "Toyota Land Cruiser, Nissan Patrol, Chevrolet Tahoe",
        "base_price": 500.0,
        "icon": "🚐"
    },
    "Luxury Sedan": {
        "examples": "BMW 5 Series, Mercedes E-Class, Audi A6",
        "base_price": 600.0,
        "icon": "🚗"
    },
    "Luxury SUV": {
        "examples": "BMW X5, Mercedes GLE, Audi Q7",
        "base_price": 800.0,
        "icon": "🚙"
    }
}

# Top branches with names
BRANCHES = {
    122: {"name": "King Khalid Airport - Riyadh", "city": "Riyadh", "is_airport": True},
    15: {"name": "Olaya District - Riyadh", "city": "Riyadh", "is_airport": False},
    63: {"name": "King Fahd Airport - Dammam", "city": "Dammam", "is_airport": True},
    33: {"name": "King Abdulaziz Airport - Jeddah", "city": "Jeddah", "is_airport": True},
    172: {"name": "Al Khobar Business District", "city": "Al Khobar", "is_airport": False},
    45: {"name": "Mecca City Center", "city": "Mecca", "is_airport": False},
    89: {"name": "Medina Downtown", "city": "Medina", "is_airport": False},
    110: {"name": "Riyadh City Center", "city": "Riyadh", "is_airport": False},
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
def load_pricing_engine(_version="v3.8"):
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
        engine, success, message = load_pricing_engine(_version="v3.8")
        st.session_state.engine = engine
        st.session_state.engine_loaded = success
        if success:
            st.sidebar.success("✅ Pricing Engine Ready (v3.6)")
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

st.sidebar.markdown(f"**Model Accuracy:** 95.35%")
st.sidebar.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Main content - Header with Logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("Gemini_Generated_Image_qzl79lqzl79lqzl7.png", use_column_width=True)
    st.markdown('<p class="main-header">Intelligent Dynamic Pricing</p>', unsafe_allow_html=True)
    st.info(f"👋 Welcome, **{user_role}**! Manage pricing for **{branch_info['name']}**")

st.markdown("---")

# Date and condition selectors
st.markdown("### 📅 Date & Conditions")

col1, col2, col3 = st.columns(3)

with col1:
    pricing_date = st.date_input(
        "Pricing Date",
        value=date(2025, 11, 18),  # Latest date with actual data in database
        min_value=date(2023, 1, 1),
        max_value=date(2025, 11, 18),  # Latest available data
        help="Select date for pricing analysis (Database has data up to Nov 18, 2025)"
    )

with col2:
    is_weekend = st.checkbox("📅 Weekend", value=False, help="Friday-Saturday in KSA")

with col3:
    pass  # Spacer

st.markdown("#### Religious Events")
col1, col2, col3, col4 = st.columns(4)

with col1:
    is_holiday = st.checkbox("🎉 Holiday", value=False, help="Eid Al-Fitr, Eid Al-Adha, National Day, Founding Day")

with col2:
    is_ramadan = st.checkbox("🌙 Ramadan", value=False, help="Holy month of Ramadan (peak Umrah)")

with col3:
    is_umrah_season = st.checkbox("🕋 Umrah", value=False, help="Peak Umrah season (Rajab, Shaban, Shawwal)")

with col4:
    is_hajj = st.checkbox("🕌 Hajj", value=False, help="Hajj season (around Eid Al-Adha)")

st.markdown("#### Other Events")
col1, col2, col3, col4 = st.columns(4)

with col1:
    is_school_vacation = st.checkbox("🏖️ Vacation", value=False, help="School vacation periods (Summer, Mid-year)")

with col2:
    is_festival = st.checkbox("🎪 Festival", value=False, help="Riyadh Season, Jeddah Season")

with col3:
    is_sports_event = st.checkbox("🏎️ Sports", value=False, help="Formula 1 Saudi Arabian Grand Prix")

with col4:
    is_conference = st.checkbox("💼 Business", value=False, help="Major business conferences & exhibitions")

# Combine events for pricing engine (backwards compatibility)
is_major_event = is_festival or is_sports_event or is_conference or is_hajj

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
            
            # Get LIVE competitor pricing for this category
            try:
                comp_stats_live = get_competitor_prices_for_dashboard(
                    category=category,
                    branch_name=branch_info['name'],
                    date=pricing_date,
                    is_holiday=is_holiday,
                    is_ramadan=is_ramadan,
                    is_umrah_season=is_umrah_season,
                    is_hajj=is_hajj,
                    is_festival=is_festival,
                    is_sports_event=is_sports_event,
                    is_conference=is_conference,
                    is_weekend=is_weekend,
                    is_vacation=is_school_vacation
                )
                
                # Convert to expected format
                comp_stats = {
                    'avg_price': comp_stats_live['avg_price'],
                    'competitors': comp_stats_live['competitors'],
                    'competitor_count': comp_stats_live['competitor_count'],
                }
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
            
            comparison = compare_live(result['final_price'], comp_stats)
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
                    # Determine badge
                    change_pct = result['price_change_pct']
                    if change_pct < -5:
                        badge = f'<span class="discount-badge">-{abs(change_pct):.0f}% DISCOUNT</span>'
                    elif change_pct > 5:
                        badge = f'<span class="premium-badge">+{change_pct:.0f}% PREMIUM</span>'
                    else:
                        badge = f'<span class="neutral-badge">STANDARD</span>'
                    
                    # Get competitor info for this category
                    comp_info = competitor_data[category]
                    comp_stats = comp_info['stats']
                    
                    # Build complete card HTML
                    card_html = f"""<div class="category-card">
                        <h3 style="color: #003d82; margin-bottom: 0.5rem;">{details['icon']} {category}</h3>
                        <p style="font-size: 0.9rem; color: #6c757d;">{details['examples']}</p>
                        <hr>
                        <p style="font-size: 0.8rem; color: #6c757d; text-decoration: line-through;">
                            Base: {result['base_price']:.0f} SAR/day
                        </p>
                        <h2 style="color: #1f77b4; margin: 0.5rem 0;">
                            {result['final_price']:.0f} SAR<span style="font-size: 0.6em;">/day</span>
                        </h2>
                        <div style="margin: 0.5rem 0;">
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
                            comp_list_html += f"<div style='font-size: 0.7rem; color: #495057; margin-top: 0.2rem;'>• {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR</div>"
                            if not comp_timestamp and 'Date' in comp:
                                comp_timestamp = comp['Date']
                        
                        if not comp_timestamp:
                            comp_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        card_html += f"""<div style="background: #f8f9fa; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem;">
                            <div style="color: #6c757d; margin-bottom: 0.25rem;">
                                <strong>Competitor Avg:</strong> {comp_avg:.0f} SAR/day
                            </div>
                            <div style="color: {comp_color}; font-weight: bold;">
                                {comp_icon} {comp_text} ({comp_count} competitors)
                            </div>
                            {comp_list_html}
                            <div style="color: #6c757d; font-size: 0.7rem; margin-top: 0.25rem;">
                                🔄 Live: {comp_timestamp}
                            </div>
                        </div>"""
                    else:
                        card_html += """<div style="background: #f8f9fa; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem; color: #6c757d;">
                            No competitor data available
                        </div>"""
                    
                    # Add multipliers section
                    card_html += f"""<hr>
                        <div style="font-size: 0.85rem; text-align: left; margin-top: 1rem;">
                            <strong>Multipliers:</strong><br>
                            Demand: {result['demand_multiplier']:.2f}x<br>
                            Supply: {result['supply_multiplier']:.2f}x<br>
                            Events: {result['event_multiplier']:.2f}x
                        </div>
                    </div>"""
                    
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
                    # Determine badge
                    change_pct = result['price_change_pct']
                    if change_pct < -5:
                        badge = f'<span class="discount-badge">-{abs(change_pct):.0f}% DISCOUNT</span>'
                    elif change_pct > 5:
                        badge = f'<span class="premium-badge">+{change_pct:.0f}% PREMIUM</span>'
                    else:
                        badge = f'<span class="neutral-badge">STANDARD</span>'
                    
                    # Get competitor info for this category
                    comp_info = competitor_data[category]
                    comp_stats = comp_info['stats']
                    
                    # Build complete card HTML
                    card_html = f"""<div class="category-card">
                        <h3 style="color: #003d82; margin-bottom: 0.5rem;">{details['icon']} {category}</h3>
                        <p style="font-size: 0.9rem; color: #6c757d;">{details['examples']}</p>
                        <hr>
                        <p style="font-size: 0.8rem; color: #6c757d; text-decoration: line-through;">
                            Base: {result['base_price']:.0f} SAR/day
                        </p>
                        <h2 style="color: #1f77b4; margin: 0.5rem 0;">
                            {result['final_price']:.0f} SAR<span style="font-size: 0.6em;">/day</span>
                        </h2>
                        <div style="margin: 0.5rem 0;">
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
                            comp_list_html += f"<div style='font-size: 0.7rem; color: #495057; margin-top: 0.2rem;'>• {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR</div>"
                            if not comp_timestamp and 'Date' in comp:
                                comp_timestamp = comp['Date']
                        
                        if not comp_timestamp:
                            comp_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                        
                        card_html += f"""<div style="background: #f8f9fa; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem;">
                            <div style="color: #6c757d; margin-bottom: 0.25rem;">
                                <strong>Competitor Avg:</strong> {comp_avg:.0f} SAR/day
                            </div>
                            <div style="color: {comp_color}; font-weight: bold;">
                                {comp_icon} {comp_text} ({comp_count} competitors)
                            </div>
                            {comp_list_html}
                            <div style="color: #6c757d; font-size: 0.7rem; margin-top: 0.25rem;">
                                🔄 Live: {comp_timestamp}
                            </div>
                        </div>"""
                    else:
                        card_html += """<div style="background: #f8f9fa; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.75rem; color: #6c757d;">
                            No competitor data available
                        </div>"""
                    
                    # Add multipliers section
                    card_html += f"""<hr>
                        <div style="font-size: 0.85rem; text-align: left; margin-top: 1rem;">
                            <strong>Multipliers:</strong><br>
                            Demand: {result['demand_multiplier']:.2f}x<br>
                            Supply: {result['supply_multiplier']:.2f}x<br>
                            Events: {result['event_multiplier']:.2f}x
                        </div>
                    </div>"""
                    
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
    
    # Competitor Comparison Section
    st.markdown("---")
    st.markdown("## 📊 Competitor Price Comparison")
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

