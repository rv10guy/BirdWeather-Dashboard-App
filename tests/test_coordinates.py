#!/usr/bin/env python3
"""
Test script for station coordinates functionality.

This script tests:
1. Reading coordinates from the database
2. Using update_station_coordinates function
3. Manually setting coordinates to new values
4. Verifying all operations work correctly
"""

import os
import sys
import yaml
from flask import Flask
from datetime import datetime

# Add the parent directory to the path to import from dashboard
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.models import db
from dashboard.models.metadata import Metadata
from dashboard.utils.database import update_station_coordinates


def load_config():
    """Load the application configuration."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_test_app():
    """Create a test Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    
    # Configure the database
    db_path = config.get('database', {}).get('path')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database
    db.init_app(app)
    
    return app, config


def test_read_coordinates(app):
    """Test reading coordinates from the database."""
    with app.app_context():
        coords = Metadata.get_station_coordinates()
        
    if coords:
        print(f"Current coordinates: lat={coords['lat']}, lon={coords['lon']}")
    else:
        print("No coordinates found in the database")
    
    return coords


def test_update_coordinates_function(app, config):
    """Test the update_station_coordinates function."""
    print("\nTesting update_station_coordinates function...")
    
    with app.app_context():
        # First, check if we already have coordinates
        existing = Metadata.get_station_coordinates()
        if existing:
            print(f"Existing coordinates: lat={existing['lat']}, lon={existing['lon']}")
        
        # Now try to update using the function
        result = update_station_coordinates(config)
        
        if result:
            print(f"After update function: lat={result['lat']}, lon={result['lon']}")
        else:
            print("Update function failed or returned None")
    
    return result


def test_manual_update(app):
    """Test manually updating coordinates."""
    print("\nTesting manual coordinate update...")
    
    # Test coordinates (Sydney Opera House)
    test_lat = -33.8567844
    test_lon = 151.2152967
    
    with app.app_context():
        # Update the coordinates
        result = Metadata.set_station_coordinates(test_lat, test_lon)
        print(f"Updated to test coordinates: lat={result['lat']}, lon={result['lon']}")
        
        # Read back to verify
        read_back = Metadata.get_station_coordinates()
        print(f"Read back: lat={read_back['lat']}, lon={read_back['lon']}")
        
        # Verify the values match
        lat_match = abs(read_back['lat'] - test_lat) < 0.0001
        lon_match = abs(read_back['lon'] - test_lon) < 0.0001
        
        if lat_match and lon_match:
            print("SUCCESS: Manual update verified!")
        else:
            print("FAILURE: Manual update did not match expected values")
    
    return read_back


def reset_to_original(app, original_coords):
    """Reset to the original coordinates."""
    print("\nResetting to original coordinates...")
    
    if not original_coords:
        print("No original coordinates to restore")
        return
    
    with app.app_context():
        result = Metadata.set_station_coordinates(original_coords['lat'], original_coords['lon'])
        print(f"Reset to original: lat={result['lat']}, lon={result['lon']}")


def main():
    """Run the tests."""
    print(f"=== Station Coordinates Test Script === ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Create test app
    app, config = create_test_app()
    
    # Test reading coordinates
    print("\nTesting coordinate reading...")
    original_coords = test_read_coordinates(app)
    
    # Test update function
    test_update_coordinates_function(app, config)
    
    # Test manual update
    test_manual_update(app)
    
    # Reset to original values
    reset_to_original(app, original_coords)
    
    print("\n=== Test Completed ===")


if __name__ == "__main__":
    main() 