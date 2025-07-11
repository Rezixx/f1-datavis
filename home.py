import streamlit as st
from streamlit_navigation_bar import st_navbar
import pages as pg
import fastf1 as ff1
import os

from app.data_loader import (
    load_session,
    get_circuits_for_year,
    get_sessions_for_circuit_year,
    get_drivers_session
    )

from app.viz import (
    plot_lap_times,
    plot_tire_strategy_chart,
    driver_comparison_chart,
    weather_analysis_chart
)

# Setup states
if 'session_data' not in st.session_state:
    st.session_state.session_data = None
if 'show_quick_laps' not in st.session_state:
    st.session_state.show_quick_laps = False  # Default to quick laps
if 'circuit_dropdown' not in st.session_state:
    st.session_state.circuit_dropdown = None


# Initialize FastF1 cache
if os.path.exists('cache'):
    ff1.Cache.enable_cache('cache')

st.set_page_config(page_title="🏎️🏁F1 Paddock App", layout="wide", initial_sidebar_state="expanded")

def setup_sidebar():
    circuit_dropdown = None
    # Custom HTML/CSS for the banner
    custom_html = """
    <div class="banner">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="position:absolute; top:0; left:0;">
            <defs>
                <pattern id="lines" patternUnits="userSpaceOnUse" width="80" height="80">
                    <path d="M-20,20 l40,-40 M0,80 l80,-80 M60,100 l40,-40" 
                          stroke="#222222" stroke-width="2" />
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#lines)" />
        </svg>
    </div>
    <style>
        .banner {
            background-color: black;
            height: 200px;
            width: 100vw;
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
        }
    </style>
    """
    # Display the custom HTML
    st.components.v1.html(custom_html)
    with st.sidebar:
        #st.image("assets/F1-icon.svg", use_column_width=True)
        st.title("🏎️🏁F1 Paddock App")
        year_dropdown = st.selectbox("Select Year", [2023, 2024, 2025], index=None)
        if year_dropdown is not None:
            circuits = get_circuits_for_year(year_dropdown)
            if not circuits.empty:
                circuit_dropdown = st.selectbox("Select Circuit", circuits['name'].tolist(), index=None)
                st.session_state.circuit_dropdown = circuit_dropdown  # Store in session state
                if circuit_dropdown is not None:
                    # Get available sessions for this circuit and year
                    available_sessions = get_sessions_for_circuit_year(year_dropdown, circuit_dropdown)
                    if available_sessions:
                        session_type = st.selectbox("Select Session Type", available_sessions, index=None)
                        if session_type is not None:
                            st.session_state.session_data = load_session(year_dropdown, circuit_dropdown, session_type)
                            session_data = st.session_state.session_data
                            st.success(f"Session loaded successfully!")
                            if circuit_dropdown is not None: 
                                st.metric("Circuit", circuit_dropdown)
                            if session_data is not None:
                                st.metric("Total Laps", str(session_data.total_laps))
                                session_date = session_data.date
                                st.metric("Session Date", f"{session_date:%d.%m.%Y} at {session_date:%H:%M}")
                    else:
                        st.warning("No sessions available for this circuit and year combination.")
            else:
                st.warning("No circuits found for the selected year.")
      
setup_sidebar()

#|-------------- Main App Content --------------|   
def home():
    st.title("🏎️🏁F1 Paddock App")
    st.text("Feel Racing. Explore Racing. Visualize Racing.")   
        
    tab1, tab2, tab3 = st.tabs(["General Dashboard", "Driver Analysis", "Weather Analysis"])
    session_data = st.session_state.session_data
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
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            driver1_dropdown = st.selectbox(
                "Select Driver 1",
                get_drivers_session(session_data), 
                index = None
                )
            if driver1_dropdown is not None:
                lap_driver1 = st.select_slider(options=session_data.laps.pick_driver(driver1_dropdown)["LapNumber"].to_list(),
                    label="Select Lap Number for Driver 1",
                    value = session_data.laps.pick_driver(driver1_dropdown).pick_fastest()["LapNumber"])
        with d_col2:
            driver2_dropdown = st.selectbox(
                "Select Driver 2",
                get_drivers_session(session_data),
                index = None
                )
            if driver2_dropdown is not None:
                lap_driver2 = st.select_slider(options=session_data.laps.pick_driver(driver1_dropdown)["LapNumber"].to_list(),
                    label="Select Lap Number for Driver 2",
                    value = session_data.laps.pick_driver(driver2_dropdown).pick_fastest()["LapNumber"])
                
            
        if driver1_dropdown and driver2_dropdown and driver1_dropdown != driver2_dropdown:
            st.markdown(f"#### Comparing {driver1_dropdown} vs {driver2_dropdown}")
            
            driver_comparison_fig = driver_comparison_chart(
                session_data, 
                driver1=driver1_dropdown, 
                driver2=driver2_dropdown,
                driver1_lap=lap_driver1,
                driver2_lap=lap_driver2
            )
            st.plotly_chart(driver_comparison_fig)
        else:
            st.error("Please select two different drivers to compare.")
            
    with tab3:
        if st.session_state.session_data is not None:
            weather_data = session_data.weather_data
            if weather_data is not None and not weather_data.empty:
                columns_to_plot = weather_data.drop(columns=['Time'])
                options = st.selectbox("Select the column to plot", columns_to_plot.columns, index=None)
                
                # Plotting the weather data
                st.markdown("#### Weather Chart")
                weather_fig = weather_analysis_chart(weather_data, options)
                
                st.plotly_chart(weather_fig, use_container_width=True)
            else:
                st.warning("No weather data available for this session.")
            
pg = st.navigation([
    st.Page(home, title="Home", default=True),
    st.Page("circuits.py", title="Circuits")])
pg.run()