import streamlit as st
import requests
import pandas as pd
import geopandas as gpd
import fastf1 as ff1

@st.cache_data(ttl=3600)
def load_session(year, circuit, session_type):
    """
    Load Formula 1 session data for a given year, circuit, and session type.
    
    This function retrieves and loads F1 session data using the FastF1 library,
    providing access to lap times, telemetry, weather data, and other session-specific information.
    
    Args:
        year (int): The F1 season year (e.g., 2023, 2024)
        circuit (str): Circuit name or short name (e.g., 'Monza', 'Silverstone')
        session_type (str): Type of session ('Practice 1', 'Practice 2', 'Practice 3', 'Qualifying', 'Race', 'Sprint', 'Sprint Qualifying', 'Sprint Shootout')
    
    Returns:
        fastf1.core.Session: Loaded F1 session object containing all session data
    
    Raises:
        Exception: If the session cannot be loaded or data is unavailable
    """
    session = ff1.get_session(year, circuit, session_type)
    session.load()
    return session

@st.cache_data(ttl=3600)
def get_circuits_for_year(year):
    """
    Retrieve all driven Formula 1 circuits for a specific season year.
    
    This function fetches circuit information from the OpenF1 API, providing
    details about all circuits that hosted F1 events in the specified year.
    
    Args:
        year (int): The F1 season year to get circuits for
    
    Returns:
        pd.DataFrame: DataFrame containing circuit information with columns:
            - name: Circuit short name
            - location: Circuit location/city
            - country_name: Country where circuit is located
            - meeting_name: Official event name
    
    Raises:
        requests.exceptions.RequestException: If API request fails
    """
    try:
        url = f"https://api.openf1.org/v1/meetings?year={year}"
        response = requests.get(url)
        response.raise_for_status()
        
        meetings_data = response.json()
        
        if not meetings_data:
            return pd.DataFrame(columns=['name', 'circuit_short_name', 'location', 'country_name'])
        
        # Create DataFrame with circuit information
        circuits_df = pd.DataFrame(meetings_data)
        
        # Create a simplified structure
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
    """
    Get all available session types for a specific circuit and year combination.
    
    This function retrieves the different session types (Practice, Qualifying, Race, Sprint, etc.)
    that were held at a particular circuit during a specific F1 season.
    
    Args:
        year (int): The F1 season year
        circuit_name (str): Short name of the circuit
    
    Returns:
        list: Sorted list of available session names for the circuit and year
    
    Raises:
        requests.exceptions.RequestException: If API request fails
    """
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
    
@st.cache_data(ttl=3600)
def get_drivers_session(_session):
    """
    Extract and return a sorted list of driver names from a loaded F1 session.
    
    This function processes the session's lap data to identify all drivers
    who participated and recorded valid lap times during the session.
    
    Args:
        session (fastf1.core.Session): Loaded F1 session object
    
    Returns:
        list: Sorted list of driver names (3-letter abbreviations or full names)
              Returns empty list if session is None or contains no valid data
    """
    if _session is None:
        return []
    
    # Get all unique drivers who recorded quick laps
    driver_names = _session.laps.pick_quicklaps().Driver.unique()
    return sorted(driver_names)

@st.cache_data(ttl=3600)
def get_circuits_geojson():
    """
    Retrieve Formula 1 circuit geographical data with track layouts and metadata.
    
    This function fetches GeoJSON data containing the geographical coordinates
    and track layouts of F1 circuits, along with additional metadata such as
    country information, opening dates, and track specifications.
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing circuit geometries and metadata with columns:
            - Name: Circuit name
            - Location: Circuit location/city  
            - Country: Country where circuit is located
            - opened: Year circuit opened
            - firstgp: Year of first Grand Prix
            - length: Track length in meters
            - altitude: Circuit altitude in meters
            - geometry: Track layout coordinates
    
    Raises:
        requests.exceptions.RequestException: If download fails
    """
    url = "https://raw.githubusercontent.com/bacinger/f1-circuits/refs/heads/master/f1-circuits.geojson"
    try:
        # Use requests to fetch the content
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        
        # Read the content from the response text
        geo_circuits = gpd.read_file(response.text)
        geo_circuits.drop(columns=['id'], inplace=True)
        # Add country information based on circuit names
        geo_circuits["Country"] = [
                                    'Australia',
                                    'Bahrain',
                                    'China',
                                    'Azerbaijan',
                                    'Spain',
                                    'Monaco',
                                    'Canada',
                                    'France',
                                    'Austria',
                                    'United Kingdom',
                                    'Germany',
                                    'Hungary',
                                    'Belgium',
                                    'Italy',
                                    'Singapore',
                                    'Russia',
                                    'Japan',
                                    'United States',
                                    'Mexico',
                                    'Brazil',
                                    'United Arab Emirates',
                                    'Italy',
                                    'Germany',
                                    'Portugal',
                                    'Italy',
                                    'Malaysia',
                                    'Turkey',
                                    'Netherlands',
                                    'France',
                                    'Portugal',
                                    'Brazil',
                                    'Saudi Arabia',
                                    'United States',
                                    'Qatar',
                                    'United States',
                                    'Spain'
                                ]
        return geo_circuits
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to download circuit data: {e}")
        return gpd.GeoDataFrame() # Return an empty GeoDataFrame on error