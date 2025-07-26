import streamlit as st
import pandas as pd
import plotly.express as px

# Set up the app
st.set_page_config(layout="wide", page_title="Truck Operations Dashboard")
st.title("🚛 End-to-End Truck Operations Dashboard")
st.subheader("Integrating Telematics, Cost Models & Field Documentation")

# Sidebar for inputs
with st.sidebar:
    st.header("Configuration")
    selected_truck = st.selectbox("Select Truck", ["TRK-001", "TRK-002", "TRK-003"])
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    
    st.markdown("---")
    st.header("Cost Model Parameters")
    fuel_price = st.number_input("Diesel Price (R/liter)", value=24.50)
    rate_per_ton_km = st.number_input("Rate per ton/km (R)", value=2.50)
    fixed_monthly_cost = st.number_input("Fixed Monthly Cost (R)", value=21400)

# Sample data - in a real app this would come from your database/APIs
@st.cache_data
def load_sample_data():
    # Telematics data
    telematics = pd.DataFrame({
        'trip_id': ['T001', 'T002', 'T003'],
        'date': ['2023-06-01', '2023-06-05', '2023-06-10'],
        'truck_id': ['TRK-001', 'TRK-001', 'TRK-001'],
        'distance_km': [450, 600, 320],
        'fuel_used_liters': [180, 240, 130],
        'idle_time_minutes': [45, 30, 60],
        'avg_speed_kmh': [72, 68, 65]
    })
    
    # Field documentation
    loading_slips = pd.DataFrame({
        'trip_id': ['T001', 'T002', 'T003'],
        'tonnage_loaded': [28, 32, 25],
        'loading_point': ['Johannesburg', 'Durban', 'Pretoria'],
        'client': ['Client A', 'Client B', 'Client A']
    })
    
    offloading_slips = pd.DataFrame({
        'trip_id': ['T001', 'T002', 'T003'],
        'tonnage_delivered': [27.5, 32, 24.8],
        'offloading_point': ['Cape Town', 'Johannesburg', 'Bloemfontein']
    })
    
    fuel_slips = pd.DataFrame({
        'trip_id': ['T001', 'T002', 'T003'],
        'liters': [185, 245, 135],
        'price_per_liter': [24.50, 24.50, 24.50],
        'total_cost': [185*24.50, 245*24.50, 135*24.50]
    })
    
    return telematics, loading_slips, offloading_slips, fuel_slips

telematics, loading_slips, offloading_slips, fuel_slips = load_sample_data()

# Merge all data
merged_data = telematics.merge(loading_slips, on='trip_id')\
                       .merge(offloading_slips, on='trip_id')\
                       .merge(fuel_slips, on='trip_id')

# Calculate financial metrics
merged_data['revenue'] = merged_data['tonnage_delivered'] * merged_data['distance_km'] * rate_per_ton_km
merged_data['fuel_cost'] = merged_data['liters'] * fuel_price
merged_data['variable_cost_per_km'] = 4.80  # From cost model (tyres, maintenance, etc)
merged_data['variable_cost'] = merged_data['distance_km'] * merged_data['variable_cost_per_km']
merged_data['fixed_cost_allocation'] = (fixed_monthly_cost / 30) * 3  # Assuming 3 days per trip
merged_data['total_cost'] = merged_data['fuel_cost'] + merged_data['variable_cost'] + merged_data['fixed_cost_allocation']
merged_data['profit'] = merged_data['revenue'] - merged_data['total_cost']
merged_data['profit_per_km'] = merged_data['profit'] / merged_data['distance_km']

# Dashboard layout
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trip Details", "Cost Analysis", "Documentation"])

with tab1:
    st.header("Operational & Financial Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Distance (km)", merged_data['distance_km'].sum())
    with col2:
        st.metric("Total Revenue (R)", f"R{merged_data['revenue'].sum():,.2f}")
    with col3:
        st.metric("Total Profit (R)", f"R{merged_data['profit'].sum():,.2f}")
    
    # Profit by trip
    fig = px.bar(merged_data, x='trip_id', y='profit', title='Profit by Trip')
    st.plotly_chart(fig, use_container_width=True)
    
    # Efficiency metrics
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(merged_data, x='distance_km', y='fuel_used_liters', 
                         title='Fuel Efficiency', trendline="ols")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(merged_data, names='client', values='revenue', title='Revenue by Client')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Detailed Trip Analysis")
    
    selected_trip = st.selectbox("Select Trip", merged_data['trip_id'].unique())
    trip_data = merged_data[merged_data['trip_id'] == selected_trip].iloc[0]
    
    st.subheader(f"Trip {selected_trip} Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Route:** {trip_data['loading_point']} → {trip_data['offloading_point']}")
        st.write(f"**Distance:** {trip_data['distance_km']} km")
        st.write(f"**Tonnage Loaded/Delivered:** {trip_data['tonnage_loaded']}/{trip_data['tonnage_delivered']} tons")
        st.write(f"**Fuel Used:** {trip_data['fuel_used_liters']}L (R{trip_data['fuel_cost']:,.2f})")
    with col2:
        st.write(f"**Revenue:** R{trip_data['revenue']:,.2f}")
        st.write(f"**Total Cost:** R{trip_data['total_cost']:,.2f}")
        st.write(f"**Profit:** R{trip_data['profit']:,.2f}")
        st.write(f"**Profit per km:** R{trip_data['profit_per_km']:,.2f}")
    
    # Map visualization would go here in a real app
    st.map()  # Placeholder for actual map integration

with tab3:
    st.header("Cost Model Analysis")
    
    st.subheader("Cost Breakdown")
    fig = px.pie(values=[merged_data['fuel_cost'].sum(), 
                  merged_data['variable_cost'].sum(), 
                  merged_data['fixed_cost_allocation'].sum()],
                names=['Fuel', 'Variable Costs', 'Fixed Costs'],
                title='Total Cost Composition')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Cost per km Analysis")
    fig = px.line(merged_data, x='trip_id', y=['variable_cost_per_km', 'profit_per_km'],
                 title='Cost & Profit per km')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("RFA Cost Model Parameters")
    st.write("""
    The cost model is based on the Road Freight Association Vehicle Cost Schedule:
    - **Fixed Costs:** Depreciation, Finance, Insurance, Licensing, Admin, Salaries
    - **Variable Costs:** Fuel, Tyres, Maintenance, Tolls, Driver Allowances
    """)
    st.write(f"Current fixed monthly cost: R{fixed_monthly_cost:,.2f}")
    st.write(f"Current variable cost per km: R{merged_data['variable_cost_per_km'].mean():.2f}")

with tab4:
    st.header("Field Documentation")
    
    st.subheader("Loading Slips")
    st.dataframe(loading_slips)
    
    st.subheader("Offloading Slips")
    st.dataframe(offloading_slips)
    
    st.subheader("Fuel Slips")
    st.dataframe(fuel_slips)
    
    st.subheader("Document Verification Status")
    doc_status = merged_data[['trip_id', 'tonnage_loaded', 'tonnage_delivered', 'liters']]
    doc_status['verified'] = ["✅ Complete" if x > 0 else "❌ Missing" for x in doc_status['liters']]
    st.dataframe(doc_status)

st.markdown("---")
st.write("Prototype for Truck Operations Dashboard - Integrating Telematics, Cost Models & Field Documentation")
