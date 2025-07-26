import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
from PIL import Image
import io
import base64

# Configure the page
st.set_page_config(
    page_title="Trucking Control Tower",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data storage (simulating database)
if 'trips' not in st.session_state:
    st.session_state.trips = []
if 'loading_slips' not in st.session_state:
    st.session_state.loading_slips = []
if 'offloading_slips' not in st.session_state:
    st.session_state.offloading_slips = []
if 'fuel_slips' not in st.session_state:
    st.session_state.fuel_slips = []

# Sample cost data (normally from Google Sheets)
SAMPLE_COST_DATA = {
    "TRK-001": {"cost_per_km": 6.94, "fixed_monthly": 21400, "fuel_lper100km": 45},
    "TRK-002": {"cost_per_km": 7.12, "fixed_monthly": 22800, "fuel_lper100km": 48},
    "TRK-003": {"cost_per_km": 6.78, "fixed_monthly": 20900, "fuel_lper100km": 42}
}

def save_image_as_base64(uploaded_file):
    """Convert uploaded image to base64 for storage"""
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_string = base64.b64encode(bytes_data).decode()
        return base64_string
    return None

def display_image_from_base64(base64_string, width=200):
    """Display image from base64 string"""
    if base64_string:
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        st.image(image, width=width)

def create_trip(truck_id, driver_id, route, date_selected):
    """Create a new trip record"""
    trip_id = str(uuid.uuid4())
    trip = {
        'id': trip_id,
        'truck_id': truck_id,
        'driver_id': driver_id,
        'route': route,
        'date': date_selected,
        'status': 'Active',
        'distance_km': 0,
        'total_cost': 0,
        'revenue': 0,
        'profit': 0,
        'created_at': datetime.now()
    }
    st.session_state.trips.append(trip)
    return trip_id

def get_active_trips():
    """Get list of active trips for dropdown"""
    return [trip for trip in st.session_state.trips if trip['status'] == 'Active']

def calculate_trip_profitability(trip_id):
    """Calculate profitability for a specific trip"""
    trip = next((t for t in st.session_state.trips if t['id'] == trip_id), None)
    if not trip:
        return None
    
    # Get slip data
    loading_slips = [s for s in st.session_state.loading_slips if s['trip_id'] == trip_id]
    offloading_slips = [s for s in st.session_state.offloading_slips if s['trip_id'] == trip_id]
    fuel_slips = [s for s in st.session_state.fuel_slips if s['trip_id'] == trip_id]
    
    # Calculate totals
    total_tonnage_loaded = sum(slip['tonnage_collected'] for slip in loading_slips)
    total_tonnage_delivered = sum(slip['tonnage_dropped'] for slip in offloading_slips)
    total_fuel_cost = sum(slip['total_cost'] for slip in fuel_slips)
    
    # Get cost data
    truck_cost = SAMPLE_COST_DATA.get(trip['truck_id'], SAMPLE_COST_DATA['TRK-001'])
    
    # Calculate revenue (assuming R2.50 per ton per km)
    rate_per_ton_km = 2.50
    if trip['distance_km'] > 0 and total_tonnage_delivered > 0:
        revenue = trip['distance_km'] * total_tonnage_delivered * rate_per_ton_km
        variable_cost = trip['distance_km'] * truck_cost['cost_per_km']
        total_cost = variable_cost + total_fuel_cost
        profit = revenue - total_cost
        
        return {
            'revenue': revenue,
            'total_cost': total_cost,
            'profit': profit,
            'tonnage_delivered': total_tonnage_delivered,
            'fuel_cost': total_fuel_cost
        }
    return None

def show_dashboard():
    """Main dashboard view"""
    st.title("🚛 Trucking Control Tower Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_trips = len(get_active_trips())
        st.metric("Active Trips", active_trips)
    
    with col2:
        total_slips = len(st.session_state.loading_slips) + len(st.session_state.fuel_slips)
        st.metric("Total Slips", total_slips)
    
    with col3:
        completed_trips = len([t for t in st.session_state.trips if t['status'] == 'Completed'])
        st.metric("Completed Trips", completed_trips)
    
    with col4:
        total_profit = sum(t.get('profit', 0) for t in st.session_state.trips)
        st.metric("Total Profit", f"R{total_profit:,.2f}")
    
    # Recent trips table
    st.subheader("Recent Trips")
    if st.session_state.trips:
        trips_df = pd.DataFrame(st.session_state.trips)
        trips_df['date'] = pd.to_datetime(trips_df['date']).dt.strftime('%Y-%m-%d')
        st.dataframe(trips_df[['truck_id', 'driver_id', 'route', 'date', 'status', 'profit']], use_container_width=True)
    else:
        st.info("No trips recorded yet. Start by creating a trip and adding slips!")

def create_trip_page():
    """Create new trip page"""
    st.title("📋 Create New Trip")
    
    with st.form("create_trip"):
        col1, col2 = st.columns(2)
        
        with col1:
            truck_id = st.selectbox("Truck ID", ["TRK-001", "TRK-002", "TRK-003"])
            driver_id = st.text_input("Driver ID", placeholder="e.g., DRV-001")
        
        with col2:
            route = st.text_input("Route", placeholder="e.g., JHB to DBN")
            trip_date = st.date_input("Trip Date", value=date.today())
        
        if st.form_submit_button("Create Trip", use_container_width=True):
            if driver_id and route:
                trip_id = create_trip(truck_id, driver_id, route, trip_date)
                st.success(f"Trip created successfully! Trip ID: {trip_id[:8]}...")
                st.balloons()
            else:
                st.error("Please fill in all required fields")

def add_loading_slip():
    """Add loading slip page"""
    st.title("📄 Add Loading Slip")
    
    active_trips = get_active_trips()
    if not active_trips:
        st.warning("No active trips available. Please create a trip first.")
        return
    
    with st.form("loading_slip"):
        col1, col2 = st.columns(2)
        
        with col1:
            trip_options = [f"{trip['truck_id']} - {trip['route']} ({trip['date']})" for trip in active_trips]
            selected_trip_idx = st.selectbox("Select Trip", range(len(trip_options)), format_func=lambda x: trip_options[x])
            tonnage_collected = st.number_input("Tonnage Collected", min_value=0.0, step=0.1)
            loading_point = st.text_input("Loading Point")
        
        with col2:
            client = st.text_input("Client")
            ticket_number = st.text_input("Ticket Number")
            slip_photo = st.file_uploader("Upload Slip Photo", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("Save Loading Slip", use_container_width=True):
            if tonnage_collected > 0 and loading_point and client:
                trip_id = active_trips[selected_trip_idx]['id']
                
                loading_slip = {
                    'id': str(uuid.uuid4()),
                    'trip_id': trip_id,
                    'tonnage_collected': tonnage_collected,
                    'loading_point': loading_point,
                    'client': client,
                    'ticket_number': ticket_number,
                    'photo': save_image_as_base64(slip_photo),
                    'created_at': datetime.now()
                }
                
                st.session_state.loading_slips.append(loading_slip)
                st.success("Loading slip saved successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields")

def add_offloading_slip():
    """Add offloading slip page"""
    st.title("📦 Add Offloading Slip")
    
    active_trips = get_active_trips()
    if not active_trips:
        st.warning("No active trips available. Please create a trip first.")
        return
    
    with st.form("offloading_slip"):
        col1, col2 = st.columns(2)
        
        with col1:
            trip_options = [f"{trip['truck_id']} - {trip['route']} ({trip['date']})" for trip in active_trips]
            selected_trip_idx = st.selectbox("Select Trip", range(len(trip_options)), format_func=lambda x: trip_options[x])
            tonnage_dropped = st.number_input("Tonnage Delivered", min_value=0.0, step=0.1)
            drop_point = st.text_input("Drop Point")
        
        with col2:
            receiver = st.text_input("Receiver")
            signed_by = st.text_input("Signed By")
            slip_photo = st.file_uploader("Upload Slip Photo", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("Save Offloading Slip", use_container_width=True):
            if tonnage_dropped > 0 and drop_point and receiver:
                trip_id = active_trips[selected_trip_idx]['id']
                
                offloading_slip = {
                    'id': str(uuid.uuid4()),
                    'trip_id': trip_id,
                    'tonnage_dropped': tonnage_dropped,
                    'drop_point': drop_point,
                    'receiver': receiver,
                    'signed_by': signed_by,
                    'photo': save_image_as_base64(slip_photo),
                    'created_at': datetime.now()
                }
                
                st.session_state.offloading_slips.append(offloading_slip)
                st.success("Offloading slip saved successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields")

def add_fuel_slip():
    """Add fuel slip page"""
    st.title("⛽ Add Fuel Slip")
    
    active_trips = get_active_trips()
    if not active_trips:
        st.warning("No active trips available. Please create a trip first.")
        return
    
    with st.form("fuel_slip"):
        col1, col2 = st.columns(2)
        
        with col1:
            trip_options = [f"{trip['truck_id']} - {trip['route']} ({trip['date']})" for trip in active_trips]
            selected_trip_idx = st.selectbox("Select Trip", range(len(trip_options)), format_func=lambda x: trip_options[x])
            litres = st.number_input("Litres", min_value=0.0, step=0.1)
            price_per_litre = st.number_input("Price per Litre (R)", min_value=0.0, step=0.01, value=24.50)
        
        with col2:
            fuel_station = st.text_input("Fuel Station")
            total_cost = litres * price_per_litre
            st.metric("Total Cost", f"R{total_cost:.2f}")
            slip_photo = st.file_uploader("Upload Receipt Photo", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("Save Fuel Slip", use_container_width=True):
            if litres > 0 and fuel_station:
                trip_id = active_trips[selected_trip_idx]['id']
                
                fuel_slip = {
                    'id': str(uuid.uuid4()),
                    'trip_id': trip_id,
                    'litres': litres,
                    'price_per_litre': price_per_litre,
                    'total_cost': total_cost,
                    'station': fuel_station,
                    'photo': save_image_as_base64(slip_photo),
                    'created_at': datetime.now()
                }
                
                st.session_state.fuel_slips.append(fuel_slip)
                st.success("Fuel slip saved successfully!")
                st.balloons()
            else:
                st.error("Please fill in all required fields")

def trip_calculator():
    """Trip profitability calculator"""
    st.title("💰 Trip Profitability Calculator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Trip Details")
        truck_id = st.selectbox("Truck", list(SAMPLE_COST_DATA.keys()))
        distance = st.number_input("Distance (km)", min_value=0.0, step=10.0)
        tonnage = st.number_input("Tonnage", min_value=0.0, step=0.5)
        rate_per_ton_km = st.number_input("Rate per Ton/km (R)", min_value=0.0, step=0.1, value=2.50)
        
        # Get cost data
        truck_cost = SAMPLE_COST_DATA.get(truck_id, SAMPLE_COST_DATA['TRK-001'])
        cost_per_km = truck_cost['cost_per_km']
        
        st.metric("Cost per km", f"R{cost_per_km:.2f}")
    
    with col2:
        st.subheader("Profitability Analysis")
        
        if distance > 0 and tonnage > 0:
            revenue = distance * tonnage * rate_per_ton_km
            total_cost = distance * cost_per_km
            profit = revenue - total_cost
            margin = (profit / revenue) * 100 if revenue > 0 else 0
            
            # Display metrics
            col2a, col2b, col2c = st.columns(3)
            
            with col2a:
                st.metric("Revenue", f"R{revenue:,.2f}")
            with col2b:
                st.metric("Total Cost", f"R{total_cost:,.2f}")
            with col2c:
                st.metric("Profit", f"R{profit:,.2f}", delta=f"{margin:.1f}%")
            
            # Breakeven analysis
            st.subheader("Breakeven Analysis")
            if rate_per_ton_km > 0:
                breakeven_tonnage = cost_per_km / rate_per_ton_km
                st.info(f"Breakeven tonnage for this route: **{breakeven_tonnage:.1f} tons per km**")
            
            # Profitability chart
            if profit > 0:
                st.success(f"✅ This trip is profitable with a {margin:.1f}% margin")
            else:
                st.error(f"❌ This trip will lose R{abs(profit):,.2f}")

def view_slips():
    """View all slips with photos"""
    st.title("📋 View All Slips")
    
    tab1, tab2, tab3 = st.tabs(["Loading Slips", "Offloading Slips", "Fuel Slips"])
    
    with tab1:
        st.subheader("Loading Slips")
        for slip in st.session_state.loading_slips:
            with st.expander(f"Loading - {slip['loading_point']} - {slip['tonnage_collected']}t"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Client:** {slip['client']}")
                    st.write(f"**Tonnage:** {slip['tonnage_collected']} tons")
                    st.write(f"**Ticket:** {slip['ticket_number']}")
                    st.write(f"**Date:** {slip['created_at'].strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if slip['photo']:
                        display_image_from_base64(slip['photo'])
    
    with tab2:
        st.subheader("Offloading Slips")
        for slip in st.session_state.offloading_slips:
            with st.expander(f"Offloading - {slip['drop_point']} - {slip['tonnage_dropped']}t"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Receiver:** {slip['receiver']}")
                    st.write(f"**Tonnage:** {slip['tonnage_dropped']} tons")
                    st.write(f"**Signed by:** {slip['signed_by']}")
                    st.write(f"**Date:** {slip['created_at'].strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if slip['photo']:
                        display_image_from_base64(slip['photo'])
    
    with tab3:
        st.subheader("Fuel Slips")
        for slip in st.session_state.fuel_slips:
            with st.expander(f"Fuel - {slip['station']} - {slip['litres']}L"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Station:** {slip['station']}")
                    st.write(f"**Litres:** {slip['litres']}L")
                    st.write(f"**Price:** R{slip['price_per_litre']:.2f}/L")
                    st.write(f"**Total:** R{slip['total_cost']:.2f}")
                    st.write(f"**Date:** {slip['created_at'].strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if slip['photo']:
                        display_image_from_base64(slip['photo'])

def main():
    """Main application"""
    
    # Sidebar navigation
    st.sidebar.title("🚛 Navigation")
    st.sidebar.markdown("---")
    
    pages = {
        "📊 Dashboard": show_dashboard,
        "🆕 Create Trip": create_trip_page,
        "📄 Loading Slip": add_loading_slip,
        "📦 Offloading Slip": add_offloading_slip,
        "⛽ Fuel Slip": add_fuel_slip,
        "💰 Trip Calculator": trip_calculator,
        "📋 View Slips": view_slips
    }
    
    selection = st.sidebar.radio("Select Page", list(pages.keys()))
    
    # Add some info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This is your Trucking Control Tower MVP. "
        "Start by creating trips, then add slips to track profitability."
    )
    
    # Run selected page
    pages[selection]()

if __name__ == "__main__":
    main()
