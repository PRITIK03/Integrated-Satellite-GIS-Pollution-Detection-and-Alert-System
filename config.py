import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PollutionConfig:
    """Configuration class for the Pollution Detection System"""
    
    # API Keys
    NASA_EARTH_DATA_USERNAME = os.getenv('NASA_EARTH_DATA_USERNAME', '')
    NASA_EARTH_DATA_PASSWORD = os.getenv('NASA_EARTH_DATA_PASSWORD', '')
    COPERNICUS_USERNAME = os.getenv('COPERNICUS_USERNAME', '')
    COPERNICUS_PASSWORD = os.getenv('COPERNICUS_PASSWORD', '')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///pollution_data.db')
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Data Storage
    DATA_DIR = os.getenv('DATA_DIR', './data')
    CACHE_DIR = os.getenv('CACHE_DIR', './cache')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    
    # API Endpoints
    NASA_EARTH_DATA_BASE_URL = "https://urs.earthdata.nasa.gov/api"
    COPERNICUS_BASE_URL = "https://scihub.copernicus.eu/dhus"
    SENTINEL_5P_BASE_URL = "https://s5phub.copernicus.eu/dhus"
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Satellite Data Parameters
    SENTINEL_5P_PRODUCTS = {
        'NO2': 'L2__NO2___',
        'AER_AI': 'L2__AER_AI',
        'CO': 'L2__CO____',
        'HCHO': 'L2__HCHO__',
        'SO2': 'L2__SO2___',
        'CH4': 'L2__CH4___'
    }
    
    MODIS_PRODUCTS = {
        'AOD': 'MODIS_Terra_Aerosol_5km_Daily',
        'FIRE': 'MODIS_Terra_Active_Fire_6_Month_1km',
        'LAND_COVER': 'MODIS_Terra_Land_Cover_Type_Yearly_500m'
    }
    
    # GIS Parameters
    DEFAULT_BOUNDS = {
        'north': 90.0,
        'south': -90.0,
        'east': 180.0,
        'west': -180.0
    }
    
    # Pollution Thresholds (WHO Guidelines)
    POLLUTION_THRESHOLDS = {
        'PM2.5': {
            'good': 10,
            'moderate': 25,
            'unhealthy_sensitive': 35,
            'unhealthy': 55,
            'very_unhealthy': 150,
            'hazardous': 250
        },
        'NO2': {
            'good': 40,
            'moderate': 100,
            'unhealthy_sensitive': 150,
            'unhealthy': 200,
            'very_unhealthy': 400,
            'hazardous': 1000
        }
    }
    
    # Time Series Parameters
    DEFAULT_TIMEFRAME = '30d'  # 30 days
    ANOMALY_DETECTION_WINDOW = 7  # 7 days for anomaly detection
    
    # Model Parameters
    ML_MODEL_PARAMS = {
        'random_forest': {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42
        },
        'xgboost': {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'random_state': 42
        }
    }
    
    # Cache Settings
    CACHE_EXPIRY = 3600  # 1 hour in seconds
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.DATA_DIR, cls.CACHE_DIR, cls.OUTPUT_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_keys = [
            'NASA_EARTH_DATA_USERNAME',
            'NASA_EARTH_DATA_PASSWORD',
            'COPERNICUS_USERNAME',
            'COPERNICUS_PASSWORD'
        ]
        
        missing_keys = [key for key in required_keys if not getattr(cls, key)]
        
        if missing_keys:
            print(f"Warning: Missing required API keys: {missing_keys}")
            print("Some features may not work without proper API keys")
        
        return len(missing_keys) == 0
