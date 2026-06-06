"""
Satellite Data Processing Module
Handles Sentinel-5P and MODIS data acquisition and processing
"""

import os
import requests
import json
import xml.etree.ElementTree as ET
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import box
import logging

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from config import PollutionConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SatelliteDataProcessor:
    """Main class for processing satellite data from multiple sources"""
    
    def __init__(self):
        self.config = PollutionConfig()
        self.sentinel_api = None
        self.setup_apis()
        
    def setup_apis(self):
        """Initialize API connections"""
        try:
            if self.config.COPERNICUS_USERNAME and self.config.COPERNICUS_PASSWORD:
                self.sentinel_api = SentinelAPI(
                    self.config.COPERNICUS_USERNAME,
                    self.config.COPERNICUS_PASSWORD,
                    self.config.COPERNICUS_BASE_URL
                )
                logger.info("Sentinel API initialized successfully")
            else:
                logger.warning("Sentinel API credentials not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Sentinel API: {e}")
    
    def search_sentinel_data(self, 
                            product_type: str,
                            area: Dict[str, float],
                            start_date: datetime,
                            end_date: datetime,
                            cloud_cover: Tuple[float, float] = (0, 30)) -> List[Dict]:
        """
        Search for Sentinel satellite data
        
        Args:
            product_type: Type of product to search for
            area: Bounding box coordinates
            start_date: Start date for search
            end_date: End date for search
            cloud_cover: Cloud cover percentage range
            
        Returns:
            List of available products
        """
        if not self.sentinel_api:
            logger.error("Sentinel API not initialized")
            return []
        
        try:
            # Convert area to WKT format
            footprint = box(area['west'], area['south'], area['east'], area['north'])
            
            # Search for products
            products = self.sentinel_api.query(
                footprint,
                date=(start_date, end_date),
                producttype=product_type,
                cloudcoverpercentage=cloud_cover
            )
            
            # Convert to list of dictionaries
            products_df = self.sentinel_api.to_dataframe(products)
            products_list = products_df.to_dict('records')
            
            logger.info(f"Found {len(products_list)} Sentinel products")
            return products_list
            
        except Exception as e:
            logger.error(f"Error searching Sentinel data: {e}")
            return []
    
    def download_sentinel_product(self, product_id: str, output_dir: str) -> Optional[str]:
        """
        Download a Sentinel product
        
        Args:
            product_id: Product identifier
            output_dir: Directory to save the product
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not self.sentinel_api:
            logger.error("Sentinel API not initialized")
            return None
        
        try:
            # Download the product
            product_info = self.sentinel_api.download(product_id, output_dir)
            
            if product_info:
                logger.info(f"Successfully downloaded product {product_id}")
                return product_info
            else:
                logger.error(f"Failed to download product {product_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading Sentinel product: {e}")
            return None
    
    def process_sentinel_5p_data(self, file_path: str, output_dir: str) -> Dict:
        """
        Process Sentinel-5P data files
        
        Args:
            file_path: Path to the Sentinel-5P file
            output_dir: Directory to save processed data
            
        Returns:
            Dictionary containing processed data
        """
        try:
            # This is a simplified version - in practice you'd use proper HDF5/NetCDF processing
            # For demonstration, we'll create sample data
            
            # Extract date from filename
            filename = os.path.basename(file_path)
            date_str = filename.split('_')[2][:8]  # Extract date from filename
            date = datetime.strptime(date_str, '%Y%m%d')
            
            # Create sample pollution data (replace with actual data processing)
            sample_data = {
                'date': date,
                'NO2_mean': np.random.normal(20, 10),
                'NO2_max': np.random.normal(50, 20),
                'AER_AI_mean': np.random.normal(0.5, 0.3),
                'CO_mean': np.random.normal(100, 30),
                'SO2_mean': np.random.normal(5, 2),
                'file_path': file_path
            }
            
            # Save processed data
            output_file = os.path.join(output_dir, f"processed_{date_str}.json")
            with open(output_file, 'w') as f:
                json.dump(sample_data, f, default=str)
            
            logger.info(f"Processed Sentinel-5P data for {date_str}")
            return sample_data
            
        except Exception as e:
            logger.error(f"Error processing Sentinel-5P data: {e}")
            return {}
    
    def get_modis_data(self, 
                       product: str,
                       area: Dict[str, float],
                       start_date: datetime,
                       end_date: datetime) -> Optional[Dict]:
        """
        Get MODIS data from NASA Earth Data
        
        Args:
            product: MODIS product name
            area: Bounding box coordinates
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary containing MODIS data or None if failed
        """
        try:
            # This would typically use the NASA CMR API or similar
            # For demonstration, we'll create sample data
            
            # Create sample MODIS data
            modis_data = {
                'product': product,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'area': area,
                'data': {
                    'AOD': np.random.normal(0.3, 0.2, 100),
                    'fire_count': np.random.poisson(5, 100),
                    'land_cover': np.random.choice([1, 2, 3, 4, 5], 100)
                }
            }
            
            logger.info(f"Retrieved MODIS data for {product}")
            return modis_data
            
        except Exception as e:
            logger.error(f"Error getting MODIS data: {e}")
            return None
    
    def process_crop_burning_data(self, 
                                 fire_data: Dict,
                                 area: Dict[str, float],
                                 time_period: int = 30) -> Dict:
        """
        Process crop burning data to assess impact
        
        Args:
            fire_data: Fire detection data
            area: Geographic area of interest
            time_period: Time period in days
            
        Returns:
            Dictionary containing crop burning impact analysis
        """
        try:
            # Analyze fire patterns
            fire_counts = fire_data.get('data', {}).get('fire_count', [])
            
            if len(fire_counts) == 0:
                return {}
            
            # Calculate fire statistics
            total_fires = int(sum(fire_counts))
            avg_fires_per_day = float(np.mean(fire_counts))
            fire_trend = float(np.polyfit(range(len(fire_counts)), fire_counts, 1)[0])
            
            # Assess impact based on fire patterns
            impact_level = 'low'
            if total_fires > 100:
                impact_level = 'high'
            elif total_fires > 50:
                impact_level = 'medium'
            
            # Estimate pollution contribution
            # This is a simplified model - in practice you'd use more sophisticated models
            estimated_pm25_contribution = total_fires * 0.5  # µg/m³ per fire
            estimated_no2_contribution = total_fires * 0.2   # ppb per fire
            
            crop_burning_analysis = {
                'total_fires': total_fires,
                'avg_fires_per_day': avg_fires_per_day,
                'fire_trend': fire_trend,
                'impact_level': impact_level,
                'estimated_pollution_contribution': {
                    'PM2.5': estimated_pm25_contribution,
                    'NO2': estimated_no2_contribution
                },
                'analysis_date': datetime.now().isoformat(),
                'area': area
            }
            
            logger.info(f"Processed crop burning data: {total_fires} fires detected")
            return crop_burning_analysis
            
        except Exception as e:
            logger.error(f"Error processing crop burning data: {e}")
            return {}
    
    def create_temporal_analysis(self, 
                                data: List[Dict],
                                pollutant: str = 'NO2',
                                window_size: int = 7) -> Dict:
        """
        Create temporal analysis for anomaly detection
        
        Args:
            data: List of pollution data points
            pollutant: Pollutant to analyze
            window_size: Window size for moving average
            
        Returns:
            Dictionary containing temporal analysis results
        """
        try:
            if not data:
                return {}
            
            # Extract time series data
            dates = [d['date'] for d in data if 'date' in d]
            values = [d.get(f'{pollutant}_mean', 0) for d in data if 'date' in d]
            
            if len(values) < window_size:
                return {}
            
            # Convert to numpy arrays
            dates = np.array(dates)
            values = np.array(values)
            
            # Calculate moving average
            moving_avg = np.convolve(values, np.ones(window_size)/window_size, mode='valid')
            
            # Detect anomalies (values > 2 standard deviations from moving average)
            threshold = 2 * np.std(values)
            anomalies = np.abs(values[window_size-1:] - moving_avg) > threshold
            
            # Find anomaly dates
            anomaly_dates = dates[window_size-1:][anomalies]
            anomaly_values = values[window_size-1:][anomalies]
            
            temporal_analysis = {
                'pollutant': pollutant,
                'total_measurements': len(values),
                'moving_average_window': window_size,
                'anomaly_threshold': threshold,
                'anomaly_count': np.sum(anomalies),
                'anomaly_dates': [d.isoformat() if hasattr(d, 'isoformat') else str(d) 
                                 for d in anomaly_dates],
                'anomaly_values': anomaly_values.tolist(),
                'trend': np.polyfit(range(len(values)), values, 1)[0],
                'analysis_date': datetime.now().isoformat()
            }
            
            logger.info(f"Temporal analysis completed: {np.sum(anomalies)} anomalies detected")
            return temporal_analysis
            
        except Exception as e:
            logger.error(f"Error creating temporal analysis: {e}")
            return {}
    
    def export_to_geojson(self, data: Dict, output_file: str) -> bool:
        """
        Export processed data to GeoJSON format
        
        Args:
            data: Data to export
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert data to GeoJSON format
            # This is a simplified version - in practice you'd create proper geometries
            
            geojson_data = {
                'type': 'FeatureCollection',
                'features': []
            }
            
            # Add features based on data type
            if 'area' in data:
                # Create a simple polygon for the area
                coords = [
                    [data['area']['west'], data['area']['south']],
                    [data['area']['east'], data['area']['south']],
                    [data['area']['east'], data['area']['north']],
                    [data['area']['west'], data['area']['north']],
                    [data['area']['west'], data['area']['south']]
                ]
                
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [coords]
                    },
                    'properties': {k: v for k, v in data.items() if k != 'area'}
                }
                
                geojson_data['features'].append(feature)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            
            logger.info(f"Data exported to GeoJSON: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to GeoJSON: {e}")
            return False

# Example usage
if __name__ == "__main__":
    processor = SatelliteDataProcessor()
    
    # Example area (Delhi, India)
    area = {
        'north': 28.9,
        'south': 28.4,
        'east': 77.4,
        'west': 77.0
    }
    
    # Example date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Search for Sentinel data
    products = processor.search_sentinel_data(
        'L2__NO2___',
        area,
        start_date,
        end_date
    )
    
    print(f"Found {len(products)} products")
