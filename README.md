# Pollution Detection using GIS + Satellite Imagery

A comprehensive system for monitoring air and water pollution using Sentinel-5P, MODIS, and GIS data to predict pollution levels and forecast risk zones.

## Features

- **Satellite Data Integration**: Sentinel-5P and MODIS data processing
- **Pollution Prediction**: PM2.5 and NO2 level forecasting
- **GIS Analysis**: Spatial analysis and risk zone mapping
- **Crop Burning Impact**: Modeling agricultural burning effects
- **Temporal Anomaly Detection**: Time-series analysis for unusual patterns
- **Interactive Dashboard**: Visual GIS dashboard for policymakers
- **Real-time Monitoring**: Live data updates and alerts

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pollution-detection-system
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
# Streamlit Dashboard
streamlit run app.py

# Flask API
python api.py

# Jupyter Notebooks
jupyter notebook notebooks/
```

## Project Structure

```
pollution-detection-system/
├── app.py                 # Main Streamlit dashboard
├── api.py                 # Flask API server
├── config.py              # Configuration settings
├── data_processing/       # Data processing modules
├── models/                # ML models and training
├── notebooks/             # Jupyter notebooks for analysis
├── static/                # Static assets
├── templates/             # HTML templates
├── utils/                 # Utility functions
└── requirements.txt       # Python dependencies
```

## API Keys Required

- **NASA Earth Data**: For MODIS data access
- **Copernicus Open Access Hub**: For Sentinel data
- **OpenWeatherMap**: For weather data
- **Google Earth Engine**: For additional satellite data

## Usage

1. **Dashboard**: Access the main dashboard at `http://localhost:8501`
2. **API**: Use the REST API at `http://localhost:5000`
3. **Analysis**: Run Jupyter notebooks for detailed analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
