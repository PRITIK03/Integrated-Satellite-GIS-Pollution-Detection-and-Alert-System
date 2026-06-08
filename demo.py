#!/usr/bin/env python3
"""
Pollution Detection System - Comprehensive Demo
This script demonstrates all features of the pollution detection system
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append('.')

from config import PollutionConfig
from data_processing.satellite_data import SatelliteDataProcessor
from models.pollution_predictor import PollutionPredictor
from utils.data_generator import SampleDataGenerator

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def demo_configuration():
    """Demonstrate configuration system"""
    print_header("CONFIGURATION SYSTEM")
    
    config = PollutionConfig()
    config.create_directories()
    
    print("✅ Configuration loaded successfully")
    print(f"📁 Data directory: {config.DATA_DIR}")
    print(f"📁 Output directory: {config.OUTPUT_DIR}")
    print(f"📁 Cache directory: {config.CACHE_DIR}")
    
    # Validate configuration
    is_valid, _ = config.validate()
    if is_valid:
        print("✅ All required API keys are configured")
    else:
        print("⚠️  Some API keys are missing (using demo mode)")
    
    return config

def demo_data_generation():
    """Demonstrate data generation capabilities"""
    print_header("DATA GENERATION SYSTEM")
    
    data_generator = SampleDataGenerator()
    
    print(f"🌍 Available cities: {', '.join(data_generator.cities.keys())}")
    
    # Generate data for Delhi
    print_section("Generating Sample Data for Delhi")
    print("🔄 Generating 30 days of pollution data...")
    
    start_time = time.time()
    files = data_generator.save_sample_data('Delhi', days=30)
    end_time = time.time()
    
    if files:
        print(f"✅ Data generated successfully in {end_time - start_time:.2f} seconds")
        print("📁 Generated files:")
        for file_type, file_path in files.items():
            print(f"   - {file_type}: {file_path}")
    else:
        print("❌ Failed to generate data")
        return None
    
    return files

def demo_data_loading():
    """Demonstrate data loading and basic analysis"""
    print_header("DATA LOADING AND ANALYSIS")
    
    config = PollutionConfig()
    data_file = os.path.join(config.DATA_DIR, 'Delhi_pollution_data.json')
    
    if not os.path.exists(data_file):
        print("❌ Data file not found. Please run data generation first.")
        return None
    
    # Load data
    print_section("Loading Pollution Data")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Loaded {len(data)} records")
    print(f"📅 Date range: {data[0]['date']} to {data[-1]['date']}")
    
    # Basic statistics
    print_section("Basic Statistics")
    pm25_values = [record['PM2.5'] for record in data]
    no2_values = [record['NO2'] for record in data]
    
    print(f"PM2.5: Mean={sum(pm25_values)/len(pm25_values):.1f} µg/m³, "
          f"Max={max(pm25_values):.1f} µg/m³")
    print(f"NO2: Mean={sum(no2_values)/len(no2_values):.1f} ppb, "
          f"Max={max(no2_values):.1f} ppb")
    
    # Risk level distribution
    risk_counts = {}
    for record in data:
        risk = record['risk_level']
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    print_section("Risk Level Distribution")
    for risk, count in risk_counts.items():
        percentage = (count / len(data)) * 100
        print(f"{risk.title()}: {count} ({percentage:.1f}%)")
    
    return data

def demo_satellite_processing():
    """Demonstrate satellite data processing"""
    print_header("SATELLITE DATA PROCESSING")
    
    processor = SatelliteDataProcessor()
    
    # Example area (Delhi)
    area = {
        'north': 28.9,
        'south': 28.4,
        'east': 77.4,
        'west': 77.0
    }
    
    print_section("Satellite Data Processing")
    print(f"📍 Processing area: {area}")
    
    # Generate sample satellite data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    satellite_data = processor.get_modis_data(
        'MODIS_Terra_Aerosol_5km_Daily',
        area, start_date, end_date
    )
    
    if satellite_data:
        print("✅ Satellite data processed successfully")
        print(f"📊 Data points: {len(satellite_data.get('data', {}).get('AOD', []))}")
        print(f"🔥 Fire count: {satellite_data.get('data', {}).get('fire_count', [0])[0]}")
    else:
        print("❌ Failed to process satellite data")
    
    # Process crop burning data
    print_section("Crop Burning Analysis")
    crop_analysis = processor.process_crop_burning_data(
        satellite_data, area, 30
    )
    
    if crop_analysis:
        print("✅ Crop burning analysis completed")
        print(f"🔥 Total fires: {crop_analysis.get('total_fires', 0)}")
        print(f"📊 Impact level: {crop_analysis.get('impact_level', 'unknown')}")
        print(f"💨 PM2.5 contribution: {crop_analysis.get('estimated_pollution_contribution', {}).get('PM2.5', 0):.1f} µg/m³")
    else:
        print("❌ Failed to analyze crop burning data")

def demo_ml_predictions():
    """Demonstrate machine learning predictions"""
    print_header("MACHINE LEARNING PREDICTIONS")
    
    config = PollutionConfig()
    data_file = os.path.join(config.DATA_DIR, 'Delhi_pollution_data.json')
    
    if not os.path.exists(data_file):
        print("❌ Data file not found. Please run data generation first.")
        return
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Test different models
    models = ['random_forest', 'xgboost', 'gradient_boosting']
    
    for model_type in models:
        print_section(f"Testing {model_type.upper()} Model")
        
        try:
            # Initialize predictor
            predictor = PollutionPredictor(model_type)
            
            # Prepare features
            print("🔄 Preparing features...")
            features, targets = predictor.prepare_features(data)
            
            if features.size == 0:
                print("❌ Failed to prepare features")
                continue
            
            print(f"✅ Features prepared: {features.shape[0]} samples, {features.shape[1]} features")
            
            # Train model
            print("🤖 Training model...")
            start_time = time.time()
            training_results = predictor.train_model(features, targets)
            end_time = time.time()
            
            if training_results:
                print(f"✅ Model trained successfully in {end_time - start_time:.2f} seconds")
                
                # Display results
                for pollutant, results in training_results.items():
                    print(f"   {pollutant}: R²={results['val_r2']:.3f}, RMSE={results['val_rmse']:.2f}")
                
                # Make forecast
                print("🔮 Generating forecast...")
                forecast = predictor.forecast_pollution(features, forecast_days=7)
                
                if forecast:
                    print("✅ 7-day forecast generated:")
                    for date, prediction in list(forecast.items())[:3]:  # Show first 3 days
                        print(f"   {date}: PM2.5={prediction['PM2.5']:.1f} µg/m³, "
                              f"NO2={prediction['NO2']:.1f} ppb, "
                              f"Risk={prediction['risk_level']}")
                else:
                    print("❌ Failed to generate forecast")
            else:
                print("❌ Failed to train model")
                
        except Exception as e:
            print(f"❌ Error with {model_type}: {e}")

def demo_temporal_analysis():
    """Demonstrate temporal analysis and anomaly detection"""
    print_header("TEMPORAL ANALYSIS AND ANOMALY DETECTION")
    
    config = PollutionConfig()
    data_file = os.path.join(config.DATA_DIR, 'Delhi_pollution_data.json')
    
    if not os.path.exists(data_file):
        print("❌ Data file not found. Please run data generation first.")
        return
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    processor = SatelliteDataProcessor()
    
    print_section("Temporal Analysis")
    temporal_analysis = processor.create_temporal_analysis(
        data, pollutant='NO2', window_size=7
    )
    
    if temporal_analysis:
        print("✅ Temporal analysis completed")
        print(f"📊 Total measurements: {temporal_analysis.get('total_measurements', 0)}")
        print(f"🚨 Anomalies detected: {temporal_analysis.get('anomaly_count', 0)}")
        print(f"📈 Trend: {temporal_analysis.get('trend', 0):.3f}")
        
        if temporal_analysis.get('anomaly_dates'):
            print("📅 Anomaly dates:")
            for date in temporal_analysis['anomaly_dates'][:5]:  # Show first 5
                print(f"   - {date}")
    else:
        print("❌ Failed to perform temporal analysis")

def demo_export_capabilities():
    """Demonstrate data export capabilities"""
    print_header("DATA EXPORT CAPABILITIES")
    
    config = PollutionConfig()
    data_file = os.path.join(config.DATA_DIR, 'Delhi_pollution_data.json')
    
    if not os.path.exists(data_file):
        print("❌ Data file not found. Please run data generation first.")
        return
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    processor = SatelliteDataProcessor()
    
    print_section("Exporting to GeoJSON")
    output_file = os.path.join(config.OUTPUT_DIR, 'delhi_export.geojson')
    
    success = processor.export_to_geojson(data, output_file)
    
    if success:
        print(f"✅ Data exported to GeoJSON: {output_file}")
        
        # Check file size
        file_size = os.path.getsize(output_file)
        print(f"📁 File size: {file_size / 1024:.1f} KB")
    else:
        print("❌ Failed to export data")

def demo_performance_metrics():
    """Demonstrate system performance metrics"""
    print_header("SYSTEM PERFORMANCE METRICS")
    
    config = PollutionConfig()
    
    print_section("Directory Structure")
    for directory_name, directory_path in [
        ("Data", config.DATA_DIR),
        ("Output", config.OUTPUT_DIR),
        ("Cache", config.CACHE_DIR)
    ]:
        if os.path.exists(directory_path):
            file_count = len([f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))])
            total_size = sum(os.path.getsize(os.path.join(directory_path, f)) 
                           for f in os.listdir(directory_path) 
                           if os.path.isfile(os.path.join(directory_path, f)))
            print(f"📁 {directory_name}: {file_count} files, {total_size / 1024:.1f} KB")
        else:
            print(f"📁 {directory_name}: Directory not found")
    
    print_section("Data Files")
    data_dir = config.DATA_DIR
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.json') or file.endswith('.geojson'):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"📄 {file}: {file_size / 1024:.1f} KB, Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}")

def main():
    """Main demo function"""
    print_header("POLLUTION DETECTION SYSTEM - COMPREHENSIVE DEMO")
    print("This demo showcases all features of the pollution detection system")
    print("Built for hackathon: Pollution Detection using GIS + Satellite Imagery")
    
    try:
        # Run all demos
        config = demo_configuration()
        
        if not config:
            print("❌ Configuration failed. Exiting.")
            return
        
        files = demo_data_generation()
        
        if not files:
            print("❌ Data generation failed. Exiting.")
            return
        
        data = demo_data_loading()
        demo_satellite_processing()
        demo_ml_predictions()
        demo_temporal_analysis()
        demo_export_capabilities()
        demo_performance_metrics()
        
        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("🎉 All features demonstrated successfully!")
        print("\n📱 Next steps:")
        print("   1. Run 'streamlit run app.py' to start the dashboard")
        print("   2. Run 'python api.py' to start the API server")
        print("   3. Run 'python notebooks/data_exploration.py' for analysis")
        print("\n🌐 Access points:")
        print("   - Dashboard: http://localhost:8501")
        print("   - API: http://localhost:5000")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
