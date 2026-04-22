"""
Flask API Server for Pollution Detection System
Provides REST API endpoints for data access and analysis
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Import custom modules
from config import PollutionConfig
from data_processing.satellite_data import SatelliteDataProcessor
from models.pollution_predictor import PollutionPredictor
from utils.data_generator import SampleDataGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
config = PollutionConfig()
config.create_directories()

# Initialize components
satellite_processor = SatelliteDataProcessor()
data_generator = SampleDataGenerator()

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Pollution Detection System API',
        'version': '1.0.0',
        'endpoints': {
            'GET /': 'API information',
            'GET /health': 'Health check',
            'GET /cities': 'List available cities',
            'GET /data/<city>': 'Get pollution data for a city',
            'POST /data/generate': 'Generate sample data',
            'GET /satellite/<city>': 'Get satellite data for a city',
            'POST /predict': 'Make pollution predictions',
            'GET /forecast/<city>': 'Get pollution forecast',
            'GET /analysis/<city>': 'Get analysis results',
            'GET /export/<city>': 'Export data as GeoJSON'
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'config_valid': config.validate_config()
    })

@app.route('/cities')
def get_cities():
    """Get list of available cities"""
    try:
        cities = []
        for city, info in data_generator.cities.items():
            cities.append({
                'name': city,
                'country': info['country'],
                'latitude': info['lat'],
                'longitude': info['lon']
            })
        
        return jsonify({
            'cities': cities,
            'total': len(cities)
        })
    except Exception as e:
        logger.error(f"Error getting cities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/data/<city>')
def get_pollution_data(city: str):
    """Get pollution data for a specific city"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        format_type = request.args.get('format', 'json')
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Check if data file exists
        data_file = os.path.join(config.DATA_DIR, f'{city}_pollution_data.json')
        
        if not os.path.exists(data_file):
            return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404
        
        # Load data
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame for filtering
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by days if specified
        if days and days < len(df):
            end_date = df['date'].max()
            start_date = end_date - timedelta(days=days)
            df = df[df['date'] >= start_date]
        
        # Convert back to list
        filtered_data = df.to_dict('records')
        
        # Return in requested format
        if format_type == 'csv':
            # Convert to CSV
            csv_data = df.to_csv(index=False)
            return csv_data, 200, {'Content-Type': 'text/csv'}
        else:
            return jsonify({
                'city': city,
                'data': filtered_data,
                'total_records': len(filtered_data),
                'date_range': {
                    'start': df['date'].min().isoformat() if not df.empty else None,
                    'end': df['date'].max().isoformat() if not df.empty else None
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting pollution data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/data/generate', methods=['POST'])
def generate_sample_data():
    """Generate sample data for a city"""
    try:
        data = request.get_json()
        city = data.get('city', 'Delhi')
        days = data.get('days', 30)
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 400
        
        # Generate data
        files = data_generator.save_sample_data(city, days)
        
        if files:
            return jsonify({
                'message': f'Sample data generated for {city}',
                'files': files,
                'city': city,
                'days': days
            })
        else:
            return jsonify({'error': 'Failed to generate data'}), 500
            
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/satellite/<city>')
def get_satellite_data(city: str):
    """Get satellite data for a city"""
    try:
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Get city coordinates
        city_info = data_generator.cities[city]
        area = {
            'north': city_info['lat'] + 0.5,
            'south': city_info['lat'] - 0.5,
            'east': city_info['lon'] + 0.5,
            'west': city_info['lon'] - 0.5
        }
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate satellite data
        satellite_data = data_generator.generate_satellite_data(
            area, start_date, end_date, num_samples=days//2
        )
        
        return jsonify({
            'city': city,
            'area': area,
            'satellite_data': satellite_data,
            'total_records': len(satellite_data),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting satellite data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def make_predictions():
    """Make pollution predictions using ML models"""
    try:
        data = request.get_json()
        city = data.get('city', 'Delhi')
        model_type = data.get('model_type', 'random_forest')
        forecast_days = data.get('forecast_days', 7)
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 400
        
        # Load data
        data_file = os.path.join(config.DATA_DIR, f'{city}_pollution_data.json')
        if not os.path.exists(data_file):
            return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404
        
        with open(data_file, 'r') as f:
            pollution_data = json.load(f)
        
        # Initialize predictor
        predictor = PollutionPredictor(model_type)
        
        # Prepare features
        features, targets = predictor.prepare_features(pollution_data)
        
        if features.size == 0:
            return jsonify({'error': 'Could not prepare features for ML model'}), 400
        
        # Train model
        training_results = predictor.train_model(features, targets)
        
        if not training_results:
            return jsonify({'error': 'Failed to train model'}), 500
        
        # Make forecast
        forecast = predictor.forecast_pollution(features, forecast_days)
        
        return jsonify({
            'city': city,
            'model_type': model_type,
            'training_results': training_results,
            'forecast': forecast,
            'forecast_days': forecast_days
        })
        
    except Exception as e:
        logger.error(f"Error making predictions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/forecast/<city>')
def get_forecast(city: str):
    """Get pollution forecast for a city"""
    try:
        # Get query parameters
        model_type = request.args.get('model_type', 'random_forest')
        forecast_days = request.args.get('forecast_days', 7, type=int)
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Load data
        data_file = os.path.join(config.DATA_DIR, f'{city}_pollution_data.json')
        if not os.path.exists(data_file):
            return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404
        
        with open(data_file, 'r') as f:
            pollution_data = json.load(f)
        
        # Initialize predictor
        predictor = PollutionPredictor(model_type)
        
        # Prepare features
        features, targets = predictor.prepare_features(pollution_data)
        
        if features.size == 0:
            return jsonify({'error': 'Could not prepare features for ML model'}), 400
        
        # Train model
        training_results = predictor.train_model(features, targets)
        
        if not training_results:
            return jsonify({'error': 'Failed to train model'}), 500
        
        # Make forecast
        forecast = predictor.forecast_pollution(features, forecast_days)
        
        return jsonify({
            'city': city,
            'model_type': model_type,
            'forecast': forecast,
            'forecast_days': forecast_days,
            'model_performance': training_results
        })
        
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<city>')
def get_analysis(city: str):
    """Get comprehensive analysis results for a city"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Load data
        data_file = os.path.join(config.DATA_DIR, f'{city}_pollution_data.json')
        if not os.path.exists(data_file):
            return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404
        
        with open(data_file, 'r') as f:
            pollution_data = json.load(f)
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(pollution_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by days if specified
        if days and days < len(df):
            end_date = df['date'].max()
            start_date = end_date - timedelta(days=days)
            df = df[df['date'] >= start_date]
        
        # Calculate statistics
        analysis_results = {
            'city': city,
            'total_records': len(df),
            'date_range': {
                'start': df['date'].min().isoformat() if not df.empty else None,
                'end': df['date'].max().isoformat() if not df.empty else None
            },
            'pollution_statistics': {
                'PM2.5': {
                    'mean': float(df['PM2.5'].mean()) if not df.empty else 0,
                    'max': float(df['PM2.5'].max()) if not df.empty else 0,
                    'min': float(df['PM2.5'].min()) if not df.empty else 0,
                    'std': float(df['PM2.5'].std()) if not df.empty else 0
                },
                'NO2': {
                    'mean': float(df['NO2'].mean()) if not df.empty else 0,
                    'max': float(df['NO2'].max()) if not df.empty else 0,
                    'min': float(df['NO2'].min()) if not df.empty else 0,
                    'std': float(df['NO2'].std()) if not df.empty else 0
                }
            },
            'weather_statistics': {
                'temperature': {
                    'mean': float(df['temperature'].mean()) if not df.empty else 0,
                    'max': float(df['temperature'].max()) if not df.empty else 0,
                    'min': float(df['temperature'].min()) if not df.empty else 0
                },
                'humidity': {
                    'mean': float(df['humidity'].mean()) if not df.empty else 0,
                    'max': float(df['humidity'].max()) if not df.empty else 0,
                    'min': float(df['humidity'].min()) if not df.empty else 0
                }
            },
            'risk_level_distribution': df['risk_level'].value_counts().to_dict() if not df.empty else {},
            'fire_statistics': {
                'total_fires': int(df['fire_count'].sum()) if not df.empty else 0,
                'avg_fires_per_day': float(df['fire_count'].mean()) if not df.empty else 0,
                'max_fires_in_day': int(df['fire_count'].max()) if not df.empty else 0
            }
        }
        
        # Add temporal analysis if enough data
        if len(df) >= 7:
            # Calculate rolling statistics for anomaly detection
            df['PM2.5_rolling_mean'] = df['PM2.5'].rolling(window=7).mean()
            df['PM2.5_rolling_std'] = df['PM2.5'].rolling(window=7).std()
            df['NO2_rolling_mean'] = df['NO2'].rolling(window=7).mean()
            df['NO2_rolling_std'] = df['NO2'].rolling(window=7).std()
            
            # Detect anomalies
            df['PM2.5_anomaly'] = np.abs(df['PM2.5'] - df['PM2.5_rolling_mean']) > 2 * df['PM2.5_rolling_std']
            df['NO2_anomaly'] = np.abs(df['NO2'] - df['NO2_rolling_mean']) > 2 * df['NO2_rolling_std']
            
            analysis_results['anomaly_analysis'] = {
                'PM2.5_anomalies': int(df['PM2.5_anomaly'].sum()),
                'NO2_anomalies': int(df['NO2_anomaly'].sum()),
                'total_anomalies': int((df['PM2.5_anomaly'] | df['NO2_anomaly']).sum())
            }
        
        return jsonify(analysis_results)
        
    except Exception as e:
        logger.error(f"Error getting analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export/<city>')
def export_data(city: str):
    """Export data as GeoJSON"""
    try:
        # Get query parameters
        format_type = request.args.get('format', 'geojson')
        
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Check if GeoJSON file exists
        geojson_file = os.path.join(config.DATA_DIR, f'{city}_pollution_data.geojson')
        
        if not os.path.exists(geojson_file):
            return jsonify({'error': f'No GeoJSON data available for {city}. Generate data first.'}), 404
        
        # Return file
        return send_file(geojson_file, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/crop-burning/<city>')
def get_crop_burning_analysis(city: str):
    """Get crop burning impact analysis for a city"""
    try:
        # Validate city
        if city not in data_generator.cities:
            return jsonify({'error': f'City {city} not found'}), 404
        
        # Get city coordinates
        city_info = data_generator.cities[city]
        area = {
            'north': city_info['lat'] + 0.5,
            'south': city_info['lat'] - 0.5,
            'east': city_info['lon'] + 0.5,
            'west': city_info['lon'] - 0.5
        }
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Generate fire data
        fire_data = data_generator.generate_satellite_data(
            area, start_date, end_date, num_samples=days//2
        )
        
        # Process crop burning data
        crop_burning_analysis = satellite_processor.process_crop_burning_data(
            fire_data[0] if fire_data else {}, area, days
        )
        
        return jsonify({
            'city': city,
            'area': area,
            'crop_burning_analysis': crop_burning_analysis,
            'fire_data': fire_data,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting crop burning analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Validate configuration
    if not config.validate_config():
        logger.warning("Some API keys are missing. Some features may not work.")
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )
