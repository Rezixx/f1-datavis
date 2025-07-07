import streamlit as st
import requests
import pandas as pd
import geopandas as gpd
import fastf1 as ff1

@st.cache_data(ttl=3600)
def load_session(year, circuit, session_type):
    """Load the F1 session data for a given year, circuit, and session type."""
    session = ff1.get_session(year, circuit, session_type)
    session.load()
    return session

@st.cache_data(ttl=3600)
def get_circuits_for_year(year):
    """Get circuits for a specific year using OpenF1 API."""
    try:
        url = f"https://api.openf1.org/v1/meetings?year={year}"
        response = requests.get(url)
        response.raise_for_status()
        
        meetings_data = response.json()
        
        if not meetings_data:
            return pd.DataFrame(columns=['name', 'circuit_short_name', 'location', 'country_name'])
        
        # Create DataFrame with circuit information
        circuits_df = pd.DataFrame(meetings_data)
        
        # Create a simplified structure similar to what Ergast provided
        circuits_df = circuits_df[['circuit_short_name', 'location', 'country_name', 'meeting_name']].copy()
        circuits_df = circuits_df.rename(columns={'circuit_short_name': 'name'})
        
        # Remove duplicates (same circuit can have multiple sessions)
        circuits_df = circuits_df.drop_duplicates(subset=['name']).reset_index(drop=True)
        
        return circuits_df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching circuits data: {e}")
        return pd.DataFrame(columns=['name', 'circuit_short_name', 'location', 'country_name'])
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame(columns=['name', 'circuit_short_name', 'location', 'country_name'])

@st.cache_data(ttl=3600)
def get_sessions_for_circuit_year(year, circuit_name):
    """Get available sessions for a specific circuit and year using OpenF1 API."""
    try:
        url = f"https://api.openf1.org/v1/sessions?year={year}&circuit_short_name={circuit_name}"
        response = requests.get(url)
        response.raise_for_status()
        
        sessions_data = response.json()
        
        if not sessions_data:
            return []
        
        # Extract unique session names
        session_names = list(set([session['session_name'] for session in sessions_data]))
        return sorted(session_names)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching sessions data: {e}")
        return []
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return []
    
def get_drivers_session(session):
    """Get the list of drivers from the session."""
    if session is None:
        return []
    
    driver_names = session.laps.pick_quicklaps().Driver.unique()
    return sorted(driver_names)

@st.cache_data(ttl=3600)
def get_circuit_geojson():
    """Get the GeoJSON data."""
    geo_circuits = gpd.read_file("https://raw.githubusercontent.com/bacinger/f1-circuits/refs/heads/master/f1-circuits.geojson")
    #circuit = geo_circuits[geo_circuits['name'] == circuit_name]
    #if not circuit.empty:
    #    return circuit.geometry.values[0]
    #return None
    return geo_circuits