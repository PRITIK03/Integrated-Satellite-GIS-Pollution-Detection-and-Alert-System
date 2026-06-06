"""
Data Generator Utility
Generates sample data for demonstration and testing purposes
"""

import os
import json
import random
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import logging

# Add parent directory to path for imports
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from config import PollutionConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    """Generates sample pollution and satellite data for demonstration"""
    
    def __init__(self):
        self.config = PollutionConfig()
        self.cities = {
            'Delhi': {'lat': 28.7041, 'lon': 77.1025, 'country': 'India'},
            'Mumbai': {'lat': 19.0760, 'lon': 72.8777, 'country': 'India'},
            'Nagpur': {'lat': 21.1458, 'lon': 79.0882, 'country': 'India'},
            'Beijing': {'lat': 39.9042, 'lon': 116.4074, 'country': 'China'},
            'Shanghai': {'lat': 31.2304, 'lon': 121.4737, 'country': 'China'},
            'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'country': 'USA'},
            'New York': {'lat': 40.7128, 'lon': -74.0060, 'country': 'USA'},
            'London': {'lat': 51.5074, 'lon': -0.1278, 'country': 'UK'},
            'Paris': {'lat': 48.8566, 'lon': 2.3522, 'country': 'France'},
            'Tokyo': {'lat': 35.6762, 'lon': 139.6503, 'country': 'Japan'},
            'Sydney': {'lat': -33.8688, 'lon': 151.2093, 'country': 'Australia'}
        }
        
    def generate_pollution_data(self, 
                               city: str,
                               start_date: datetime,
                               end_date: datetime,
                               num_samples: int = 100) -> List[Dict]:
        """
        Generate sample pollution data for a city
        
        Args:
            city: City name
            start_date: Start date for data generation
            end_date: End date for data generation
            num_samples: Number of samples to generate
            
        Returns:
            List of pollution data dictionaries
        """
        try:
            if city not in self.cities:
                logger.warning(f"City {city} not found, using Delhi as default")
                city = 'Delhi'
            
            city_info = self.cities[city]
            
            # Generate dates
            date_range = (end_date - start_date).days
            dates = [start_date + timedelta(days=i * date_range / num_samples) 
                    for i in range(num_samples)]
            
            pollution_data = []
            
            for i, date in enumerate(dates):
                # Base pollution levels (varies by city and season)
                base_pm25 = self._get_base_pollution(city, date, 'PM2.5')
                base_no2 = self._get_base_pollution(city, date, 'NO2')
                
                # Add seasonal variations
                seasonal_factor = self._get_seasonal_factor(date)
                
                # Add random noise
                noise_pm25 = np.random.normal(0, base_pm25 * 0.2)
                noise_no2 = np.random.normal(0, base_no2 * 0.15)
                
                # Add weekly patterns (weekends often have lower pollution)
                weekly_factor = 0.8 if date.weekday() >= 5 else 1.0
                
                # Add daily patterns (rush hour effects)
                hour_factor = self._get_hourly_factor(date.hour)
                
                # Calculate final values
                pm25 = float(max(0, (base_pm25 + noise_pm25) * seasonal_factor * weekly_factor * hour_factor))
                no2 = float(max(0, (base_no2 + noise_no2) * seasonal_factor * weekly_factor * hour_factor))
                
                # Generate related pollutants
                co = float(max(0, pm25 * 2.5 + np.random.normal(50, 20)))
                so2 = float(max(0, pm25 * 0.3 + np.random.normal(5, 2)))
                o3 = float(max(0, 30 + np.random.normal(0, 10)))  # Ozone often anti-correlated
                
                # Generate weather data
                weather = self._generate_weather_data(date, city)
                
                # Generate fire/crop burning data
                fire_data = self._generate_fire_data(date, city)
                
                # Create data record
                record = {
                    'city': city,
                    'country': city_info['country'],
                    'latitude': city_info['lat'],
                    'longitude': city_info['lon'],
                    'date': date.isoformat(),
                    'PM2.5': round(pm25, 2),
                    'NO2': round(no2, 2),
                    'CO': round(co, 2),
                    'SO2': round(so2, 2),
                    'O3': round(o3, 2),
                    'temperature': weather['temperature'],
                    'humidity': weather['humidity'],
                    'wind_speed': weather['wind_speed'],
                    'pressure': weather['pressure'],
                    'fire_count': fire_data['fire_count'],
                    'fire_intensity': fire_data['fire_intensity'],
                    'land_cover': fire_data['land_cover'],
                    'risk_level': self._assess_risk_level(pm25, no2)
                }
                
                pollution_data.append(record)
            
            logger.info(f"Generated {len(pollution_data)} pollution records for {city}")
            return pollution_data
            
        except Exception as e:
            logger.error(f"Error generating pollution data: {e}")
            return []
    
    def _get_base_pollution(self, city: str, date: datetime, pollutant: str) -> float:
        """Get base pollution level for a city and pollutant"""
        # Base levels vary by city and season
        city_base = {
            'Delhi': {'PM2.5': 80, 'NO2': 60},
            'Mumbai': {'PM2.5': 60, 'NO2': 45},
            'Beijing': {'PM2.5': 70, 'NO2': 55},
            'Shanghai': {'PM2.5': 55, 'NO2': 40},
            'Los Angeles': {'PM2.5': 35, 'NO2': 30},
            'New York': {'PM2.5': 40, 'NO2': 35},
            'London': {'PM2.5': 30, 'NO2': 25},
            'Paris': {'PM2.5': 25, 'NO2': 20},
            'Tokyo': {'PM2.5': 35, 'NO2': 30},
            'Sydney': {'PM2.5': 20, 'NO2': 15}
        }
        
        base = city_base.get(city, {'PM2.5': 40, 'NO2': 30})[pollutant]
        
        # Add seasonal variation
        month = date.month
        if month in [12, 1, 2]:  # Winter
            base *= 1.3
        elif month in [6, 7, 8]:  # Summer
            base *= 0.8
        
        return base
    
    def _get_seasonal_factor(self, date: datetime) -> float:
        """Get seasonal factor for pollution levels"""
        # Pollution often higher in winter due to heating and inversions
        day_of_year = date.timetuple().tm_yday
        seasonal = 1.0 + 0.3 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
        return seasonal
    
    def _get_hourly_factor(self, hour: int) -> float:
        """Get hourly factor for pollution levels"""
        # Rush hour effects
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.3
        elif 22 <= hour or hour <= 6:
            return 0.7
        else:
            return 1.0
    
    def _generate_weather_data(self, date: datetime, city: str) -> Dict:
        """Generate weather data for a city and date"""
        # Base weather varies by city and season
        month = date.month
        
        if city in ['Delhi', 'Mumbai', 'Beijing', 'Shanghai']:
            # Asian cities - monsoon and seasonal patterns
            if month in [6, 7, 8, 9]:  # Monsoon season
                temp = np.random.normal(30, 5)
                humidity = np.random.normal(80, 10)
            else:
                temp = np.random.normal(25, 8)
                humidity = np.random.normal(50, 20)
        elif city in ['Los Angeles', 'New York']:
            # US cities - seasonal patterns
            if month in [12, 1, 2]:
                temp = np.random.normal(10, 8)
                humidity = np.random.normal(60, 15)
            elif month in [6, 7, 8]:
                temp = np.random.normal(25, 5)
                humidity = np.random.normal(40, 15)
            else:
                temp = np.random.normal(18, 8)
                humidity = np.random.normal(50, 15)
        else:
            # European cities
            if month in [12, 1, 2]:
                temp = np.random.normal(5, 5)
                humidity = np.random.normal(70, 15)
            elif month in [6, 7, 8]:
                temp = np.random.normal(20, 5)
                humidity = np.random.normal(50, 15)
            else:
                temp = np.random.normal(12, 8)
                humidity = np.random.normal(60, 15)
        
        return {
            'temperature': float(round(temp, 1)),
            'humidity': float(round(max(0, min(100, humidity)), 1)),
            'wind_speed': float(round(max(0, np.random.normal(8, 4)), 1)),
            'pressure': float(round(np.random.normal(1013, 20), 1))
        }
    
    def _generate_fire_data(self, date: datetime, city: str) -> Dict:
        """Generate fire/crop burning data"""
        month = date.month
        
        # Fire season varies by region
        if city in ['Delhi', 'Mumbai']:
            # India - crop burning season (Oct-Nov)
            if month in [10, 11]:
                fire_count = np.random.poisson(15)
                fire_intensity = np.random.normal(0.8, 0.2)
            else:
                fire_count = np.random.poisson(3)
                fire_intensity = np.random.normal(0.3, 0.2)
        elif city in ['Beijing', 'Shanghai']:
            # China - some agricultural burning
            if month in [3, 4, 10, 11]:
                fire_count = np.random.poisson(8)
                fire_intensity = np.random.normal(0.6, 0.2)
            else:
                fire_count = np.random.poisson(2)
                fire_intensity = np.random.normal(0.2, 0.1)
        else:
            # Other cities - minimal fire activity
            fire_count = np.random.poisson(1)
            fire_intensity = np.random.normal(0.1, 0.1)
        
        # Land cover types: 1=urban, 2=agricultural, 3=forest, 4=grassland, 5=water
        land_cover_weights = {
            'Delhi': [0.7, 0.2, 0.05, 0.03, 0.02],
            'Mumbai': [0.6, 0.15, 0.1, 0.1, 0.05],
            'Beijing': [0.6, 0.25, 0.1, 0.03, 0.02],
            'Shanghai': [0.5, 0.3, 0.1, 0.05, 0.05],
            'Los Angeles': [0.4, 0.1, 0.3, 0.15, 0.05],
            'New York': [0.5, 0.1, 0.25, 0.1, 0.05],
            'London': [0.6, 0.2, 0.1, 0.08, 0.02],
            'Paris': [0.5, 0.3, 0.1, 0.08, 0.02],
            'Tokyo': [0.6, 0.15, 0.15, 0.05, 0.05],
            'Sydney': [0.4, 0.1, 0.3, 0.15, 0.05]
        }
        
        land_cover = np.random.choice(
            [1, 2, 3, 4, 5], 
            p=land_cover_weights.get(city, [0.5, 0.2, 0.2, 0.08, 0.02])
        )
        
        return {
            'fire_count': int(max(0, int(fire_count))),
            'fire_intensity': float(max(0, min(1, fire_intensity))),
            'land_cover': int(land_cover)
        }
    
    def _assess_risk_level(self, pm25: float, no2: float) -> str:
        """Assess overall pollution risk level"""
        # Use WHO guidelines
        pm25_thresholds = self.config.POLLUTION_THRESHOLDS['PM2.5']
        no2_thresholds = self.config.POLLUTION_THRESHOLDS['NO2']
        
        # Assess PM2.5 risk
        if pm25 <= pm25_thresholds['good']:
            pm25_risk = 'good'
        elif pm25 <= pm25_thresholds['moderate']:
            pm25_risk = 'moderate'
        elif pm25 <= pm25_thresholds['unhealthy_sensitive']:
            pm25_risk = 'unhealthy_sensitive'
        elif pm25 <= pm25_thresholds['unhealthy']:
            pm25_risk = 'unhealthy'
        elif pm25 <= pm25_thresholds['very_unhealthy']:
            pm25_risk = 'very_unhealthy'
        else:
            pm25_risk = 'hazardous'
        
        # Assess NO2 risk
        if no2 <= no2_thresholds['good']:
            no2_risk = 'good'
        elif no2 <= no2_thresholds['moderate']:
            no2_risk = 'moderate'
        elif no2 <= no2_thresholds['unhealthy_sensitive']:
            no2_risk = 'unhealthy_sensitive'
        elif no2 <= no2_thresholds['unhealthy']:
            no2_risk = 'unhealthy'
        elif no2 <= no2_thresholds['very_unhealthy']:
            no2_risk = 'very_unhealthy'
        else:
            no2_risk = 'hazardous'
        
        # Overall risk (take the worse of the two)
        risk_levels = ['good', 'moderate', 'unhealthy_sensitive', 'unhealthy', 'very_unhealthy', 'hazardous']
        overall_risk = max(risk_levels.index(pm25_risk), risk_levels.index(no2_risk))
        
        return risk_levels[overall_risk]
    
    def generate_satellite_data(self, 
                               area: Dict[str, float],
                               start_date: datetime,
                               end_date: datetime,
                               num_samples: int = 50) -> List[Dict]:
        """
        Generate sample satellite data
        
        Args:
            area: Bounding box coordinates
            start_date: Start date
            end_date: End date
            num_samples: Number of samples
            
        Returns:
            List of satellite data dictionaries
        """
        try:
            # Generate dates
            date_range = (end_date - start_date).days
            dates = [start_date + timedelta(days=i * date_range / num_samples) 
                    for i in range(num_samples)]
            
            satellite_data = []
            
            for date in dates:
                # Generate sample Sentinel-5P data
                sentinel_data = {
                    'date': date.isoformat(),
                    'product_type': 'L2__NO2___',
                    'area': area,
                    'NO2_mean': np.random.normal(20, 10),
                    'NO2_max': np.random.normal(50, 20),
                    'AER_AI_mean': np.random.normal(0.5, 0.3),
                    'CO_mean': np.random.normal(100, 30),
                    'HCHO_mean': np.random.normal(15, 8),
                    'SO2_mean': np.random.normal(5, 2),
                    'CH4_mean': np.random.normal(1800, 100),
                    'cloud_cover': np.random.uniform(0, 30),
                    'processing_level': 'L2',
                    'platform': 'Sentinel-5P'
                }
                
                # Generate sample MODIS data
                modis_data = {
                    'date': date.isoformat(),
                    'product_type': 'MODIS_Terra_Aerosol_5km_Daily',
                    'area': area,
                    'AOD_550nm': np.random.normal(0.3, 0.2),
                    'AOD_660nm': np.random.normal(0.25, 0.15),
                    'AOD_860nm': np.random.normal(0.2, 0.1),
                    'fire_count': np.random.poisson(5),
                    'fire_confidence': np.random.uniform(0.5, 1.0),
                    'land_cover': np.random.choice([1, 2, 3, 4, 5]),
                    'platform': 'MODIS_Terra'
                }
                
                satellite_data.extend([sentinel_data, modis_data])
            
            logger.info(f"Generated {len(satellite_data)} satellite data records")
            return satellite_data
            
        except Exception as e:
            logger.error(f"Error generating satellite data: {e}")
            return []
    
    def generate_geojson_data(self, 
                              pollution_data: List[Dict],
                              output_file: str) -> bool:
        """
        Convert pollution data to GeoJSON format
        
        Args:
            pollution_data: List of pollution data
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create GeoJSON structure
            geojson = {
                'type': 'FeatureCollection',
                'features': []
            }
            
            for record in pollution_data:
                # Create point geometry
                point = Point(record['longitude'], record['latitude'])
                
                # Create feature
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [record['longitude'], record['latitude']]
                    },
                    'properties': {
                        'city': record['city'],
                        'country': record['country'],
                        'date': record['date'],
                        'PM2.5': record['PM2.5'],
                        'NO2': record['NO2'],
                        'CO': record['CO'],
                        'SO2': record['SO2'],
                        'O3': record['O3'],
                        'temperature': record['temperature'],
                        'humidity': record['humidity'],
                        'wind_speed': record['wind_speed'],
                        'pressure': record['pressure'],
                        'fire_count': record['fire_count'],
                        'fire_intensity': record['fire_intensity'],
                        'land_cover': record['land_cover'],
                        'risk_level': record['risk_level']
                    }
                }
                
                geojson['features'].append(feature)
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(geojson, f, indent=2)
            
            logger.info(f"GeoJSON data saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating GeoJSON: {e}")
            return False
    
    def save_sample_data(self, 
                        city: str = 'Delhi',
                        days: int = 30,
                        output_dir: str = None) -> Dict[str, str]:
        """
        Generate and save sample data for a city
        
        Args:
            city: City name
            days: Number of days of data
            output_dir: Output directory
            
        Returns:
            Dictionary with file paths
        """
        try:
            if output_dir is None:
                output_dir = self.config.DATA_DIR
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Generate pollution data
            pollution_data = self.generate_pollution_data(
                city, start_date, end_date, num_samples=days
            )
            
            # Generate satellite data
            area = {
                'north': self.cities[city]['lat'] + 0.5,
                'south': self.cities[city]['lat'] - 0.5,
                'east': self.cities[city]['lon'] + 0.5,
                'west': self.cities[city]['lon'] - 0.5
            }
            
            satellite_data = self.generate_satellite_data(
                area, start_date, end_date, num_samples=days//2
            )
            
            # Save data
            pollution_file = os.path.join(output_dir, f'{city}_pollution_data.json')
            satellite_file = os.path.join(output_dir, f'{city}_satellite_data.json')
            geojson_file = os.path.join(output_dir, f'{city}_pollution_data.geojson')
            
            # Save pollution data
            with open(pollution_file, 'w') as f:
                json.dump(pollution_data, f, indent=2, default=str)
            
            # Save satellite data
            with open(satellite_file, 'w') as f:
                json.dump(satellite_data, f, indent=2, default=str)
            
            # Generate GeoJSON
            self.generate_geojson_data(pollution_data, geojson_file)
            
            logger.info(f"Sample data saved for {city}")
            
            return {
                'pollution_data': pollution_file,
                'satellite_data': satellite_file,
                'geojson_data': geojson_file
            }
            
        except Exception as e:
            logger.error(f"Error saving sample data: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    generator = SampleDataGenerator()
    
    # Generate sample data for Delhi
    files = generator.save_sample_data('Delhi', days=30)
    print("Generated files:", files)
