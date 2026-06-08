import os
from dataclasses import dataclass, field
from typing import Dict, Tuple

from dotenv import load_dotenv

load_dotenv()


@dataclass
class PollutionConfig:
    NASA_EARTH_DATA_USERNAME: str = field(default_factory=lambda: os.getenv('NASA_EARTH_DATA_USERNAME', ''))
    NASA_EARTH_DATA_PASSWORD: str = field(default_factory=lambda: os.getenv('NASA_EARTH_DATA_PASSWORD', ''))
    COPERNICUS_USERNAME: str = field(default_factory=lambda: os.getenv('COPERNICUS_USERNAME', ''))
    COPERNICUS_PASSWORD: str = field(default_factory=lambda: os.getenv('COPERNICUS_PASSWORD', ''))
    OPENWEATHER_API_KEY: str = field(default_factory=lambda: os.getenv('OPENWEATHER_API_KEY', ''))
    DATABASE_URL: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///pollution_data.db'))
    DEBUG: bool = field(default_factory=lambda: os.getenv('DEBUG', 'True').lower() == 'true')
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'))
    FLASK_ENV: str = field(default_factory=lambda: os.getenv('FLASK_ENV', 'development'))
    DATA_DIR: str = field(default_factory=lambda: os.getenv('DATA_DIR', './data'))
    CACHE_DIR: str = field(default_factory=lambda: os.getenv('CACHE_DIR', './cache'))
    OUTPUT_DIR: str = field(default_factory=lambda: os.getenv('OUTPUT_DIR', './output'))

    NASA_EARTH_DATA_BASE_URL: str = "https://urs.earthdata.nasa.gov/api"
    COPERNICUS_BASE_URL: str = "https://scihub.copernicus.eu/dhus"
    SENTINEL_5P_BASE_URL: str = "https://s5phub.copernicus.eu/dhus"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    SENTINEL_5P_PRODUCTS: Dict[str, str] = field(default_factory=lambda: {
        'NO2': 'L2__NO2___',
        'AER_AI': 'L2__AER_AI',
        'CO': 'L2__CO____',
        'HCHO': 'L2__HCHO__',
        'SO2': 'L2__SO2___',
        'CH4': 'L2__CH4___'
    })

    MODIS_PRODUCTS: Dict[str, str] = field(default_factory=lambda: {
        'AOD': 'MODIS_Terra_Aerosol_5km_Daily',
        'FIRE': 'MODIS_Terra_Active_Fire_6_Month_1km',
        'LAND_COVER': 'MODIS_Terra_Land_Cover_Type_Yearly_500m'
    })

    DEFAULT_BOUNDS: Dict[str, float] = field(default_factory=lambda: {
        'north': 90.0, 'south': -90.0, 'east': 180.0, 'west': -180.0
    })

    POLLUTION_THRESHOLDS: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'PM2.5': {
            'good': 10, 'moderate': 25, 'unhealthy_sensitive': 35,
            'unhealthy': 55, 'very_unhealthy': 150, 'hazardous': 250
        },
        'NO2': {
            'good': 40, 'moderate': 100, 'unhealthy_sensitive': 150,
            'unhealthy': 200, 'very_unhealthy': 400, 'hazardous': 1000
        }
    })

    DEFAULT_TIMEFRAME: str = '30d'
    ANOMALY_DETECTION_WINDOW: int = 7

    ML_MODEL_PARAMS: Dict[str, Dict] = field(default_factory=lambda: {
        'random_forest': {
            'n_estimators': 100, 'max_depth': 10, 'random_state': 42
        },
        'xgboost': {
            'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.1, 'random_state': 42
        }
    })

    CACHE_EXPIRY: int = 3600

    def create_directories(self) -> None:
        for directory in [self.DATA_DIR, self.CACHE_DIR, self.OUTPUT_DIR]:
            os.makedirs(directory, exist_ok=True)

    def validate(self) -> Tuple[bool, list]:
        missing = [
            key for key in (
                'NASA_EARTH_DATA_USERNAME', 'NASA_EARTH_DATA_PASSWORD',
                'COPERNICUS_USERNAME', 'COPERNICUS_PASSWORD'
            )
            if not getattr(self, key)
        ]
        return len(missing) == 0, missing
