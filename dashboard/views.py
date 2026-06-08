"""
Dashboard visualization views.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import folium_static
from config import PollutionConfig
from utils.risk import assess_risk_level


class DashboardViews:
    RISK_COLORS = {
        "good": "#28a745",
        "moderate": "#ffc107",
        "unhealthy_sensitive": "#fd7e14",
        "unhealthy": "#dc3545",
        "very_unhealthy": "#6f42c1",
        "hazardous": "#000000",
    }

    def __init__(self):
        self.config = PollutionConfig()

    def display_overview_metrics(self, df: pd.DataFrame, city: str):
        import streamlit as st

        st.header("📊 Overview Metrics")

        if df is None or df.empty:
            st.warning("No data available. Please generate sample data first.")
            return

        latest_data = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Current PM2.5",
                value=f"{latest_data['PM2.5']:.1f} µg/m³",
                delta=f"{df['PM2.5'].iloc[-1] - df['PM2.5'].iloc[-2]:.1f}"
                if len(df) > 1
                else 0,
            )

        with col2:
            st.metric(
                label="Current NO2",
                value=f"{latest_data['NO2']:.1f} ppb",
                delta=f"{df['NO2'].iloc[-1] - df['NO2'].iloc[-2]:.1f}"
                if len(df) > 1
                else 0,
            )

        with col3:
            st.metric(
                label="Air Quality Index",
                value=latest_data["risk_level"].title(),
                delta=None,
            )

        with col4:
            st.metric(
                label="Temperature",
                value=f"{latest_data['temperature']:.1f}°C",
                delta=None,
            )

        risk_level = latest_data["risk_level"]
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Current Risk Level: <span style="color: {self.RISK_COLORS.get(risk_level, '#666')}">{risk_level.upper()}</span></h4>
                <p>Based on WHO guidelines for PM2.5 and NO2 levels</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def display_pollution_trends(self, df: pd.DataFrame):
        import streamlit as st

        st.header("📈 Pollution Trends")

        if df is None or df.empty:
            st.warning("No data available for trends.")
            return

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("PM2.5 Trend", "NO2 Trend", "CO Trend", "SO2 Trend"),
            vertical_spacing=0.1,
        )

        fig.add_trace(
            go.Scatter(x=df["date"], y=df["PM2.5"], mode="lines+markers", name="PM2.5"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["NO2"], mode="lines+markers", name="NO2"),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["CO"], mode="lines+markers", name="CO"),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=df["date"], y=df["SO2"], mode="lines+markers", name="SO2"),
            row=2,
            col=2,
        )

        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    def display_weather_correlation(self, df: pd.DataFrame):
        import streamlit as st

        st.header("🌤️ Weather Correlation")

        if df is None or df.empty:
            st.warning("No data available for weather correlation.")
            return

        corr_df = df[["PM2.5", "NO2", "temperature", "humidity", "wind_speed", "pressure"]].corr()

        fig = px.imshow(
            corr_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Weather-Pollution Correlation Matrix",
        )
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.scatter(
                df, x="temperature", y="PM2.5", title="Temperature vs PM2.5", trendline="ols"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(df, x="humidity", y="NO2", title="Humidity vs NO2", trendline="ols")
            st.plotly_chart(fig, use_container_width=True)

    def display_geographic_visualization(self, df: pd.DataFrame, city: str):
        import streamlit as st

        st.header("🗺️ Geographic Visualization")

        if df is None or df.empty:
            st.warning("No data available for geographic visualization.")
            return

        from utils.data_generator import SampleDataGenerator

        data_generator = SampleDataGenerator()
        city_info = data_generator.cities.get(city, {})
        if not city_info:
            st.error("City information not found.")
            return

        m = folium.Map(
            location=[city_info["lat"], city_info["lon"]],
            zoom_start=10,
            tiles="OpenStreetMap",
        )

        for _, row in df.iterrows():
            color = self.RISK_COLORS.get(row["risk_level"], "gray")
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=8,
                popup=f"""
                    <b>Date:</b> {row['date']}<br>
                    <b>PM2.5:</b> {row['PM2.5']:.1f} µg/m³<br>
                    <b>NO2:</b> {row['NO2']:.1f} ppb<br>
                    <b>Risk:</b> {row['risk_level'].title()}<br>
                    <b>Temperature:</b> {row['temperature']:.1f}°C
                    """,
                color=color,
                fill=True,
                fillOpacity=0.7,
            ).add_to(m)

        folium.Marker(
            [city_info["lat"], city_info["lon"]],
            popup=f"<b>{city}</b><br>Center Point",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

        folium_static(m, width=800, height=500)

    def display_crop_burning_analysis(self, df: pd.DataFrame):
        import streamlit as st

        st.header("🔥 Crop Burning Impact Analysis")

        if df is None or df.empty:
            st.warning("No data available for crop burning analysis.")
            return

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                df, x="date", y="fire_count", title="Fire Count Over Time", markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.histogram(
                df, x="fire_intensity", title="Fire Intensity Distribution", nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)

        if "fire_count" in df.columns and "PM2.5" in df.columns:
            fig = px.scatter(
                df, x="fire_count", y="PM2.5", title="Fire Count vs PM2.5 Levels", trendline="ols"
            )
            st.plotly_chart(fig, use_container_width=True)

    def display_ml_predictions(self, df: pd.DataFrame, model_type: str, forecast_days: int):
        import streamlit as st

        st.header("🤖 Machine Learning Predictions")

        if df is None or df.empty:
            st.warning("No data available for ML predictions.")
            return

        try:
            from models.pollution_predictor import PollutionPredictor

            predictor = PollutionPredictor(model_type)
            features, _ = predictor.prepare_features(df.to_dict("records"))

            if features.size == 0:
                st.warning("Could not prepare features for ML model.")
                return

            with st.spinner("Training ML model..."):
                training_results = predictor.train_model(features, predictor.targets)

            if training_results:
                st.subheader("Model Training Results")
                col1, col2 = st.columns(2)

                with col1:
                    for pollutant, results in training_results.items():
                        st.metric(label=f"{pollutant} R² Score", value=f"{results['val_r2']:.3f}")

                with col2:
                    for pollutant, results in training_results.items():
                        st.metric(label=f"{pollutant} RMSE", value=f"{results['val_rmse']:.2f}")

                with st.spinner("Generating forecast..."):
                    forecast = predictor.forecast_pollution(features, forecast_days)

                if forecast:
                    st.subheader(f"{forecast_days}-Day Pollution Forecast")
                    forecast_df = pd.DataFrame.from_dict(forecast, orient="index")
                    forecast_df.index = pd.to_datetime(forecast_df.index)

                    fig = make_subplots(
                        rows=1,
                        cols=2,
                        subplot_titles=("PM2.5 Forecast", "NO2 Forecast"),
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_df.index,
                            y=forecast_df["PM2.5"],
                            mode="lines+markers",
                            name="PM2.5",
                        ),
                        row=1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=forecast_df.index,
                            y=forecast_df["NO2"],
                            mode="lines+markers",
                            name="NO2",
                        ),
                        row=1,
                        col=2,
                    )

                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Detailed Forecast")
                    st.dataframe(forecast_df)

        except Exception as e:
            st.error(f"Error in ML predictions: {e}")
