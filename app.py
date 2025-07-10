import streamlit as st
import fastf1 as ff1
import os
from streamlit_navigation_bar import st_navbar
import pages as pg

from app.data_loader import (
    load_session,
    get_circuits_for_year,
    get_sessions_for_circuit_year
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

page = st_navbar(['Home', 'Circuits'])

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

if page == 'Home':
    pg.home()
elif page == 'Circuits':
    pg.circuits()