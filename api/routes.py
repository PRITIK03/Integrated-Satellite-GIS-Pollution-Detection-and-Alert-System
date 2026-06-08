"""
API Routes Module - Modular Flask endpoints.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
from flask import Blueprint, request, jsonify, send_file

from config import PollutionConfig
from data_processing.satellite_data import SatelliteDataProcessor
from models.pollution_predictor import PollutionPredictor
from utils.data_generator import SampleDataGenerator

logger = logging.getLogger(__name__)


def _get_config() -> PollutionConfig:
    return PollutionConfig()


def _get_generator() -> SampleDataGenerator:
    return SampleDataGenerator()


def _load_city_dataframe(city: str, config: PollutionConfig):
    path = os.path.join(config.DATA_DIR, f'{city}_pollution_data.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def _apply_window(df: pd.DataFrame, window: int) -> pd.DataFrame:
    if window and window < len(df):
        end = df['date'].max()
        df = df[df['date'] >= end - timedelta(days=window)].copy()
    return df


def _area_for_city(city_info: Dict[str, float]) -> Dict[str, float]:
    lat, lon = city_info['lat'], city_info['lon']
    return {
        'north': lat + 0.5,
        'south': lat - 0.5,
        'east': lon + 0.5,
        'west': lon - 0.5,
    }



@bp.route('/')
def home():
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


@bp.route('/health')
def health_check():
    config = _get_config()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'config_valid': config.validate_config()
    })


@bp.route('/cities')
def cities():
    generator = _get_generator()
    payload = [
        {
            'name': city,
            'country': info['country'],
            'latitude': info['lat'],
            'longitude': info['lon'],
        }
        for city, info in generator.cities.items()
    ]
    return jsonify({'cities': payload, 'total': len(payload)})


@bp.route('/data/<city>')
def city_data(city: str):
    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    window = request.args.get('days', 30, type=int)
    fmt = request.args.get('format', 'json')

    config = _get_config()
    df = _load_city_dataframe(city, config)
    if df is None:
        return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404

    df = _apply_window(df, window)
    records = df.to_dict('records')

    if fmt == 'csv':
        return df.to_csv(index=False), 200, {'Content-Type': 'text/csv'}

    return jsonify({
        'city': city,
        'data': records,
        'total_records': len(records),
        'date_range': {
            'start': df['date'].min().isoformat() if not df.empty else None,
            'end': df['date'].max().isoformat() if not df.empty else None,
        },
    })


@bp.route('/data/generate', methods=['POST'])
def generate():
    payload = request.get_json() or {}
    city = payload.get('city', 'Delhi')
    days = payload.get('days', 30)

    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 400

    files = generator.save_sample_data(city, days)
    if not files:
        return jsonify({'error': 'Failed to generate data'}), 500

    return jsonify({
        'message': f'Sample data generated for {city}',
        'files': files,
        'city': city,
        'days': days,
    })


@bp.route('/satellite/<city>')
def satellite_data(city: str):
    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    window = request.args.get('days', 30, type=int)
    now = datetime.now()
    start = now - timedelta(days=window)

    area = _school_for_city(generator.cities[city])
    records = generator.generate_satellite_data(area, start, now, num_samples=window // 2)

    return jsonify({
        'city': city,
        'area': area,
        'satellite_data': records,
        'total_records': len(records),
        'date_range': {
            'start': start.isoformat(),
            'end': now.isoformat(),
        },
    })


@bp.route('/predict', methods=['POST'])
def predict():
    payload = request.get_json() or {}
    city = payload.get('city', 'Delhi')
    model_type = payload.get('model_type', 'random_forest')
    forecast_days = payload.get('forecast_days', 7)

    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 400

    config = _get_config()
    df = _load_city_dataframe(city, config)
    if df is None:
        return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404

    predictor = PollutionPredictor(model_type)
    features, targets = predictor.prepare_features(df.to_dict('records'))
    if features.size == 0:
        return jsonify({'error': 'Could not prepare features for ML model'}), 400

    training = predictor.train_model(features, targets)
    if not training:
        return jsonify({'error': 'Failed to train model'}), 500

    forecast = predictor.forecast_pollution(features, forecast_days)
    return jsonify({
        'city': city,
        'model_type': model_type,
        'training_results': training,
        'forecast': forecast,
        'forecast_days': forecast_days,
    })


@bp.route('/forecast/<city>')
def forecast(city: str):
    model_type = request.args.get('model_type', 'random_forest')
    forecast_days = request.args.get('forecast_days', 7, type=int)

    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    config = _get_config()
    df = _load_city_dataframe(city, config)
    if df is None:
        return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404

    predictor = PollutionPredictor(model_type)
    features, targets = predictor.prepare_features(df.to_dict('records'))
    if features.size == 0:
        return jsonify({'error': 'Could not prepare features for ML model'}), 400

    training = predictor.train_model(features, targets)
    if not training:
        return jsonify({'error': 'Failed to train model'}), 500

    result = predictor.forecast_pollution(features, forecast_days)
    return jsonify({
        'city': city,
        'model_type': model_type,
        'forecast': result,
        'forecast_days': forecast_days,
        'model_performance': training,
    })


@bp.route('/analysis/<city>')
def analysis(city: str):
    window = request.args.get('days', 30, type=int)

    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    config = _get_config()
    df = _load_city_dataframe(city, config)
    if df is None:
        return jsonify({'error': f'No data available for {city}. Generate data first.'}), 404

    df = _apply_window(df, window)
    df['date'] = pd.to_datetime(df['date'])

    def series_stats(series):
        if df.empty:
            return {'mean': 0, 'max': 0, 'min': 0, 'std': 0}
        return {
            'mean': float(series.mean()),
            'max': float(series.max()),
            'min': float(series.min()),
            'std': float(series.std()),
        }

    result = {
        'city': city,
        'total_records': len(df),
        'date_range': {
            'start': df['date'].min().isoformat() if not df.empty else None,
            'end': df['date'].max().isoformat() if not df.empty else None,
        },
        'pollution_statistics': {
            'PM2.5': series_stats(df['PM2.5']),
            'NO2': series_stats(df['NO2']),
        },
        'weather_statistics': {
            'temperature': series_stats(df['temperature']),
            'humidity': series_stats(df['humidity']),
        },
        'risk_level_distribution': df['risk_level'].value_counts().to_dict() if not df.empty else {},
        'fire_statistics': {
            'total_fires': int(df['fire_count'].sum()) if not df.empty else 0,
            'avg_fires_per_day': float(df['fire_count'].mean()) if not df.empty else 0,
            'max_fires_in_day': int(df['fire_count'].max()) if not df.empty else 0,
        },
    }

    if len(df) >= 7:
        pm_mean = df['PM2.5'].rolling(window=7).mean()
        pm_std = df['PM2.5'].rolling(window=7).std()
        no2_mean = df['NO2'].rolling(window=7).mean()
        no2_std = df['NO2'].rolling(window=7).std()
        result['anomaly_analysis'] = {
            'PM2.5_anomalies': int((np.abs(df['PM2.5'] - pm_mean) > 2 * pm_std).sum()),
            'NO2_anomalies': int((np.abs(df['NO2'] - no2_mean) > 2 * no2_std).sum()),
            'total_anomalies': int(((np.abs(df['PM2.5'] - pm_mean) > 2 * pm_std) |
                                    (np.abs(df['NO2'] - no2_mean) > 2 * no2_std)).sum()),
        }

    return jsonify(result)


@bp.route('/export/<city>')
def export(city: str):
    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    config = _get_config()
    path = os.path.join(config.DATA_DIR, f'{city}_pollution_data.geojson')
    if not os.path.exists(path):
        return jsonify({'error': f'No GeoJSON data available for {city}. Generate data first.'}), 404

    return send_file(path, as_attachment=True)


@bp.route('/crop-burning/<city>')
def crop_burning(city: str):
    generator = _get_generator()
    if city not in generator.cities:
        return jsonify({'error': f'City {city} not found'}), 404

    area = _school_for_city(generator.cities[city])
    window = request.args.get('days', 30, type=int)
    now = datetime.now()
    start = now - timedelta(days=window)

    satellite = generator.generate_satellite_data(area, start, now, num_samples=window // 2)
    processor = SatelliteDataProcessor()
    analysis = processor.process_crop_burning_data(satellite[0] if satellite else {}, area, window)

    return jsonify({
        'city': city,
        'area': area,
        'crop_burning_analysis': analysis,
        'fire_data': satellite,
        'date_range': {
            'start': start.isoformat(),
            'end': now.isoformat(),
        },
    })


@bp.errorhandler(404)
def not_found(_error):
    return jsonify({'error': 'Endpoint not found'}), 404


@bp.errorhandler(500)
def server_error(_error):
    return jsonify({'error': 'Internal server error'}), 500


