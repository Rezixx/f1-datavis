import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import fastf1 as ff1
import numpy as np

from app.data_loader import (
    load_session,
    get_circuits_for_year,
    get_sessions_for_circuit_year,
    get_circuit_geojson,
    )

from app.viz import ( 
    plot_lap_times,
    plot_tire_strategy_chart,
    create_3d_circuit_visualization,
    create_circuit_flythrough_animation
    )


ff1.Cache.enable_cache('cache')
st.set_page_config(page_title="F1 Strategy Dashboard", layout="wide")
st.title("🏎️ F1 App - Assignment 3")
st.text("Feel Racing.")

if 'session_data' not in st.session_state:
    st.session_state.session_data = None
if 'show_quick_laps' not in st.session_state:
    st.session_state.show_quick_laps = False  # Default to quick laps

col1, col2 = st.columns(2)

tab1, tab2, tab3 = st.tabs(["General Dashboard", "Driver Analysis", "Circuit Analysis"])

session_data = None
circuit_dropdown = None

with col1:
    year_dropdown = st.selectbox("Select Year", [2023, 2024, 2025], index=None)
    if year_dropdown is not None:
        circuits = get_circuits_for_year(year_dropdown)
        if not circuits.empty:
            circuit_dropdown = st.selectbox("Select Circuit", circuits['name'].tolist(), index=None)
            if circuit_dropdown is not None:
                # Get available sessions for this circuit and year
                available_sessions = get_sessions_for_circuit_year(year_dropdown, circuit_dropdown)
                if available_sessions:
                    session_type = st.selectbox("Select Session Type", available_sessions, index=None)
                    
                    if session_type is not None:
                        # Add loading and displaying session data
                        try:
                            with st.spinner(f"🏎️ Loading {year_dropdown} {circuit_dropdown} {session_type}..."):
                                session_data = load_session(year_dropdown, circuit_dropdown, session_type)
                            st.success(f"Session loaded successfully!")
                        except Exception as e:
                            st.error(f"Error loading session: {e}")
                else:
                    st.warning("No sessions available for this circuit and year combination.")
        else:
            st.warning("No circuits found for the selected year.")
with col2:
    cl1, cl2 = st.columns(2)
    with cl1:
        if circuit_dropdown is not None: st.metric("Circuit", circuit_dropdown)
        if session_data is not None:
            st.metric("Total Laps", str(session_data.total_laps))
            session_date = session_data.date
            st.metric("Session Date", f"{session_date:%d.%m.%Y} at {session_date:%H:%M}")
        #st.text(f"{session_data["meeting_key"]}")
            

    with cl2:
        st.image("assets/F1-icon.svg", width=340)
with tab1:
    if 'session_data' in locals() and session_data is not None:
        if st.session_state.show_quick_laps:
            st.markdown("#### ⚡ Quick Laps Analysis")
            lap_times_fig = plot_lap_times(session_data, quick_load=True)
        else:
            st.markdown("#### 🏁 All Laps Analysis")
            lap_times_fig = plot_lap_times(session_data, quick_load=False)
        with st.expander("Lap Times Chart", expanded=True):
            # Create button columns for better layout
            btn_col1, btn_col2= st.columns([1, 1])
            with btn_col1:
                if st.button(
                    "⚡ Quick Laps", 
                    type="secondary" if not st.session_state.show_quick_laps else "secondary",
                    key="quick_laps_btn"
                ):
                    st.session_state.show_quick_laps = True
            with btn_col2:
                if st.button(
                    "🏁 All Laps", 
                    type="primary" if st.session_state.show_quick_laps else "secondary",
                    key="all_laps_btn"
                ):
                    st.session_state.show_quick_laps = False
            
            # Display the plot
            st.plotly_chart(lap_times_fig, use_container_width=True)
            
        with st.expander("Tire Strategy Chart", expanded=True):  
            tire_strat_fig = plot_tire_strategy_chart(session_data)
            st.plotly_chart(tire_strat_fig, use_container_width=True) 
            
        

with tab2:
    st.header("Driver Analysis")
    st.info("Driver analysis features will be implemented here. This tab will use OpenF1 API for driver-specific data.")

with tab3:
    st.header("Circuit Analysis - 3D Visualization")
    
    if circuit_dropdown is not None:
        geo_circuits = get_circuit_geojson()
        
        viz_tab1, viz_tab2 = st.tabs(["3D Circuit View", "Circuit Flythrough"])
        
        with viz_tab1:
            st.markdown("#### 🏔️ 3D Circuit with Terrain")
            
            try:
                with st.spinner("Creating 3D visualization..."):
                    circuit_3d_fig = create_3d_circuit_visualization(
                        circuit_dropdown, 
                        geo_circuits, 
                        session_data
                    )
                
                if circuit_3d_fig:
                    st.plotly_chart(circuit_3d_fig, use_container_width=True)
                    
                    # Add controls
                    st.markdown("**Controls:**")
                    st.markdown("- 🖱️ **Mouse**: Rotate, zoom, pan the 3D view")
                    st.markdown("- 🔴 **Red line**: Circuit track layout") 
                    st.markdown("- 💎 **Green diamond**: Start/Finish line")
                    st.markdown("- 🌄 **Surface**: Terrain elevation")
                else:
                    st.error("Circuit not found in the geo data.")
                    
            except Exception as e:
                st.error(f"Error creating 3D visualization: {e}")
        
        with viz_tab2:
            st.markdown("#### 🎬 Animated Circuit Flythrough")
            
            try:
                with st.spinner("Creating flythrough animation..."):
                    flythrough_fig = create_circuit_flythrough_animation(
                        circuit_dropdown,
                        geo_circuits
                    )
                
                if flythrough_fig:
                    st.plotly_chart(flythrough_fig, use_container_width=True)
                    
                    st.markdown("**Instructions:**")
                    st.markdown("- ▶️ Click **Play** to start the animated flythrough")
                    st.markdown("- ⏸️ Click **Pause** to stop the animation")
                    st.markdown("- 🎥 The camera follows the racing line around the circuit")
                else:
                    st.error("Could not create flythrough animation.")
                    
            except Exception as e:
                st.error(f"Error creating flythrough: {e}")
        
        # Circuit statistics
        with st.expander("Circuit Statistics", expanded=False):
            try:
                circuit_geo = None
                for feature in geo_circuits['Location']:
                    if feature['Location'] == circuit_dropdown:
                        circuit_geo = feature
                        break
                
                if circuit_geo:
                    coordinates = circuit_geo['geometry'].apply(lambda x: x.coords[0] if x else None)
                    
                    # Calculate approximate track length
                    total_distance = 0
                    for i in range(len(coordinates) - 1):
                        lat1, lon1 = coordinates[i][1], coordinates[i][0]
                        lat2, lon2 = coordinates[i+1][1], coordinates[i+1][0]
                        
                        # Haversine formula for distance
                        R = 6371000  # Earth radius in meters
                        dlat = np.radians(lat2 - lat1)
                        dlon = np.radians(lon2 - lon1)
                        a = (np.sin(dlat/2)**2 + 
                             np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
                             np.sin(dlon/2)**2)
                        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                        total_distance += R * c
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Track Length", f"{total_distance/1000:.2f} km")
                    with col2:
                        st.metric("Number of Coordinates", len(coordinates))
                    with col3:
                        if session_data is not None:
                            st.metric("Session Type", session_type)
                
            except Exception as e:
                st.error(f"Error calculating circuit statistics: {e}")
    else:
        st.info("Please select a circuit from the dropdown above to view the 3D visualization.")
        
        # Show available circuits preview
        geo_circuits = get_circuit_geojson()
        available_circuits = [feature['Location'] for feature in geo_circuits['Location']]
        st.markdown("**Available Circuits for 3D Visualization:**")
        for circuit in sorted(available_circuits)[:10]:  # Show first 10
            st.markdown(f"- {circuit}")
        if len(available_circuits) > 10:
            st.markdown(f"... and {len(available_circuits) - 10} more circuits")




