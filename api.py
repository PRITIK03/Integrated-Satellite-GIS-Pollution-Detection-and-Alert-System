"""
Flask API Server for Pollution Detection System
Provides REST API endpoints for data access and analysis.
"""

from flask import Flask
from flask_cors import CORS
import logging

from config import PollutionConfig
from api.routes import api_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(api_bp)
    return app


if __name__ == '__main__':
    config = PollutionConfig()
    if not config.validate_config():
        logger.warning("Some API keys are missing. Some features may not work.")

    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )
