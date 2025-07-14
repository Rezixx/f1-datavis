import streamlit as st
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

# Setup session states variables
if 'session_data' not in st.session_state:
    st.session_state.session_data = None
if 'show_quick_laps' not in st.session_state:
    st.session_state.show_quick_laps = False  # Default to quick laps
if 'circuit_dropdown' not in st.session_state:
    st.session_state.circuit_dropdown = None


# Initialize FastF1 cache
if os.path.exists('cache'):
    ff1.Cache.enable_cache('cache')

# Configure Streamlit page layout and theme
st.set_page_config(page_title="🏎️🏁F1 Paddock App", layout="wide", initial_sidebar_state="expanded")

def setup_sidebar():
    """
    Configure and populate the application sidebar with F1 data selection controls.
    
    This function creates a hierarchical selection interface allowing users to:
    1. Select an F1 season year
    2. Choose a circuit from that year's calendar
    3. Pick a specific session type (Practice, Qualifying, Race)
    4. Load and display session metadata
    
    The function maintains session state and provides user feedback through
    success messages, warnings, and metric displays.
    
    Returns:
        None: Configures sidebar interface and updates session state
    """
    circuit_dropdown = None
    # Custom HTML/CSS for the banner
    custom_html = '''
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
    '''
    # Display the custom HTML
    st.components.v1.html(custom_html)
    
    with st.sidebar:
        st.title("🏎️🏁F1 Paddock App")
        year_dropdown = st.selectbox("Select Year", [2023, 2024, 2025], index=None)
        
        # Circuit selection (depends on year selection)
        if year_dropdown is not None:
            circuits = get_circuits_for_year(year_dropdown)
            if not circuits.empty:
                circuit_dropdown = st.selectbox("Select Circuit", circuits['name'].tolist(), index=None)
                st.session_state.circuit_dropdown = circuit_dropdown  # Store in session state
                
                # Session selection
                if circuit_dropdown is not None:
                    # Get available sessions for this circuit and year
                    available_sessions = get_sessions_for_circuit_year(year_dropdown, circuit_dropdown)
                    if available_sessions:
                        session_type = st.selectbox("Select Session Type", available_sessions, index=None)
                        
                        # Load session data when all selections are made
                        if session_type is not None:
                            st.session_state.session_data = load_session(year_dropdown, circuit_dropdown, session_type)
                            session_data = st.session_state.session_data
                            st.success(f"Session loaded successfully!")
                            
                            # Display session metadata as metrics
                            if circuit_dropdown is not None: 
                                st.metric("Circuit", circuit_dropdown)
                            if session_data is not None:
                                st.metric("Total Laps", str(session_data.total_laps))
                                session_date = session_data.date
                                st.metric("Session Date", f"{session_date:%d.%m.%Y}")
                                st.metric("Session Time", f"{session_date:%H:%M}")
                    else:
                        st.warning("No sessions available for this circuit and year combination.")
            else:
                st.warning("No circuits found for the selected year.")
      
setup_sidebar()

#|-------------- Main App Content --------------|   
def home():
    """
    Main application interface containing the primary F1 data visualization dashboard.
    
    This function creates a tabbed interface with three main sections:
    1. General Dashboard - Overall session analysis with lap times and tire strategies
    2. Driver Analysis - Detailed telemetry comparison between selected drivers
    3. Weather Analysis - Environmental conditions throughout the session
    
    Each tab provides interactive visualizations and controls for exploring
    different aspects of Formula 1 session data.
    
    Returns:
        None: Renders the main dashboard interface in Streamlit
    """
    st.title("🏎️🏁F1 Paddock App")
    st.text("Feel Racing. Explore Racing. Visualize Racing.")   
        
    tab1, tab2, tab3 = st.tabs(["General Dashboard", "Driver Analysis", "Weather Analysis"])
    session_data = st.session_state.session_data
    
    # Tab 1: General Dashboard with lap times and tire strategies
    with tab1:
        if 'session_data' in locals() and session_data is not None:
            # Display either only quick laps or all laps based on user selection
            if st.session_state.show_quick_laps:
                st.markdown("#### ⚡ Quick Laps Analysis")
                lap_times_fig = plot_lap_times(session_data, quick_load=True)
            else:
                st.markdown("#### 🏁 All Laps Analysis")
                lap_times_fig = plot_lap_times(session_data, quick_load=False)
                
            # Lap times visualization section
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
                st.info(
                    "**What to look for:**\n"
                    "*   **Fastest Laps: Which driver set the fastes lap time of the session?\n"
                    "*   **Trends:** Do lap times generally get faster as fuel burns off?\n"
                    "*   **Consistency:** Which drivers have the most consistent lap times?\n"
                    "*   **Anomalies:** Sudden slow laps can indicate a pit stop, a mistake, or traffic."
                )
                st.plotly_chart(lap_times_fig, use_container_width=True)
                
            # Tire strategy visualization section
            with st.expander("Tire Strategy Chart", expanded=True):  
                tire_strat_fig = plot_tire_strategy_chart(session_data)
                st.info(
                    '**What to look for:**\n'
                    '*   **Stint Length:** Compare how long drivers stay on each tire compound\n'
                    '*   **Strategy Variety:** Different teams may choose contrasting approaches\n'
                    '*   **Compound Choices:** Hard tires for durability vs soft tires for speed\n'
                    '*   **Pit Windows:** Clustered pit stops indicate strategic timing\n'
                    '*   **Weather Adaptation:** Green/blue bars show rain tire usage'
                )
                st.plotly_chart(tire_strat_fig, use_container_width=True) 
                
                     
    # Tab 2: Driver Analysis with telemetry comparison
    with tab2:
        st.header("Driver Analysis")
        
        d_col1, d_col2 = st.columns(2)
        
        # Driver 1 selection and lap picker
        with d_col1:
            driver1_dropdown = st.selectbox(
                "Select Driver 1",
                get_drivers_session(session_data), 
                index = None
                )
            if driver1_dropdown is not None:
                # Lap selection slider for Driver 1
                lap_driver1 = st.select_slider(
                    options=session_data.laps.pick_drivers(driver1_dropdown)["LapNumber"].to_list(),
                    label="Select Lap Number for Driver 1",
                    value = session_data.laps.pick_drivers(driver1_dropdown).pick_fastest()["LapNumber"])
        
        # Driver 2 selection and lap picker
        with d_col2:
            driver2_dropdown = st.selectbox(
                "Select Driver 2",
                get_drivers_session(session_data),
                index = None
                )
            if driver2_dropdown is not None:
                # Lap selection slider for Driver 2
                lap_driver2 = st.select_slider(
                    options=session_data.laps.pick_drivers(driver1_dropdown)["LapNumber"].to_list(),
                    label="Select Lap Number for Driver 2",
                    value = session_data.laps.pick_drivers(driver2_dropdown).pick_fastest()["LapNumber"])
                
        # Generate comparison chart only when both drivers are selected
        if driver1_dropdown and driver2_dropdown and driver1_dropdown != driver2_dropdown:
            st.markdown(f"#### Comparing {driver1_dropdown} vs {driver2_dropdown}")
            
            driver_comparison_fig = driver_comparison_chart(
                session_data, 
                driver1=driver1_dropdown, 
                driver2=driver2_dropdown,
                driver1_lap=lap_driver1,
                driver2_lap=lap_driver2
            )
            st.info(
                '**What to look for:**\n'
                '*   **Speed Differences:** Where does one driver gain/lose time on track?\n'
                '*   **Braking Points:** Earlier braking may indicate caution or different lines\n'
                '*   **Throttle Application:** Smooth vs aggressive acceleration out of corners\n'
                '*   **Gear Selection:** Optimal shift points and gear usage through corners\n'
                '*   **Driving Style:** Consistent patterns reveal each driver\'s technique\n'
                '*   **Sector Analysis:** Which parts of the lap favor each driver?'
            )
            st.plotly_chart(driver_comparison_fig)
            
        else:
            st.error("Please select two different drivers to compare.")
    
    # Tab 3: Weather Analysis     
    with tab3:
        if st.session_state.session_data is not None:
            weather_data = session_data.weather_data
            
            # Check if weather data is available
            if weather_data is not None and not weather_data.empty:
                # Create dropdown for weather parameter selection
                columns_to_plot = weather_data.drop(columns=['Time', 'WindDirection'])
                options = st.selectbox("Select the column to plot", columns_to_plot.columns, index=None)
                
                # Plotting the weather data
                st.markdown("#### Weather Chart")
                weather_fig = weather_analysis_chart(weather_data, options)
                st.info(
                    '**What to look for:**\n'
                    '*   **Temperature Changes:** Track/air temp affects tire performance and grip\n'
                    '*   **Humidity Patterns:** Higher humidity can indicate approaching rain\n'
                    '*   **Pressure Trends:** Dropping pressure often signals weather changes\n'
                    '*   **Wind Speed:** Affects aerodynamics and driver confidence\n'
                    '*   **Rainfall:** Explains sudden lap time changes and strategy shifts\n'
                    '*   **Critical Moments:** Weather spikes that forced strategic decisions'
                )
                st.plotly_chart(weather_fig, use_container_width=True)
                
            else:
                st.warning("No weather data available for this session.")

# Configure navigation between pages
pg = st.navigation([
    st.Page(home, title="Home", default=True),
    st.Page("circuits.py", title="Circuits")])
pg.run()