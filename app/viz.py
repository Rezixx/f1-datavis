import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
import folium
from streamlit_folium import st_folium

pd.set_option('future.no_silent_downcasting', True)

def format_lap_time(seconds):
    """Format lap time in MM:SS.mmm format for human-readable tooltips."""
    if pd.isna(seconds) or seconds <= 0:
        return "N/A"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{minutes:02}:{sec:02}.{millis:03}"

def format_timedelta_to_hms(td):
    """Format a timedelta object into an HH:MM:SS string."""
    if pd.isna(td):
        return "N/A"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def format_timedelta_to_ms(td):
    """Format a timedelta object into an MM:SS string."""
    if pd.isna(td):
        return "N/A"
    minutes = td.components.minutes
    seconds = td.components.seconds
    milliseconds = td.components.milliseconds
    return f"{minutes:02}:{seconds:02}:{milliseconds:03}"

def format_seconds_to_mmss(seconds):
    """Format seconds into MM:SS string for Y-axis tick labels."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"

# FastF1 official team colors for consistent branding
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
    'Haas F1 Team': '#B6BABD',
    'Racing Bulls': '#6692FF',
    'Kick Sauber': '#52C832'
}

# Backup colors if team not found in official colors
FALLBACK_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#F4D03F'
]

# F1 tire compound colors
COMPOUND_COLORS = {
    "SOFT": "#FF3333",      # Red
    "MEDIUM": "#FFFF00",    # Yellow  
    "HARD": "#FFFFFF",      # White
    "INTERMEDIATE": "#39FF14", # Green
    "WET": "#0080FF",       # Blue
    "Unknown": "#808080"    # Gray
}

# |--------- Lap Times Chart ---------|
def plot_lap_times(session, quick_load=False):
    """
    Create an interactive line chart showing lap time progression for all drivers throughout a session.
    
    This visualization displays how each driver's lap times evolve over the course of a session,
    allowing users to identify performance trends, consistency patterns, and strategic decisions.
    The chart uses official F1 team colors for authentic visual representation.
    
    Storytelling:
    This chart tells the story of a Formula 1 session through the lens of lap time performance.
    Each line represents a driver's journey through the session, revealing:
    - Performance evolution as cars burn fuel and tires degrade
    - Consistency differences between drivers and teams
    - Strategic pit stop timing (visible as time spikes)
    - Traffic impact and clear track opportunities
    - Weather condition effects on overall pace
    The visualization helps viewers understand the tactical battle beneath the surface of F1 racing.
    
    Args:
        session (fastf1.core.Session): Loaded F1 session object containing lap data
        quick_load (bool): If True, only shows quickest laps; if False, shows all valid laps
    
    Returns:
        plotly.graph_objects.Figure: Interactive lap times chart with hover tooltips and team colors
    """
    # Load session data if not already loaded
    if not hasattr(session, 'laps') or session.laps is None:
        session.load()
    
    # Get all laps data
    laps = session.laps
    

    if quick_load:
        # Only quick laps to show relevant laps
        valid_laps = laps.pick_quicklaps()
    else:
        # Filter out invalid lap times (NaN, too slow, or unrealistic times)
        valid_laps = laps[
            (laps['LapTime'].notna()) & 
            (laps['LapTime'] > pd.Timedelta(seconds=30)) & 
            (laps['LapTime'] < pd.Timedelta(seconds=300))
        ].copy()
    
    # Handle case where no valid laps exists
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
    valid_laps.loc[:, 'LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
    
    # Get unique drivers
    drivers = valid_laps['Driver'].unique()
    
    # Create figure
    fig = go.Figure()
    
    # Plot each driver's lap times
    for i, driver in enumerate(drivers):
        driver_laps = valid_laps[valid_laps['Driver'] == driver].sort_values('LapNumber')
    
        if not driver_laps.empty:
            team = session.get_driver(driver)['TeamName']
            
            # Get color from FastF1 team colors or use fallback
            if team in TEAM_COLORS:
                color = TEAM_COLORS[team]
            else:
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
            
            # Add driver trace to the plot
            fig.add_trace(
                go.Scatter(
                    x=driver_laps['LapNumber'],
                    y=driver_laps['LapTimeSeconds'],
                    mode='lines+markers',
                    name=driver,
                    line=dict(color=color, width=2),
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

# |--------- Tire Strategy Chart ---------|
def plot_tire_strategy_chart(session):
    """
    Create a horizontal stacked bar chart visualizing tire compound strategies for all drivers.
    
    This chart displays each driver's tire strategy throughout the session, showing
    when they used different tire compounds and for how many laps. Each compound
    is color-coded according to FIA regulations.
    
    Storytelling:
    This visualization reveals the strategic chess game of Formula 1 tire management.
    Each horizontal bar tells a driver's tactical story:
    - Stint length decisions (longer stints vs. fresh tire advantage)
    - Compound choices based on track conditions and strategy
    - Pit stop timing coordination with team strategy
    - Risk vs. reward decisions in tire compound selection
    - Weather-related strategy adaptations (intermediate/wet compounds)
    The chart exposes how teams balance speed, durability, and strategic positioning.
    
    Args:
        session (fastf1.core.Session): Loaded F1 session object containing lap and stint data
    
    Returns:
        plotly.graph_objects.Figure: Horizontal stacked bar chart showing tire strategies
    """
    
    # Extract lap data and driver list
    laps = session.laps
    drivers = session.drivers
    
    # Convert driver numbers to abbreviations for cleaner display
    drivers = [session.get_driver(d)["Abbreviation"] for d in drivers]
    
    # Group laps by driver, stint, and compound to calculate stint lengths
    stints = laps[["Driver", "Stint", "Compound", "LapNumber"]].groupby(["Driver", "Stint", "Compound"]).count().reset_index().rename(columns={"LapNumber": "StintLength"})
    
    fig = go.Figure()
    
    # Create stacked bars for each driver's tire strategy
    for driver in drivers:
        driver_stints = stints.loc[stints["Driver"] == driver]
        
        previous_stint_end = 0  # Track stint lengths
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
                    base=max(previous_stint_end-1,0),   # stack horizontally
                    showlegend=False
                )
            )
            
            # Update previous stint end for next iteration
            previous_stint_end += row["StintLength"]       
            
    # Apply styling consistent with F1 theme         
    fig.update_layout(
        title=dict(
            text="Tire Strategy by Driver",
            x=0.4,
            font=dict(size=28, color='white', family='rounded-sans')
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

# |--------- Driver Comparison Chart ---------|
def driver_comparison_chart(session, driver1, driver2, driver1_lap, driver2_lap):
    """
    Create a comprehensive telemetry comparison chart between two drivers for specific laps.
    
    This multi-panel visualization compares detailed telemetry data (speed, throttle, brake, gear)
    between two drivers on selected laps, providing insights into driving techniques and performance differences.
    
    Storytelling:
    This chart reveals the intimate details of Formula 1 driving skill and pushing the edge.
    Through four synchronized telemetry panels, it tells the story of:
    - Driving style differences (aggressive vs. smooth inputs)
    - Braking point variations and late-braking opportunities
    - Throttle application techniques (early vs. late apex acceleration)
    - Gear selection strategies and shift point optimization
    - Corner-by-corner performance advantages and weaknesses
    The visualization exposes the tiny margins that separate F1 drivers at the very highest level.
    
    Args:
        session (fastf1.core.Session): Loaded F1 session object
        driver1 (str): First driver's name/abbreviation
        driver2 (str): Second driver's name/abbreviation  
        driver1_lap (int): Lap number for first driver analysis
        driver2_lap (int): Lap number for second driver analysis
    
    Returns:
        plotly.graph_objects.Figure: Multi-panel telemetry comparison chart
    """
    try:
        # Get lap data for both drivers
        lap_d1 = session.laps.pick_drivers(driver1).pick_laps(driver1_lap)
        lap_d2 = session.laps.pick_drivers(driver2).pick_laps(driver2_lap)
        
        # Format lap times for display
        laptime_d1 = format_timedelta_to_ms(lap_d1["LapTime"].iloc[0])
        laptime_d2 = format_timedelta_to_ms(lap_d2["LapTime"].iloc[0])

        # Get telemetry data
        tel1 = lap_d1.get_telemetry()
        tel2 = lap_d2.get_telemetry()
        
        # Convert brake boolean values to 0/1 for plotting
        tel1['Brake'] = tel1['Brake'].replace({True: 1, False: 0})
        tel2['Brake'] = tel2['Brake'].replace({True: 1, False: 0})
        
        color1 =  TEAM_COLORS.get(session.get_driver(driver1)['TeamName'], '#FF6B6B')  # Default to red if not found
        color2 =  TEAM_COLORS.get(session.get_driver(driver2)['TeamName'], '#4ECDC4')  # Default to teal if not found
                
        # Create 4 subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=(
                'Speed (km/h)', 'Throttle (%)',
                'Brake (%)', 'Gear'
            ),
            vertical_spacing=0.09,
            horizontal_spacing=1
        )
        
        # Subplot 1: Speed comparison
        fig.add_trace(
            go.Scatter(
                x=tel1['Distance'],
                y=tel1['Speed'],
                mode='lines',
                name=f"{driver1} - Lap {driver1_lap}",
                line=dict(color=color1, width=2),
                hovertemplate=f"{driver1}<br>Distance: %{{x:.0f}}m<br>Speed: %{{y:.0f}} km/h<extra></extra>"
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=tel2['Distance'],
                y=tel2['Speed'],
                mode='lines',
                name=f"{driver2} - Lap {driver2_lap}",
                line=dict(color=color2, width=2, dash='dot'),
                hovertemplate=f"{driver2}<br>Distance: %{{x:.0f}}m<br>Speed: %{{y:.0f}} km/h<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Subplot 2: Throttle comparison
        fig.add_trace(
            go.Scatter(
                x=tel1['Distance'],
                y=tel1['Throttle'],
                mode='lines',
                name=f"{driver1} Throttle",
                line=dict(color=color1, width=2),
                showlegend=False,
                hovertemplate=f"{driver1}<br>Distance: %{{x:.0f}}m<br>Throttle: %{{y:.0f}}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=tel2['Distance'],
                y=tel2['Throttle'],
                mode='lines',
                name=f"{driver2} Throttle",
                line=dict(color=color2, width=2, dash='dot'),
                showlegend=False,
                hovertemplate=f"{driver2}<br>Distance: %{{x:.2f}}m<br>Throttle: %{{y:.0f}}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        # Subplot 3: Brake comparison
        fig.add_trace(
            go.Scatter(
                x=tel1['Distance'],
                y=tel1['Brake'] * 100, # Convert to percentage
                mode='lines',
                name=f"{driver1} Brake",
                line=dict(color=color1, width=2),
                showlegend=False,
                hovertemplate=f"{driver1}<br>Distance: %{{x:.2f}}m<br>Brake: %{{y:.0f}}%<extra></extra>"
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=tel2['Distance'],
                y=tel2['Brake'] * 100,
                mode='lines',
                name=f"{driver2} Brake",
                line=dict(color=color2, width=2, dash='dot'),
                showlegend=False,
                hovertemplate=f"{driver2}<br>Distance: %{{x:.2f}}m<br>Brake: %{{y:.0f}}%<extra></extra>"
            ),
            row=3, col=1
        )
        
        # Subplot 4: Gear comparison
        fig.add_trace(
            go.Scatter(
                x=tel1['Distance'],
                y=tel1['nGear'],
                mode='lines',
                name=f"{driver1} Gear",
                line=dict(color=color1, width=2),
                showlegend=False,
                hovertemplate=f"{driver1}<br>Distance: %{{x:.0f}}m<br>Gear: %{{y:.0f}}<extra></extra>"
            ),
            row=4, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=tel2['Distance'],
                y=tel2['nGear'],
                mode='lines',
                name=f"{driver2} Gear",
                line=dict(color=color2, width=2, dash='dot'),
                showlegend=False,
                hovertemplate=f"{driver2}<br>Distance: %{{x:.0f}}m<br>Gear: %{{y:.0f}}<extra></extra>"
            ),
            row=4, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=f"<b>🏎️ Driver Comparison: {driver1} (Lap {driver1_lap}, {laptime_d1} ) vs {driver2} (Lap {driver2_lap}, {laptime_d2})</b>",
                x=0.1,
                font=dict(size=20, color='white', family='Arial Black')
            ),
            plot_bgcolor='#15151E',
            paper_bgcolor='#15151E',
            font=dict(color='white'),
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1,
                xanchor="center",
                x=0.91,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='white',
                borderwidth=1,
                font=dict(color='white', size=12)
            )
        )
        
        # Update axes for styling for all subplots
        for i in range(1, 5):
            for j in range(1, 3):
                fig.update_xaxes(
                    title_text="Distance (m)" if i == 4 else "",
                    showgrid=True,
                    gridcolor='#404040',
                    linecolor='white',
                    tickfont=dict(color='white'),
                    row=i, col=j
                )
                fig.update_yaxes(
                    showgrid=True,
                    gridcolor='#404040',
                    linecolor='white',
                    tickfont=dict(color='white'),
                    row=i, col=j
                )
        
        # Update specific y-axis ranges for better visualization
        fig.update_yaxes(range=[0, 100], row=2, col=2)  # Throttle
        fig.update_yaxes(range=[0, 100], row=3, col=1)  # Brake
        fig.update_yaxes(range=[1, 8], row=4, col=1)    # Gear
        
        return fig
        
    except Exception as e:
        # Return error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error creating comparison: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='white')
        )
        fig.update_layout(
            plot_bgcolor='#15151E',
            paper_bgcolor='#15151E',
            font=dict(color='white')
        )
        return fig

# |--------- Weather Analysis Chart ---------|
def weather_analysis_chart(weather_data, yaxis_column):
    """
    Create a time-series chart analyzing weather conditions during an F1 session.
    
    This visualization displays how weather parameters change throughout a session,
    providing insights into environmental factors that influence racing conditions and strategy.
    
    Storytelling:
    This chart reveals weather's crucial role as the 'invisible competitor' in Formula 1.
    The timeline tells the story of:
    - Changing track conditions affecting grip and tire strategy
    - Temperature variations influencing car setup and tire performance
    - Humidity and wind patterns affecting aerodynamic balance
    - Barometric pressure changes indicating approaching weather systems
    - Critical moments when weather shifts force strategic decisions
    Weather data often explains unexpected lap time variations and strategic choices that seem puzzling without context.
    
    Args:
        weather_data (pd.DataFrame): Weather data for the session with time-indexed measurements
        yaxis_column (str): Specific weather parameter to visualize
    
    Returns:
        plotly.graph_objects.Figure: Time-series weather analysis chart
    """
    
    if yaxis_column is not None:
        # Format time data for readable x-axis labels
        weather_data['TimeFormatted'] = weather_data['Time'].apply(format_timedelta_to_hms)
        fig = px.line(weather_data, x='TimeFormatted', y=yaxis_column, title=f"Weather Analysis - {yaxis_column}")
        
        # Apply consistent styling with other F1 charts
        fig.update_traces(line=dict(color='#4ECDC4', width=2.5))
        
        fig.update_layout(
            title=dict(
                text=f"<b>🌦️ Weather Analysis: {yaxis_column}</b>",
                x=0.4,
                font=dict(size=20, color='white', family='Arial Black')
            ),
            xaxis=dict(
                title="Time",
                showgrid=True,
                gridcolor='#404040',
                linecolor='white',
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                title=yaxis_column,
                showgrid=True,
                gridcolor='#404040',
                linecolor='white',
                tickfont=dict(color='white')
            ),
            plot_bgcolor='#15151E',
            paper_bgcolor='#15151E',
            font=dict(color='white'),
            height=600,
            hovermode='x unified'
        )
        
        return fig
    else:
        # Return empty figure if no column selected
        fig = go.Figure()
        fig.add_annotation(
            text="No weather data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='white')
        )
        fig.update_layout(
            plot_bgcolor='#15151E',
            paper_bgcolor='#15151E',
            font=dict(color='white')
        )
        return fig

def build_aggrid_table(data):
    """
    Create an interactive AgGrid table component for displaying F1 circuit data.
    
    This function configures and builds a sortable, filterable data table
    optimized for displaying circuit information with selectable rows for
    triggering detailed visualizations.
    
    Args:
        data (pd.DataFrame): Circuit data to display in tabular format
    
    Returns:
        AgGrid: Configured Streamlit AgGrid component with sorting, filtering, and selection capabilities
    """
    grid_options = {
        'defaultColDef': {
            'sortable': True,      # Enable column sorting
            'filter': True,        # Enable column filtering
            'resizable': True,     # Allow column resizing
            'wrapText': True,      # Wrap long text content
            'autoHeight': True     # Auto-adjust row heights
        },
        'columnDefs': [
            {'headerName': 'Name', 'field': 'Name', 'width': 200},
            {'headerName': 'Location', 'field': 'Location', 'width': 150},
            {'headerName': 'Country', 'field': 'Country', 'width': 150},
            {'headerName': 'Opened', 'field': 'opened', 'width': 100},
            {'headerName': 'First GP', 'field': 'firstgp', 'width': 100},
            {'headerName': 'Length (m)', 'field': 'length', 'width': 100},
            {'headerName': 'Altitude (m)', 'field': 'altitude', 'width': 100},
        ],
        'rowSelection': "single",
        "pagination": False,
        "suppressRowClickSelection": False
    }
    
    return AgGrid(
        data,
        height=800, 
        gridOptions=grid_options, 
        fit_columns_on_grid_load=True,
        selection_mode="single",
        use_checkbox=False,
        theme="fresh"
    )

# |--------- Circuit Visualization ---------|
def visualize_circuit_geometry(circuit_geometry, circuit_name):
    """
    Create an interactive map visualization of a Formula 1 circuit layout.
    
    This function generates a Folium map displaying the circuit's track geometry
    with geographical context, including start/finish line markers and proper
    map bounds fitting the circuit layout.
    
    Storytelling:
    This map visualization brings F1 circuits to life by showing their real-world context.
    Each circuit tells a geographical story:
    - Urban circuits threading through city streets (Monaco, Singapore)  
    - Purpose-built facilities in remote locations (Spa, Silverstone)
    - Elevation changes and natural terrain integration
    - Strategic corner sequences and straight sections
    - Proximity to local landmarks and infrastructure
    The map helps viewers understand why each circuit produces unique racing characteristics.
    
    Args:
        circuit_geometry (shapely.geometry): Circuit track geometry coordinates
        circuit_name (str): Name of the circuit for labeling and identification
    
    Returns:
        None: Displays the interactive map directly in Streamlit interface
    """
    if circuit_geometry and circuit_name:
        center_lat, center_lon = circuit_geometry.centroid.y, circuit_geometry.centroid.x
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')
        
        # Add circuit track geometry as red line overlay
        folium.GeoJson(
            circuit_geometry,
            name=circuit_name,
            style_function=lambda x: {'color': 'red', 'weight': 3, 'opacity': 0.8}
        ).add_to(m)
        
        # Mark start/finish line location
        start_finish_coords = [circuit_geometry.coords[0][1], circuit_geometry.coords[0][0]]
        folium.Marker(
            location=start_finish_coords,
            popup=f"Start/Finish: {circuit_name}",
            icon=folium.Icon(color='black', icon='flag')
        ).add_to(m)
        
        # Automatically fit map bounds to circuit geometry
        m.fit_bounds(folium.GeoJson(circuit_geometry).get_bounds())
        
        # Display map in Streamlit with circuit name header
        st.header(f"🗺️ Map of {circuit_name}")
        st_folium(m, width=800, height=800, returned_objects=[])