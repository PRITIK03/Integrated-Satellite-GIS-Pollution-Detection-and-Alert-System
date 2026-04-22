# Pollution Detection System - Data Exploration
# This script provides comprehensive data exploration and analysis

import sys
import os
sys.path.append('..')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta

# Import custom modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PollutionConfig
from utils.data_generator import SampleDataGenerator

# Set up plotting style
plt.style.use('default')
sns.set_palette("husl")

def main():
    print("=== POLLUTION DETECTION SYSTEM - DATA EXPLORATION ===\n")
    
    # Load configuration
    config = PollutionConfig()
    config.create_directories()
    
    print(f"Data directory: {config.DATA_DIR}")
    print(f"Output directory: {config.OUTPUT_DIR}")
    
    # Initialize data generator
    data_generator = SampleDataGenerator()
    
    # Generate sample data for Delhi
    print("\nGenerating sample data for Delhi...")
    files = data_generator.save_sample_data('Delhi', days=90)
    print(f"Generated files: {files}")
    
    # Load pollution data
    data_file = os.path.join(config.DATA_DIR, 'Delhi_pollution_data.json')
    
    with open(data_file, 'r') as f:
        pollution_data = json.load(f)
    
    # Convert to DataFrame
    df = pd.DataFrame(pollution_data)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\nData shape: {df.shape}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Basic statistics
    print("\nBasic Statistics:")
    print(df.describe())
    
    # Risk level distribution
    risk_counts = df['risk_level'].value_counts()
    print(f"\nRisk Level Distribution:")
    for risk, count in risk_counts.items():
        percentage = (count / len(df)) * 100
        print(f"- {risk.title()}: {count} ({percentage:.1f}%)")
    
    # Create visualizations
    create_pollution_trends(df)
    create_weather_correlation(df)
    create_risk_analysis(df)
    
    # Summary
    print_summary(df)
    
    print("\n=== EXPLORATION COMPLETE ===")

def create_pollution_trends(df):
    """Create pollution trends visualization"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Pollution Trends Over Time', fontsize=16)
    
    # PM2.5 trend
    axes[0, 0].plot(df['date'], df['PM2.5'], 'b-', linewidth=2)
    axes[0, 0].set_title('PM2.5 Trend')
    axes[0, 0].set_ylabel('PM2.5 (µg/m³)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # NO2 trend
    axes[0, 1].plot(df['date'], df['NO2'], 'r-', linewidth=2)
    axes[0, 1].set_title('NO2 Trend')
    axes[0, 1].set_ylabel('NO2 (ppb)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # CO trend
    axes[1, 0].plot(df['date'], df['CO'], 'g-', linewidth=2)
    axes[1, 0].set_title('CO Trend')
    axes[1, 0].set_ylabel('CO (ppb)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # SO2 trend
    axes[1, 1].plot(df['date'], df['SO2'], 'm-', linewidth=2)
    axes[1, 1].set_title('SO2 Trend')
    axes[1, 1].set_ylabel('SO2 (ppb)')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('pollution_trends.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_weather_correlation(df):
    """Create weather correlation analysis"""
    weather_pollution = df[['PM2.5', 'NO2', 'temperature', 'humidity', 'wind_speed', 'pressure']]
    correlation_matrix = weather_pollution.corr()
    
    # Plot correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='RdBu_r', center=0, 
                square=True, linewidths=0.5)
    plt.title('Weather-Pollution Correlation Matrix', fontsize=16)
    plt.tight_layout()
    plt.savefig('weather_correlation.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_risk_analysis(df):
    """Create risk level analysis"""
    risk_counts = df['risk_level'].value_counts()
    
    # Create pie chart
    plt.figure(figsize=(10, 8))
    colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545', '#6f42c1', '#000000']
    plt.pie(risk_counts.values, labels=risk_counts.index, autopct='%1.1f%%', 
            colors=colors[:len(risk_counts)], startangle=90)
    plt.title('Distribution of Air Quality Risk Levels', fontsize=16)
    plt.axis('equal')
    plt.savefig('risk_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def print_summary(df):
    """Print comprehensive summary"""
    print(f"\n=== COMPREHENSIVE SUMMARY ===")
    print(f"Dataset Overview:")
    print(f"- Total records: {len(df)}")
    print(f"- Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"- City: Delhi, India")
    
    print(f"\nPollution Statistics:")
    print(f"- PM2.5: Mean={df['PM2.5'].mean():.1f} µg/m³, Max={df['PM2.5'].max():.1f} µg/m³")
    print(f"- NO2: Mean={df['NO2'].mean():.1f} ppb, Max={df['NO2'].max():.1f} ppb")
    print(f"- CO: Mean={df['CO'].mean():.1f} ppb, Max={df['CO'].max():.1f} ppb")
    print(f"- SO2: Mean={df['SO2'].mean():.1f} ppb, Max={df['SO2'].max():.1f} ppb")
    
    print(f"\nWeather Conditions:")
    print(f"- Temperature: {df['temperature'].mean():.1f}°C (range: {df['temperature'].min():.1f}°C to {df['temperature'].max():.1f}°C)")
    print(f"- Humidity: {df['humidity'].mean():.1f}% (range: {df['humidity'].min():.1f}% to {df['humidity'].max():.1f}%)")
    print(f"- Wind Speed: {df['wind_speed'].mean():.1f} m/s (range: {df['wind_speed'].min():.1f} m/s to {df['wind_speed'].max():.1f} m/s)")
    
    print(f"\nFire Activity:")
    print(f"- Total fires detected: {df['fire_count'].sum()}")
    print(f"- Average fires per day: {df['fire_count'].mean():.1f}")
    print(f"- Maximum fires in a day: {df['fire_count'].max()}")

if __name__ == "__main__":
    main()
