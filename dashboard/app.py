#!/usr/bin/env python3
"""
Dashboard application main entry point.
"""
import os
import yaml
import json
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

def load_mock_data():
    """Load mock data from JSON file."""
    try:
        mock_data_path = Path(__file__).parent.parent / 'docs' / 'mock-data.json'
        with open(mock_data_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to load mock data: {e}")
        return {}

@app.route('/')
def index():
    """Render the main dashboard page."""
    # Load mock data from JSON file
    mock_data = load_mock_data()
    
    # Get configuration
    config = app.config.get('dashboard_config', {})
    
    # Get image placeholder configuration
    image_placeholder = config.get('images', {}).get('default_placeholder', 
                                                   'https://placehold.co/400x300/4A90E2/FFFFFF?text=Bird')
    
    current_date_time = datetime.datetime.now().strftime("%d %b %Y %I:%M %p")
    
    return render_template(
        'index.html',
        recent_detections=mock_data.get('recent_detections', []),
        detection_summary=mock_data.get('detection_summary', []),
        birds=mock_data.get('birds', {}),
        weather=mock_data.get('weather', {}),
        station=mock_data.get('station', {}),
        current_date_time=current_date_time,
        image_placeholder=image_placeholder
    )

def main():
    """Application entry point."""
    config = load_config()
    setup_logging(config)
    
    # Store the entire config in app.config for access in routes
    app.config['dashboard_config'] = config
    
    # Configure Flask app from config
    app.config['DEBUG'] = config.get('server', {}).get('debug', True)
    host = config.get('server', {}).get('host', '127.0.0.1')
    port = config.get('server', {}).get('port', 8080)
    
    logging.info(f"Starting dashboard application on {host}:{port}")
    app.run(host=host, port=port)
    logging.info("Dashboard application stopped")

if __name__ == "__main__":
    main()
