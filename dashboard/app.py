#!/usr/bin/env python3
"""
Dashboard application main entry point.
"""
import os
import yaml
import logging
import datetime
from pathlib import Path
from flask import Flask, render_template

# Initialize Flask app
app = Flask(__name__)

def load_config(config_path=None):
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.environ.get('CONFIG_PATH', 
                                     Path(__file__).parent.parent / 'config' / 'config.yaml')
    
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return {}

def setup_logging(config):
    """Set up logging based on configuration."""
    log_level = config.get('logging', {}).get('level', 'INFO')
    log_file = config.get('logging', {}).get('file', None)
    
    logging_config = {
        'level': getattr(logging, log_level),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    }
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logging_config['filename'] = log_file
    
    logging.basicConfig(**logging_config)

# Mock data for development
def get_mock_weather_data():
    """Generate mock weather data for development."""
    return {
        'location': 'Sample Location',
        'temperature': 22.5,
        'feels_like': 23.1,
        'humidity': 65,
        'wind_speed': 12,
        'condition': 'Partly Cloudy'
    }

def get_mock_bird_data():
    """Generate mock bird sighting data for development."""
    return [
        {'species': 'American Robin', 'count': 5, 'time': '08:30 AM'},
        {'species': 'Blue Jay', 'count': 2, 'time': '09:15 AM'},
        {'species': 'Northern Cardinal', 'count': 3, 'time': '10:00 AM'},
        {'species': 'Black-capped Chickadee', 'count': 7, 'time': '10:45 AM'},
        {'species': 'Downy Woodpecker', 'count': 1, 'time': '11:30 AM'}
    ]

@app.route('/')
def index():
    """Render the main dashboard page."""
    # For a real app, you would fetch actual data here
    weather_data = get_mock_weather_data()
    bird_data = get_mock_bird_data()
    
    return render_template(
        'index.html',
        weather=weather_data,
        birds=bird_data,
        current_year=datetime.datetime.now().year
    )

def main():
    """Application entry point."""
    config = load_config()
    setup_logging(config)
    
    # Configure Flask app from config
    app.config['DEBUG'] = config.get('server', {}).get('debug', True)
    host = config.get('server', {}).get('host', '127.0.0.1')
    port = config.get('server', {}).get('port', 8080)
    
    logging.info(f"Starting dashboard application on {host}:{port}")
    app.run(host=host, port=port)
    logging.info("Dashboard application stopped")

if __name__ == "__main__":
    main()
