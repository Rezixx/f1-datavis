import streamlit as st

from app.data_loader import (
    get_circuits_geojson
    )

from app.viz import (
    build_aggrid_table,
    visualize_circuit_geometry
)

#|-------------- Circuit Page Content --------------|
#
#     Create the circuits exploration page with interactive table and map visualization.
# 
#     This page provides an interface for exploring Formula 1 circuit information
#     through a sortable/filterable table and interactive map visualization.
#     Users can click on any circuit row to view its geographical layout.
#
t3_col1, t3_col2 = st.columns([0.6, 0.4])
# Left column: Circuits data table
with t3_col1:
    st.header("📅Table of Circuits")
    circuits_df = get_circuits_geojson()
    display_data = circuits_df.drop(columns=['geometry'])
    
    # Create interactive AgGrid table with selection capability
    grid_response = build_aggrid_table(display_data)

# Right column: Map visualization
with t3_col2:    
    # Check if a row is selected
    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
        # Extract selected circuit information
        circuit_name = grid_response['selected_rows']['Name']
        
        # Get geometry data for the selected circuit
        circuit_geometry = circuits_df[circuits_df['Name'] == circuit_name.iloc[0]]['geometry'].iloc[0]
                    
        # Call circuit visualization
        visualize_circuit_geometry(circuit_geometry, circuit_name.iloc[0])
    else:
        # Show instruction message when no circuit is selected
        st.header("")
        st.info("Click on a circuit row to visualize its geometry")