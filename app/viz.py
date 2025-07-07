import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import fastf1 as ff1
import numpy as np
import requests

def format_lap_time(seconds):
    """Format lap time in MM:SS.mmm format for human-readable tooltips."""
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{minutes:02}:{sec:02}.{millis:03}"

def format_seconds_to_mmss(seconds):
    """Format seconds into MM:SS string for Y-axis tick labels."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"

# FastF1 official team colors (2024 season)
TEAM_COLORS = {
    'Red Bull Racing': '#3671C6',
    'Mercedes': '#27F4D2', 
    'Ferrari': '#E8002D',
    'McLaren': '#FF8000',
    'Aston Martin': '#229971',
    'Alpine': '#0093CC',
    'Williams': '#64C4FF',
    'AlphaTauri': '#5E8FAA',
    'Alfa Romeo': '#B12039',
    'Haas': '#B6BABD',
    'RB': '#6692FF',
    'Kick Sauber': '#52C832'
}

# Backup colors if team not found
FALLBACK_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#F4D03F'
]

# Lap Time Chart
def plot_lap_times(session, quick_load=False):
    """
    Plot lap times for all drivers throughout the session.
    
    Args:
        session: FastF1 session object
    
    Returns:
        plotly.graph_objects.Figure: Interactive lap times chart
    """
    # Load session data if not already loaded
    if not hasattr(session, 'laps') or session.laps is None:
        session.load()
    
    # Get all laps data
    laps = session.laps
    
    if quick_load:
        valid_laps = laps.pick_quicklaps()
    else:
        # Filter out invalid lap times (NaN, 0, or extremely slow laps > 300 seconds)
        valid_laps = laps[
            (laps['LapTime'].notna()) & 
            (laps['LapTime'] > pd.Timedelta(seconds=30)) & 
            (laps['LapTime'] < pd.Timedelta(seconds=300))
        ].copy()
        
    if valid_laps.empty:
        # Return empty figure if no valid laps
        fig = go.Figure()
        fig.add_annotation(
            text="No valid lap time data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            plot_bgcolor='#15151E',
            paper_bgcolor='#15151E'
        )
        return fig
    
    
    
    # Convert LapTime to seconds for plotting
    valid_laps['LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
    
    # Get unique drivers
    drivers = valid_laps['Driver'].unique()
    
    # Create figure
    fig = go.Figure()
    
    # Define colors for drivers (you can customize this)
    colors = px.colors.qualitative.Set3
    
    # Plot each driver's lap times
    for i, driver in enumerate(drivers):
        driver_laps = valid_laps[valid_laps['Driver'] == driver].sort_values('LapNumber')
        
        if not driver_laps.empty:
            team = driver_laps['Team'].iloc[0] if 'Team' in driver_laps.columns else None
            
            # Get color from FastF1 team colors or use fallback
            if team and team in TEAM_COLORS:
                color = TEAM_COLORS[team]
            else:
                # Try to get FastF1 color if available
                try:
                    color = ff1.plotting.team_color(team) if team else FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
                except:
                    color = FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
            
            # Create hover text with formatted lap times
            hover_text = [
                f"Driver: {driver}<br>" +
                f"Team: {team if team else 'Unknown'}<br>" +
                f"Lap: {lap_num:.0f}<br>" +
                f"Time: {format_lap_time(lap_time)}<br>" +
                f"Compound: {compound if pd.notna(compound) else 'Unknown'}"
                for lap_num, lap_time, compound in zip(
                    driver_laps['LapNumber'],
                    driver_laps['LapTimeSeconds'],
                    driver_laps['Compound']
                )
            ]
            
            fig.add_trace(
                go.Scatter(
                    x=driver_laps['LapNumber'],
                    y=driver_laps['LapTimeSeconds'],
                    mode='lines+markers',
                    name=driver,
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4),
                    hovertemplate='%{hovertext}<extra></extra>',
                    hovertext=hover_text
                )
            )
    
    # Calculate y-axis range with some padding
    min_time = valid_laps['LapTimeSeconds'].min()
    max_time = valid_laps['LapTimeSeconds'].max()
    time_range = max_time - min_time
    y_min = max(0, min_time - time_range * 0.05)
    y_max = max_time + time_range * 0.05
    
    # Create custom tick values for better readability
    tick_interval = max(1, int(time_range / 10))
    tick_vals = list(range(int(y_min), int(y_max) + 1, tick_interval))
    tick_text = [format_seconds_to_mmss(t) for t in tick_vals]
    
    # Update layout with F1 styling
    fig.update_layout(
        title=dict(
            text=f"<b>🏎️ {session.event['EventName']} - {session.name}</b><br><span style='font-size:14px'></span>",
            x=0.38,
            font=dict(size=24, color='white', family='Arial Black')
        ),
        xaxis=dict(
            title=dict(text="<b>Lap Number</b>", font=dict(size=14, color='white')),
            showgrid=True,
            gridcolor='#404040',
            gridwidth=1,
            tickfont=dict(color='white', size=12),
            linecolor='white',
            mirror=True
        ),
        yaxis=dict(
            title=dict(text="<b>Lap Time</b>", font=dict(size=14, color='white')),
            showgrid=True,
            gridcolor='#404040',
            gridwidth=1,
            tickfont=dict(color='white', size=12),
            tickvals=tick_vals,
            ticktext=tick_text,
            linecolor='white',
            mirror=True,
            range=[y_min, y_max]
        ),
        legend=dict(
            title=dict(text="<b>Drivers</b>", font=dict(color='white', size=14)),
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='white',
            borderwidth=1,
            font=dict(color='white', size=11)
        ),
        hovermode='closest',
        plot_bgcolor='#15151E',  # F1 dark background
        paper_bgcolor='#15151E',
        font=dict(color='white'),
        height=650,
        margin=dict(r=120, t=80, b=60, l=60),
        hoverlabel=dict(
            bgcolor='rgba(0,0,0,0.8)',
            bordercolor='white',
            font_size=12,
            font_color='white'
        )
    )
    
    # Add F1 branding watermark
    fig.add_annotation(
        text="FastF1 Data",
        xref="paper", yref="paper",
        x=0.99, y=0.01,
        showarrow=False,
        font=dict(size=10, color='#666666'),
        opacity=0.7
    )
    
    return fig

def plot_tire_strategy_chart(session):
    """
    Plot tire strategy chart for all drivers in the session.
    """
    
    laps = session.laps
    drivers = session.drivers
    
    drivers = [session.get_driver(d)["Abbreviation"] for d in drivers]
    
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].groupby(["Driver", "Stint", "Compound"]).count().reset_index().rename(columns={"LapNumber": "StintLength"})
    
    fig = go.Figure()
    
    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]
        
        previous_stint_end = 0
        for _, row in driver_stints.iterrows():
            compound_color = COMPOUND_COLORS.get(row["Compound"])
            
            fig.add_trace(
                go.Bar(
                    x=[row["StintLength"]],
                    y=[driver],
                    orientation='h',
                    name="",
                    marker=dict(
                        color=compound_color,
                        line=dict(color='black', width=1)
                        ),
                    hovertemplate=(
                        f"{driver}<br>"
                        f"Stint: {row['Stint']:.0f}<br>"
                        f"Compound: {row['Compound']}<br>"
                        f"Length: {row['StintLength']} laps<extra></extra>"
                    ),
                    base=max(previous_stint_end-1,0),
                    showlegend=False
                )
            )
            
            previous_stint_end += row["StintLength"]       
            
            
    fig.update_layout(
        title=dict(
            text="Tire Strategy by Driver",
            x=0.4,
            font=dict(size=24, color='white', family='Arial Black')
            ),
        xaxis_title = "Lap Number",
        yaxis_title = "",
        barmode= "stack",
        plot_bgcolor='#15151E',  # F1 dark background
        paper_bgcolor='#15151E',
        yaxis=dict(autorange="reversed"),
        height=800,
        )
    
    fig.update_yaxes(color='white', tickfont=dict(color='white', size=12))
    
    return fig

# Tire Strategy Chart with F1 compound colors
COMPOUND_COLORS = {
    "SOFT": "#FF3333",      # Red
    "MEDIUM": "#FFFF00",    # Yellow  
    "HARD": "#FFFFFF",      # White
    "INTERMEDIATE": "#39FF14", # Green
    "WET": "#0080FF",       # Blue
    "Unknown": "#808080"    # Gray
}

def get_elevation_data(coordinates, samples=50):
    """Get elevation data for circuit coordinates using Open Elevation API"""
    try:
        # Sample coordinates to avoid API limits
        if len(coordinates) > samples:
            indices = np.linspace(0, len(coordinates)-1, samples, dtype=int)
            sampled_coords = [coordinates[i] for i in indices]
        else:
            sampled_coords = coordinates
        
        # Prepare coordinates for API
        locations = []
        for coord in sampled_coords:
            if len(coord) >= 2:
                locations.append({"latitude": coord[1], "longitude": coord[0]})
        
        if not locations:
            return []
        
        # Call Open Elevation API
        response = requests.post(
            'https://api.open-elevation.com/api/v1/lookup',
            json={'locations': locations},
            timeout=30
        )
        
        if response.status_code == 200:
            elevations = response.json()['results']
            return [result['elevation'] for result in elevations]
        else:
            # Fallback to simulated elevation
            return np.random.uniform(0, 100, len(locations)).tolist()
            
    except Exception as e:
        st.warning(f"Could not fetch elevation data: {e}. Using simulated data.")
        return np.random.uniform(0, 100, len(coordinates)).tolist()

def create_3d_circuit_visualization(circuit_name, geo_data, session_data=None):
    """Create 3D visualization of circuit with terrain"""
    
    # Find the circuit in geo data
    circuit_geo = None
    for feature in geo_data['Location']:
        if feature == circuit_name:
            circuit_geo = feature
            break
    
    if not circuit_geo:
        return None
    
    # Extract coordinates
    coordinates = circuit_geo['geometry'][0]
    
    # Get elevation data
    elevations = get_elevation_data(coordinates)
    
    # Interpolate to create smooth circuit path
    if len(coordinates) != len(elevations):
        # Match lengths
        min_len = min(len(coordinates), len(elevations))
        coordinates = coordinates[:min_len]
        elevations = elevations[:min_len]
    
    # Extract lat, lon, elevation
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    
    # Create terrain surface around circuit
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    
    # Expand area for terrain
    terrain_lats = np.linspace(min(lats) - lat_range*0.1, max(lats) + lat_range*0.1, 30)
    terrain_lons = np.linspace(min(lons) - lon_range*0.1, max(lons) + lon_range*0.1, 30)
    
    terrain_lons_mesh, terrain_lats_mesh = np.meshgrid(terrain_lons, terrain_lats)
    
    # Simple terrain elevation (you could use real DEM data here)
    terrain_elevations = np.random.uniform(
        min(elevations) - 50, 
        max(elevations) + 50, 
        terrain_lons_mesh.shape
    )
    
    # Create the 3D plot
    fig = go.Figure()
    
    # Add terrain surface
    fig.add_trace(go.Surface(
        x=terrain_lons_mesh,
        y=terrain_lats_mesh,
        z=terrain_elevations,
        colorscale='Earth',
        showscale=False,
        opacity=0.7,
        name='Terrain'
    ))
    
    # Add circuit path
    fig.add_trace(go.Scatter3d(
        x=lons + [lons[0]],  # Close the loop
        y=lats + [lats[0]],
        z=[e + 10 for e in elevations] + [elevations[0] + 10],  # Elevate above terrain
        mode='lines+markers',
        line=dict(color='red', width=8),
        marker=dict(size=3, color='red'),
        name='Circuit Track'
    ))
    
    # Add start/finish line
    fig.add_trace(go.Scatter3d(
        x=[lons[0]],
        y=[lats[0]],
        z=[elevations[0] + 20],
        mode='markers',
        marker=dict(size=10, color='green', symbol='diamond'),
        name='Start/Finish'
    ))
    
    # Update layout for 3D
    fig.update_layout(
        title=f"3D Circuit Visualization - {circuit_name}",
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude", 
            zaxis_title="Elevation (m)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.3),
            bgcolor='#15151E'
        ),
        height=600,
        showlegend=True,
        paper_bgcolor='#15151E',
        font=dict(color='white')
    )
    
    return fig

def create_circuit_flythrough_animation(circuit_name, geo_data):
    """Create animated flythrough of the circuit"""
    
    # Find the circuit in geo data
    circuit_geo = None
    for feature in geo_data['features']:
        if feature['properties']['name'] == circuit_name:
            circuit_geo = feature
            break
    
    if not circuit_geo:
        return None
    
    coordinates = circuit_geo['geometry']['coordinates'][0]
    elevations = get_elevation_data(coordinates)
    
    if len(coordinates) != len(elevations):
        min_len = min(len(coordinates), len(elevations))
        coordinates = coordinates[:min_len]
        elevations = elevations[:min_len]
    
    lons = [coord[0] for coord in coordinates]
    lats = [coord[1] for coord in coordinates]
    
    # Create frames for animation
    frames = []
    n_frames = 50
    
    for i in range(n_frames):
        # Calculate camera position following the track
        track_progress = i / n_frames
        coord_idx = int(track_progress * (len(coordinates) - 1))
        
        # Camera follows the track
        camera_x = lons[coord_idx]
        camera_y = lats[coord_idx] 
        camera_z = elevations[coord_idx] + 100  # Above the track
        
        # Look ahead on the track
        look_ahead_idx = min(coord_idx + 3, len(coordinates) - 1)
        center_x = lons[look_ahead_idx]
        center_y = lats[look_ahead_idx]
        center_z = elevations[look_ahead_idx]
        
        frame = go.Frame(
            data=[
                go.Scatter3d(
                    x=lons + [lons[0]],
                    y=lats + [lats[0]], 
                    z=[e + 10 for e in elevations] + [elevations[0] + 10],
                    mode='lines+markers',
                    line=dict(color='red', width=8),
                    marker=dict(size=3, color='red'),
                    name='Circuit Track'
                )
            ],
            layout=go.Layout(
                scene_camera=dict(
                    eye=dict(
                        x=camera_x,
                        y=camera_y,
                        z=camera_z
                    ),
                    center=dict(
                        x=center_x,
                        y=center_y, 
                        z=center_z
                    )
                )
            )
        )
        frames.append(frame)
    
    # Create base figure
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=lons + [lons[0]],
                y=lats + [lats[0]],
                z=[e + 10 for e in elevations] + [elevations[0] + 10],
                mode='lines+markers',
                line=dict(color='red', width=8),
                marker=dict(size=3, color='red'),
                name='Circuit Track'
            )
        ],
        frames=frames
    )
    
    fig.update_layout(
        title=f"Circuit Flythrough - {circuit_name}",
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            zaxis_title="Elevation (m)",
            aspectmode='manual',
            aspectratio=dict(x=1, y=1, z=0.3),
            bgcolor='#15151E'
        ),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None, {'frame': {'duration': 200}, 'transition': {'duration': 100}}]
                },
                {
                    'label': 'Pause',
                    'method': 'animate',
                    'args': [[None], {'frame': {'duration': 0}, 'mode': 'immediate'}]
                }
            ]
        }],
        height=600,
        paper_bgcolor='#15151E',
        font=dict(color='white')
    )
    
    return fig