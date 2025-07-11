from streamlit_navigation_bar import st_navbar
import streamlit as st

from app.data_loader import (
    get_circuits_geojson
    )

from app.viz import (
    build_aggrid_table,
    visualize_circuit_geometry
)

#|-------------- Circuit Page Content --------------|
  
t3_col1, t3_col2 = st.columns([0.6, 0.4])
with t3_col1:
    st.header("📅Table of Circuits")
    circuits_df = get_circuits_geojson()
    display_data = circuits_df.drop(columns=['geometry'])
    
    # Use AgGrid instead of Great Table for click functionality
    grid_response = build_aggrid_table(display_data)
    
with t3_col2:    
    # Check if a row is selected
    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
        circuit_name = grid_response['selected_rows']['Name']
        
        circuit_geometry = circuits_df[circuits_df['Name'] == circuit_name.iloc[0]]['geometry'].iloc[0]
                    
        # Call circuit visualization
        visualize_circuit_geometry(circuit_geometry, circuit_name.iloc[0])
    else:
        st.header("")
        st.info("Click on a circuit row to visualize its geometry")