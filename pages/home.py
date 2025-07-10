import streamlit as st
from app.data_loader import (
    get_drivers_session
)
from app.viz import (
    plot_lap_times,
    plot_tire_strategy_chart,
    driver_comparison_chart
)

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
