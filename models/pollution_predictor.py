"""
Pollution Prediction Models
Machine learning models for predicting PM2.5, NO2, and other pollutants
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
import xgboost as xgb
import joblib

from config import PollutionConfig
from utils.risk import RiskAssessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PollutionPredictor:
    """Main class for pollution prediction using machine learning models"""
    
    def __init__(self, model_type: str = 'random_forest'):
        self.config = PollutionConfig()
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.target_names = []
        self.model_path = os.path.join(self.config.OUTPUT_DIR, f'{model_type}_model.pkl')
        self.scaler_path = os.path.join(self.config.OUTPUT_DIR, f'{model_type}_scaler.pkl')
        
        # Initialize model
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the specified machine learning model"""
        if self.model_type == 'random_forest':
            self.model = RandomForestRegressor(**self.config.ML_MODEL_PARAMS['random_forest'])
        elif self.model_type == 'xgboost':
            self.model = xgb.XGBRegressor(**self.config.ML_MODEL_PARAMS['xgboost'])
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        elif self.model_type == 'linear':
            self.model = Ridge(alpha=1.0, random_state=42)
        else:
            logger.warning(f"Unknown model type: {self.model_type}. Using Random Forest.")
            self.model = RandomForestRegressor(**self.config.ML_MODEL_PARAMS['random_forest'])
    
    def prepare_features(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and targets from raw data
        
        Args:
            data: List of pollution data dictionaries
            
        Returns:
            Tuple of (features, targets)
        """
        try:
            if not data:
                return np.array([]), np.array([])
            
            # Extract features and targets
            features = []
            targets_pm25 = []
            targets_no2 = []
            
            for record in data:
                # Extract date-based features
                if 'date' in record:
                    date = record['date']
                    if isinstance(date, str):
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    
                    # Time-based features
                    features.append([
                        date.month,  # Month
                        date.day,    # Day of month
                        date.weekday(),  # Day of week
                        date.hour if hasattr(date, 'hour') else 12,  # Hour
                        np.sin(2 * np.pi * date.timetuple().tm_yday / 365.25),  # Seasonal
                        np.cos(2 * np.pi * date.timetuple().tm_yday / 365.25)   # Seasonal
                    ])
                    
                    # Add pollution features if available
                    if 'NO2_mean' in record:
                        features[-1].extend([
                            record.get('NO2_mean', 0),
                            record.get('NO2_max', 0),
                            record.get('AER_AI_mean', 0),
                            record.get('CO_mean', 0),
                            record.get('SO2_mean', 0)
                        ])
                    else:
                        # Fill with zeros if no pollution data
                        features[-1].extend([0, 0, 0, 0, 0])
                    
                    # Add weather features (if available)
                    features[-1].extend([
                        record.get('temperature', 25),  # Default temperature
                        record.get('humidity', 50),    # Default humidity
                        record.get('wind_speed', 5),   # Default wind speed
                        record.get('pressure', 1013)   # Default pressure
                    ])
                    
                    # Add fire/crop burning features
                    features[-1].extend([
                        record.get('fire_count', 0),
                        record.get('fire_intensity', 0),
                        record.get('land_cover', 1)
                    ])
                    
                    # Targets
                    targets_pm25.append(record.get('PM2.5', 0))
                    targets_no2.append(record.get('NO2', record.get('NO2_mean', 0)))
            
            # Convert to numpy arrays
            features = np.array(features)
            targets_pm25 = np.array(targets_pm25)
            targets_no2 = np.array(targets_no2)
            
            # Store feature names for later use
            self.feature_names = [
                'month', 'day', 'weekday', 'hour', 'seasonal_sin', 'seasonal_cos',
                'NO2_mean', 'NO2_max', 'AER_AI_mean', 'CO_mean', 'SO2_mean',
                'temperature', 'humidity', 'wind_speed', 'pressure',
                'fire_count', 'fire_intensity', 'land_cover'
            ]
            
            self.target_names = ['PM2.5', 'NO2']
            
            logger.info(f"Prepared {len(features)} samples with {features.shape[1]} features")
            return features, np.column_stack([targets_pm25, targets_no2])
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.array([]), np.array([])
    
    def train_model(self, features: np.ndarray, targets: np.ndarray, 
                   validation_split: float = 0.2) -> Dict:
        """
        Train the pollution prediction model
        
        Args:
            features: Feature matrix
            targets: Target matrix (PM2.5, NO2)
            validation_split: Fraction of data to use for validation
            
        Returns:
            Dictionary containing training results
        """
        try:
            if features.size == 0 or targets.size == 0:
                logger.error("No data provided for training")
                return {}
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                features, targets, test_size=validation_split, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_val_scaled = self.scaler.transform(X_val)
            
            # Train model for each target
            training_results = {}
            
            for i, target_name in enumerate(self.target_names):
                logger.info(f"Training model for {target_name}")
                
                # Train model
                self.model.fit(X_train_scaled, y_train[:, i])
                
                # Make predictions
                y_pred_train = self.model.predict(X_train_scaled)
                y_pred_val = self.model.predict(X_val_scaled)
                
                # Calculate metrics
                train_rmse = np.sqrt(mean_squared_error(y_train[:, i], y_pred_train))
                val_rmse = np.sqrt(mean_squared_error(y_val[:, i], y_pred_val))
                train_mae = mean_absolute_error(y_train[:, i], y_pred_train)
                val_mae = mean_absolute_error(y_val[:, i], y_pred_val)
                train_r2 = r2_score(y_train[:, i], y_pred_train)
                val_r2 = r2_score(y_val[:, i], y_pred_val)
                
                # Cross-validation score
                cv_scores = cross_val_score(
                    self.model, X_train_scaled, y_train[:, i], 
                    cv=5, scoring='neg_mean_squared_error'
                )
                cv_rmse = np.sqrt(-cv_scores.mean())
                
                training_results[target_name] = {
                    'train_rmse': train_rmse,
                    'val_rmse': val_rmse,
                    'train_mae': train_mae,
                    'val_mae': val_mae,
                    'train_r2': train_r2,
                    'val_r2': val_r2,
                    'cv_rmse': cv_rmse,
                    'feature_importance': self._get_feature_importance()
                }
                
                logger.info(f"{target_name} - Train R²: {train_r2:.3f}, Val R²: {val_r2:.3f}")
            
            # Save model and scaler
            self.save_model()
            
            return training_results
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {}
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        try:
            if hasattr(self.model, 'feature_importances_'):
                importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
                # Sort by importance
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            else:
                return {}
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def predict_pollution(self, features: np.ndarray) -> np.ndarray:
        """
        Predict pollution levels
        
        Args:
            features: Feature matrix
            
        Returns:
            Predicted pollution levels (PM2.5, NO2)
        """
        try:
            if self.model is None:
                logger.error("Model not trained")
                return np.array([])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make predictions
            predictions = self.model.predict(features_scaled)
            
            # Ensure 2D array
            if predictions.ndim == 1:
                predictions = predictions.reshape(-1, 1)
            
            logger.info(f"Made predictions for {len(predictions)} samples")
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return np.array([])
    
    def forecast_pollution(self, 
                          base_features: np.ndarray,
                          forecast_days: int = 7,
                          weather_forecast: Optional[Dict] = None) -> Dict:
        """
        Forecast pollution levels for future dates
        
        Args:
            base_features: Base feature set
            forecast_days: Number of days to forecast
            weather_forecast: Optional weather forecast data
            
        Returns:
            Dictionary containing forecast results
        """
        try:
            if self.model is None:
                logger.error("Model not trained")
                return {}
            
            forecasts = {}
            current_date = datetime.now()
            
            for day in range(forecast_days):
                forecast_date = current_date + timedelta(days=day)
                
                # Create features for this date
                date_features = [
                    forecast_date.month,
                    forecast_date.day,
                    forecast_date.weekday(),
                    12,  # Default hour
                    np.sin(2 * np.pi * forecast_date.timetuple().tm_yday / 365.25),
                    np.cos(2 * np.pi * forecast_date.timetuple().tm_yday / 365.25)
                ]
                
                # Add base pollution features (use recent averages)
                if base_features.size > 0:
                    recent_features = base_features[-1, 6:11]  # Pollution features
                    date_features.extend(recent_features)
                else:
                    date_features.extend([0, 0, 0, 0, 0])
                
                # Add weather features
                if weather_forecast and str(day) in weather_forecast:
                    weather = weather_forecast[str(day)]
                    date_features.extend([
                        weather.get('temperature', 25),
                        weather.get('humidity', 50),
                        weather.get('wind_speed', 5),
                        weather.get('pressure', 1013)
                    ])
                else:
                    date_features.extend([25, 50, 5, 1013])  # Default values
                
                # Add fire features (assume no change)
                date_features.extend([0, 0, 1])
                
                # Make prediction
                features_array = np.array([date_features])
                prediction = self.predict_pollution(features_array)
                
                if prediction.size > 0:
                    forecasts[forecast_date.strftime('%Y-%m-%d')] = {
                        'PM2.5': float(prediction[0, 0]) if prediction.shape[1] > 0 else 0,
                        'NO2': float(prediction[0, 1]) if prediction.shape[1] > 1 else 0,
                        'risk_level': self._assess_risk_level(prediction[0])
                    }
            
            logger.info(f"Generated {forecast_days} day forecast")
            return forecasts
            
        except Exception as e:
            logger.error(f"Error forecasting pollution: {e}")
            return {}
    
    def _assess_risk_level(self, prediction: np.ndarray) -> str:
        pm25 = prediction[0] if prediction.size > 0 else 0
        no2 = prediction[1] if prediction.size > 1 else 0
        return RiskAssessor(self.config.POLLUTION_THRESHOLDS).assess(pm25, no2)
    
    def save_model(self):
        """Save the trained model and scaler"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
            
            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save scaler
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self) -> bool:
        """Load a previously trained model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                # Load model
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                
                # Load scaler
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                logger.info("Model loaded successfully")
                return True
            else:
                logger.warning("No saved model found")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def evaluate_model(self, test_features: np.ndarray, test_targets: np.ndarray) -> Dict:
        """
        Evaluate model performance on test data
        
        Args:
            test_features: Test feature matrix
            test_targets: Test target matrix
            
        Returns:
            Dictionary containing evaluation metrics
        """
        try:
            if self.model is None:
                logger.error("Model not trained")
                return {}
            
            # Make predictions
            predictions = self.predict_pollution(test_features)
            
            if predictions.size == 0:
                return {}
            
            # Calculate metrics for each target
            evaluation_results = {}
            
            for i, target_name in enumerate(self.target_names):
                if i < test_targets.shape[1] and i < predictions.shape[1]:
                    y_true = test_targets[:, i]
                    y_pred = predictions[:, i]
                    
                    evaluation_results[target_name] = {
                        'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
                        'mae': mean_absolute_error(y_true, y_pred),
                        'r2': r2_score(y_true, y_pred),
                        'mape': np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
                    }
            
            logger.info("Model evaluation completed")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    # Create predictor
    predictor = PollutionPredictor('random_forest')
    
    # Generate sample data
    sample_data = []
    for i in range(100):
        sample_data.append({
            'date': datetime.now() - timedelta(days=i),
            'NO2_mean': np.random.normal(20, 10),
            'NO2_max': np.random.normal(50, 20),
            'AER_AI_mean': np.random.normal(0.5, 0.3),
            'CO_mean': np.random.normal(100, 30),
            'SO2_mean': np.random.normal(5, 2),
            'PM2.5': np.random.normal(30, 15),
            'temperature': np.random.normal(25, 10),
            'humidity': np.random.normal(50, 20),
            'wind_speed': np.random.normal(5, 3),
            'pressure': np.random.normal(1013, 50),
            'fire_count': np.random.poisson(2),
            'fire_intensity': np.random.normal(0.5, 0.3),
            'land_cover': np.random.choice([1, 2, 3, 4, 5])
        })
    
    # Prepare features
    features, targets = predictor.prepare_features(sample_data)
    
    if features.size > 0:
        # Train model
        results = predictor.train_model(features, targets)
        print("Training results:", results)
        
        # Make forecast
        forecast = predictor.forecast_pollution(features, forecast_days=7)
        print("7-day forecast:", forecast)
