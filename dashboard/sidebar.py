"""
Dashboard sidebar controls.
"""

import streamlit as st
from datetime import datetime, timedelta


def render_sidebar(dashboard):
    st.sidebar.title("🎛️ Dashboard Controls")

    cities = list(dashboard.data_generator.cities.keys())
    selected_city = st.sidebar.selectbox(
        "Select City",
        cities,
        index=cities.index(st.session_state.current_city),
    )

    if selected_city != st.session_state.current_city:
        st.session_state.current_city = selected_city
        st.session_state.data_loaded = False
        st.experimental_rerun()

    st.sidebar.subheader("📅 Date Range")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(start_date.date(), end_date.date()),
        max_value=end_date.date(),
    )

    st.sidebar.subheader("📊 Data Management")
    if st.sidebar.button("🔄 Generate Sample Data"):
        with st.spinner("Generating sample data..."):
            files = dashboard.data_generator.save_sample_data(
                selected_city,
                days=(date_range[1] - date_range[0]).days,
            )
            if files:
                st.session_state.data_loaded = True
                st.success(f"Sample data generated for {selected_city}")
                st.experimental_rerun()

    st.sidebar.subheader("🤖 ML Model")
    model_type = st.sidebar.selectbox(
        "Select Model Type",
        ["random_forest", "xgboost", "gradient_boosting", "linear"],
        index=0,
    )

    st.sidebar.subheader("🔮 Forecast Settings")
    forecast_days = st.sidebar.slider("Forecast Days", 1, 14, 7)

    return {
        "city": selected_city,
        "date_range": date_range,
        "model_type": model_type,
        "forecast_days": forecast_days,
    }
