"""
Main Streamlit Dashboard for Pollution Detection System
Interactive GIS dashboard for monitoring air and water pollution
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import folium_static
import json
import os
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import Point
import logging

# Import custom modules
from config import PollutionConfig
from data_processing.satellite_data import SatelliteDataProcessor
from models.pollution_predictor import PollutionPredictor
from utils.data_generator import SampleDataGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Pollution Detection System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-good { color: #28a745; }
    .risk-moderate { color: #ffc107; }
    .risk-unhealthy { color: #fd7e14; }
    .risk-hazardous { color: #dc3545; }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

class PollutionDashboard:
    """Main dashboard class for pollution monitoring"""
    
    def __init__(self):
        self.config = PollutionConfig()
        self.config.create_directories()
        self.satellite_processor = SatelliteDataProcessor()
        self.data_generator = SampleDataGenerator()
        
        # Initialize session state
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_city' not in st.session_state:
            st.session_state.current_city = 'Delhi'
    
    def main_header(self):
        """Display main header"""
        st.markdown('<h1 class="main-header">🌍 Pollution Detection System</h1>', unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <p style='font-size: 1.2rem; color: #666;'>
                Real-time monitoring of air and water pollution using GIS and Satellite Imagery
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def sidebar_controls(self):
        """Create sidebar controls"""
        st.sidebar.title("🎛️ Dashboard Controls")
        
        # City selection
        cities = list(self.data_generator.cities.keys())
        selected_city = st.sidebar.selectbox(
            "Select City",
            cities,
            index=cities.index(st.session_state.current_city)
        )
        
        if selected_city != st.session_state.current_city:
            st.session_state.current_city = selected_city
            st.session_state.data_loaded = False
            st.experimental_rerun()
        
        # Date range selection
        st.sidebar.subheader("📅 Date Range")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(start_date.date(), end_date.date()),
            max_value=end_date.date()
        )
        
        # Data generation
        st.sidebar.subheader("📊 Data Management")
        if st.sidebar.button("🔄 Generate Sample Data"):
            with st.spinner("Generating sample data..."):
                files = self.data_generator.save_sample_data(
                    selected_city, 
                    days=(date_range[1] - date_range[0]).days
                )
                if files:
                    st.session_state.data_loaded = True
                    st.success(f"Sample data generated for {selected_city}")
                    st.experimental_rerun()
        
        # Model selection
        st.sidebar.subheader("🤖 ML Model")
        model_type = st.sidebar.selectbox(
            "Select Model Type",
            ['random_forest', 'xgboost', 'gradient_boosting', 'linear'],
            index=0
        )
        
        # Forecast settings
        st.sidebar.subheader("🔮 Forecast Settings")
        forecast_days = st.sidebar.slider("Forecast Days", 1, 14, 7)
        
        return {
            'city': selected_city,
            'date_range': date_range,
            'model_type': model_type,
            'forecast_days': forecast_days
        }
    
    def load_data(self, city: str, date_range: tuple):
        """Load pollution data for the selected city"""
        try:
            data_file = os.path.join(self.config.DATA_DIR, f'{city}_pollution_data.json')
            
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                
                # Filter by date range
                start_date = pd.to_datetime(date_range[0])
                end_date = pd.to_datetime(date_range[1])
                df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                
                return df
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
    
    def display_overview_metrics(self, df: pd.DataFrame, city: str):
        """Display overview metrics"""
        st.header("📊 Overview Metrics")
        
        if df is None or df.empty:
            st.warning("No data available. Please generate sample data first.")
            return
        
        # Calculate metrics
        latest_data = df.iloc[-1] if not df.empty else None
        
        # Create metric columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Current PM2.5",
                value=f"{latest_data['PM2.5']:.1f} µg/m³",
                delta=f"{df['PM2.5'].iloc[-1] - df['PM2.5'].iloc[-2]:.1f}" if len(df) > 1 else 0
            )
        
        with col2:
            st.metric(
                label="Current NO2",
                value=f"{latest_data['NO2']:.1f} ppb",
                delta=f"{df['NO2'].iloc[-1] - df['NO2'].iloc[-2]:.1f}" if len(df) > 1 else 0
            )
        
        with col3:
            st.metric(
                label="Air Quality Index",
                value=latest_data['risk_level'].title(),
                delta=None
            )
        
        with col4:
            st.metric(
                label="Temperature",
                value=f"{latest_data['temperature']:.1f}°C",
                delta=None
            )
        
        # Risk level indicator
        risk_level = latest_data['risk_level']
        risk_colors = {
            'good': '#28a745',
            'moderate': '#ffc107',
            'unhealthy_sensitive': '#fd7e14',
            'unhealthy': '#dc3545',
            'very_unhealthy': '#6f42c1',
            'hazardous': '#000000'
        }
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>Current Risk Level: <span style="color: {risk_colors.get(risk_level, '#666')}">{risk_level.upper()}</span></h4>
            <p>Based on WHO guidelines for PM2.5 and NO2 levels</p>
        </div>
        """, unsafe_allow_html=True)
    
    def display_pollution_trends(self, df: pd.DataFrame):
        """Display pollution trends over time"""
        st.header("📈 Pollution Trends")
        
        if df is None or df.empty:
            st.warning("No data available for trends.")
            return
        
        # Create subplots for different pollutants
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('PM2.5 Trend', 'NO2 Trend', 'CO Trend', 'SO2 Trend'),
            vertical_spacing=0.1
        )
        
        # PM2.5 trend
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['PM2.5'], mode='lines+markers', name='PM2.5'),
            row=1, col=1
        )
        
        # NO2 trend
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['NO2'], mode='lines+markers', name='NO2'),
            row=1, col=2
        )
        
        # CO trend
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['CO'], mode='lines+markers', name='CO'),
            row=2, col=1
        )
        
        # SO2 trend
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['SO2'], mode='lines+markers', name='SO2'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    def display_weather_correlation(self, df: pd.DataFrame):
        """Display weather correlation with pollution"""
        st.header("🌤️ Weather Correlation")
        
        if df is None or df.empty:
            st.warning("No data available for weather correlation.")
            return
        
        # Create correlation matrix
        weather_pollution = df[['PM2.5', 'NO2', 'temperature', 'humidity', 'wind_speed', 'pressure']]
        correlation_matrix = weather_pollution.corr()
        
        # Plot correlation heatmap
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu_r',
            title="Weather-Pollution Correlation Matrix"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plots
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(
                df, x='temperature', y='PM2.5',
                title='Temperature vs PM2.5',
                trendline='ols'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                df, x='humidity', y='NO2',
                title='Humidity vs NO2',
                trendline='ols'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def display_geographic_visualization(self, df: pd.DataFrame, city: str):
        """Display geographic visualization"""
        st.header("🗺️ Geographic Visualization")
        
        if df is None or df.empty:
            st.warning("No data available for geographic visualization.")
            return
        
        # Get city coordinates
        city_info = self.data_generator.cities.get(city, {})
        if not city_info:
            st.error("City information not found.")
            return
        
        # Create map
        m = folium.Map(
            location=[city_info['lat'], city_info['lon']],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add pollution data points
        for _, row in df.iterrows():
            # Color based on risk level
            risk_colors = {
                'good': 'green',
                'moderate': 'yellow',
                'unhealthy_sensitive': 'orange',
                'unhealthy': 'red',
                'very_unhealthy': 'purple',
                'hazardous': 'black'
            }
            
            color = risk_colors.get(row['risk_level'], 'gray')
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
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
                fillOpacity=0.7
            ).add_to(m)
        
        # Add city marker
        folium.Marker(
            [city_info['lat'], city_info['lon']],
            popup=f"<b>{city}</b><br>Center Point",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Display map
        folium_static(m, width=800, height=500)
    
    def display_crop_burning_analysis(self, df: pd.DataFrame):
        """Display crop burning impact analysis"""
        st.header("🔥 Crop Burning Impact Analysis")
        
        if df is None or df.empty:
            st.warning("No data available for crop burning analysis.")
            return
        
        # Analyze fire patterns
        col1, col2 = st.columns(2)
        
        with col1:
            # Fire count over time
            fig = px.line(
                df, x='date', y='fire_count',
                title='Fire Count Over Time',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Fire intensity distribution
            fig = px.histogram(
                df, x='fire_intensity',
                title='Fire Intensity Distribution',
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation with pollution
        if 'fire_count' in df.columns and 'PM2.5' in df.columns:
            fig = px.scatter(
                df, x='fire_count', y='PM2.5',
                title='Fire Count vs PM2.5 Levels',
                trendline='ols'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def display_ml_predictions(self, df: pd.DataFrame, model_type: str, forecast_days: int):
        """Display machine learning predictions"""
        st.header("🤖 Machine Learning Predictions")
        
        if df is None or df.empty:
            st.warning("No data available for ML predictions.")
            return
        
        try:
            # Initialize predictor
            predictor = PollutionPredictor(model_type)
            
            # Prepare features
            features, targets = predictor.prepare_features(df.to_dict('records'))
            
            if features.size == 0:
                st.warning("Could not prepare features for ML model.")
                return
            
            # Train model
            with st.spinner("Training ML model..."):
                training_results = predictor.train_model(features, targets)
            
            if training_results:
                # Display training results
                st.subheader("Model Training Results")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for pollutant, results in training_results.items():
                        st.metric(
                            label=f"{pollutant} R² Score",
                            value=f"{results['val_r2']:.3f}"
                        )
                
                with col2:
                    for pollutant, results in training_results.items():
                        st.metric(
                            label=f"{pollutant} RMSE",
                            value=f"{results['val_rmse']:.2f}"
                        )
                
                # Make forecast
                with st.spinner("Generating forecast..."):
                    forecast = predictor.forecast_pollution(features, forecast_days)
                
                if forecast:
                    st.subheader(f"{forecast_days}-Day Pollution Forecast")
                    
                    # Convert forecast to DataFrame
                    forecast_df = pd.DataFrame.from_dict(forecast, orient='index')
                    forecast_df.index = pd.to_datetime(forecast_df.index)
                    
                    # Plot forecast
                    fig = make_subplots(
                        rows=1, cols=2,
                        subplot_titles=('PM2.5 Forecast', 'NO2 Forecast')
                    )
                    
                    fig.add_trace(
                        go.Scatter(x=forecast_df.index, y=forecast_df['PM2.5'], 
                                 mode='lines+markers', name='PM2.5'),
                        row=1, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(x=forecast_df.index, y=forecast_df['NO2'], 
                                 mode='lines+markers', name='NO2'),
                        row=1, col=2
                    )
                    
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display forecast table
                    st.subheader("Detailed Forecast")
                    st.dataframe(forecast_df)
                    
        except Exception as e:
            st.error(f"Error in ML predictions: {e}")
            logger.error(f"ML prediction error: {e}")
    
    def display_anomaly_detection(self, df: pd.DataFrame):
        """Display temporal anomaly detection"""
        st.header("🚨 Anomaly Detection")
        
        if df is None or df.empty:
            st.warning("No data available for anomaly detection.")
            return
        
        # Simple anomaly detection using rolling statistics
        window_size = 7
        
        if len(df) >= window_size:
            # Calculate rolling mean and std
            df['PM2.5_rolling_mean'] = df['PM2.5'].rolling(window=window_size).mean()
            df['PM2.5_rolling_std'] = df['PM2.5'].rolling(window=window_size).std()
            df['NO2_rolling_mean'] = df['NO2'].rolling(window=window_size).mean()
            df['NO2_rolling_std'] = df['NO2'].rolling(window=window_size).std()
            
            # Detect anomalies (values > 2 standard deviations from rolling mean)
            df['PM2.5_anomaly'] = np.abs(df['PM2.5'] - df['PM2.5_rolling_mean']) > 2 * df['PM2.5_rolling_std']
            df['NO2_anomaly'] = np.abs(df['NO2'] - df['NO2_rolling_mean']) > 2 * df['NO2_rolling_std']
            
            # Plot anomalies
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('PM2.5 with Anomalies', 'NO2 with Anomalies'),
                vertical_spacing=0.1
            )
            
            # PM2.5 plot
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['PM2.5'], mode='lines', name='PM2.5', line=dict(color='blue')),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['PM2.5_rolling_mean'], mode='lines', 
                          name='Rolling Mean', line=dict(color='red', dash='dash')),
                row=1, col=1
            )
            
            # Highlight anomalies
            anomalies_pm25 = df[df['PM2.5_anomaly']]
            if not anomalies_pm25.empty:
                fig.add_trace(
                    go.Scatter(x=anomalies_pm25['date'], y=anomalies_pm25['PM2.5'], 
                              mode='markers', name='PM2.5 Anomalies',
                              marker=dict(color='red', size=10, symbol='x')),
                    row=1, col=1
                )
            
            # NO2 plot
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['NO2'], mode='lines', name='NO2', line=dict(color='green')),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['NO2_rolling_mean'], mode='lines', 
                          name='Rolling Mean', line=dict(color='red', dash='dash')),
                row=2, col=1
            )
            
            # Highlight anomalies
            anomalies_no2 = df[df['NO2_anomaly']]
            if not anomalies_no2.empty:
                fig.add_trace(
                    go.Scatter(x=anomalies_no2['date'], y=anomalies_no2['NO2'], 
                              mode='markers', name='NO2 Anomalies',
                              marker=dict(color='red', size=10, symbol='x')),
                    row=2, col=1
                )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display anomaly summary
            st.subheader("Anomaly Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("PM2.5 Anomalies", len(anomalies_pm25))
            
            with col2:
                st.metric("NO2 Anomalies", len(anomalies_no2))
            
            if not anomalies_pm25.empty or not anomalies_no2.empty:
                st.subheader("Anomaly Details")
                st.write("Dates with detected anomalies:")
                
                all_anomalies = []
                for _, row in df.iterrows():
                    if row['PM2.5_anomaly'] or row['NO2_anomaly']:
                        all_anomalies.append({
                            'Date': row['date'].strftime('%Y-%m-%d'),
                            'PM2.5': f"{row['PM2.5']:.1f} µg/m³",
                            'NO2': f"{row['NO2']:.1f} ppb",
                            'PM2.5 Anomaly': 'Yes' if row['PM2.5_anomaly'] else 'No',
                            'NO2 Anomaly': 'Yes' if row['NO2_anomaly'] else 'No'
                        })
                
                if all_anomalies:
                    anomaly_df = pd.DataFrame(all_anomalies)
                    st.dataframe(anomaly_df)
        else:
            st.warning("Need at least 7 days of data for anomaly detection.")
    
    def run(self):
        """Run the main dashboard"""
        # Main header
        self.main_header()
        
        # Sidebar controls
        controls = self.sidebar_controls()
        
        # Load data
        df = self.load_data(controls['city'], controls['date_range'])
        
        # Main content
        if df is not None and not df.empty:
            # Overview metrics
            self.display_overview_metrics(df, controls['city'])
            
            # Create tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📈 Trends", "🌤️ Weather", "🗺️ Geography", "🔥 Crop Burning", "🤖 ML Predictions", "🚨 Anomalies"
            ])
            
            with tab1:
                self.display_pollution_trends(df)
            
            with tab2:
                self.display_weather_correlation(df)
            
            with tab3:
                self.display_geographic_visualization(df, controls['city'])
            
            with tab4:
                self.display_crop_burning_analysis(df)
            
            with tab5:
                self.display_ml_predictions(df, controls['model_type'], controls['forecast_days'])
            
            with tab6:
                self.display_anomaly_detection(df)
        else:
            st.info("👆 Please generate sample data using the sidebar controls to start monitoring pollution levels.")
            
            # Show sample data structure
            st.subheader("📋 Sample Data Structure")
            st.markdown("""
            The system generates sample data with the following pollutants and parameters:
            
            **Air Pollutants:**
            - PM2.5 (Particulate Matter ≤2.5 µm)
            - NO2 (Nitrogen Dioxide)
            - CO (Carbon Monoxide)
            - SO2 (Sulfur Dioxide)
            - O3 (Ozone)
            
            **Weather Parameters:**
            - Temperature
            - Humidity
            - Wind Speed
            - Atmospheric Pressure
            
            **Environmental Factors:**
            - Fire Count (Crop Burning)
            - Fire Intensity
            - Land Cover Type
            
            **Risk Assessment:**
            - Based on WHO guidelines
            - Real-time risk level calculation
            - Historical trend analysis
            """)

# Run the dashboard
if __name__ == "__main__":
    dashboard = PollutionDashboard()
    dashboard.run()
