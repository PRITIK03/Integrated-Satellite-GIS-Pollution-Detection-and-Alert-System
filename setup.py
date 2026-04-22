#!/usr/bin/env python3
"""
Setup script for Pollution Detection System
Automates the installation and configuration process
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n--- {title} ---")

def check_python_version():
    """Check if Python version is compatible"""
    print_section("Checking Python Version")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_directories():
    """Create necessary directories"""
    print_section("Creating Directories")
    
    directories = [
        'data',
        'cache', 
        'output',
        'logs',
        'models'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def install_requirements():
    """Install required packages"""
    print_section("Installing Requirements")
    
    try:
        # Check if pip is available
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pip not found. Please install pip first.")
        return False
    
    # Install requirements
    print("📦 Installing required packages...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    print_section("Environment Setup")
    
    env_file = Path('.env')
    env_example = Path('env_example.txt')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        # Copy example file
        shutil.copy(env_example, env_file)
        print("📝 Created .env file from template")
        print("⚠️  Please edit .env file with your API keys")
        return True
    else:
        print("⚠️  No .env template found. Creating basic .env file...")
        
        # Create basic .env file
        env_content = """# API Keys for Satellite Data Sources
NASA_EARTH_DATA_USERNAME=your_nasa_username
NASA_EARTH_DATA_PASSWORD=your_nasa_password

# Copernicus Open Access Hub (Sentinel data)
COPERNICUS_USERNAME=your_copernicus_username
COPERNICUS_PASSWORD=your_copernicus_password

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_openweather_api_key

# Application Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
FLASK_ENV=development

# Data Storage
DATA_DIR=./data
CACHE_DIR=./cache
OUTPUT_DIR=./output
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("📝 Created basic .env file")
        print("⚠️  Please edit .env file with your API keys")
        return True

def test_imports():
    """Test if all modules can be imported"""
    print_section("Testing Imports")
    
    test_modules = [
        'numpy',
        'pandas', 
        'sklearn',
        'matplotlib',
        'seaborn',
        'plotly',
        'folium',
        'geopandas',
        'streamlit',
        'flask'
    ]
    
    failed_imports = []
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Failed to import: {', '.join(failed_imports)}")
        return False
    
    return True

def test_custom_modules():
    """Test custom module imports"""
    print_section("Testing Custom Modules")
    
    try:
        from config import PollutionConfig
        print("✅ config module")
        
        from data_processing.satellite_data import SatelliteDataProcessor
        print("✅ satellite_data module")
        
        from models.pollution_predictor import PollutionPredictor
        print("✅ pollution_predictor module")
        
        from utils.data_generator import SampleDataGenerator
        print("✅ data_generator module")
        
        return True
        
    except ImportError as e:
        print(f"❌ Custom module import failed: {e}")
        return False

def generate_sample_data():
    """Generate sample data for testing"""
    print_section("Generating Sample Data")
    
    try:
        from utils.data_generator import SampleDataGenerator
        
        data_generator = SampleDataGenerator()
        files = data_generator.save_sample_data('Delhi', days=7)
        
        if files:
            print("✅ Sample data generated successfully")
            for file_type, file_path in files.items():
                print(f"   📄 {file_type}: {file_path}")
            return True
        else:
            print("❌ Failed to generate sample data")
            return False
            
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        return False

def run_quick_test():
    """Run a quick system test"""
    print_section("Running Quick Test")
    
    try:
        from config import PollutionConfig
        config = PollutionConfig()
        config.create_directories()
        
        print("✅ Configuration system working")
        
        from data_processing.satellite_data import SatelliteDataProcessor
        processor = SatelliteDataProcessor()
        print("✅ Satellite processor initialized")
        
        from models.pollution_predictor import PollutionPredictor
        predictor = PollutionPredictor('random_forest')
        print("✅ ML predictor initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("SETUP COMPLETED")
    print("🎉 Pollution Detection System is ready!")
    
    print("\n📱 Next Steps:")
    print("1. Edit .env file with your API keys (optional for demo)")
    print("2. Run the demo: python demo.py")
    print("3. Start the dashboard: streamlit run app.py")
    print("4. Start the API server: python api.py")
    
    print("\n🌐 Access Points:")
    print("- Dashboard: http://localhost:8501")
    print("- API: http://localhost:5000")
    print("- API Documentation: http://localhost:5000/")
    
    print("\n📚 Available Scripts:")
    print("- demo.py: Comprehensive feature demonstration")
    print("- app.py: Streamlit dashboard")
    print("- api.py: Flask API server")
    print("- notebooks/data_exploration.py: Data analysis")
    
    print("\n🔧 Troubleshooting:")
    print("- Check .env file for API keys")
    print("- Ensure all requirements are installed")
    print("- Check logs for error messages")
    
    print("\n📖 Documentation:")
    print("- README.md: Project overview and setup")
    print("- requirements.txt: Python dependencies")
    print("- env_example.txt: Environment variables template")

def main():
    """Main setup function"""
    print_header("POLLUTION DETECTION SYSTEM - SETUP")
    print("This script will set up the pollution detection system")
    
    try:
        # Check Python version
        if not check_python_version():
            return
        
        # Create directories
        if not create_directories():
            return
        
        # Install requirements
        if not install_requirements():
            return
        
        # Setup environment
        if not setup_environment():
            return
        
        # Test imports
        if not test_imports():
            print("⚠️  Some packages failed to import. Continuing...")
        
        # Test custom modules
        if not test_custom_modules():
            print("❌ Custom modules failed. Setup incomplete.")
            return
        
        # Generate sample data
        if not generate_sample_data():
            print("⚠️  Sample data generation failed. Continuing...")
        
        # Run quick test
        if not run_quick_test():
            print("⚠️  Quick test failed. Setup may be incomplete.")
        
        # Print next steps
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
