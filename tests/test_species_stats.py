#!/usr/bin/env python3
"""
Test script for the get_species_detection_stats function in the BirdWeather API utilities.
This script tests the ability to retrieve combined species detection statistics from
multiple API endpoints.

Usage:
    python test_species_stats.py

Note: This test requires a valid BirdWeather API key and station ID in the configuration.
"""

import sys
import os
import yaml
from pprint import pprint

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the function to test
from dashboard.utils.birdweather_api import get_species_detection_stats


def load_config():
    """Load configuration from YAML file"""
    config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    if not os.path.exists(config_file):
        print(f"Error: Configuration file not found at {config_file}")
        print("Make sure to create a config.yaml file based on config.example.yaml")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config


def test_species_detection_stats():
    """Test the get_species_detection_stats function"""
    # Load configuration
    config = load_config()
    
    # Test with a 1-day period for all species, limiting to 5 results
    print("\n=== Testing Species Detection Stats (1 day, all species) ===")
    period = {"count": 1, "unit": "day"}
    
    try:
        stats = get_species_detection_stats(config, period, limit=5)
        print(f"Retrieved {len(stats)} species detection statistics:")
        pprint(stats)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with a 7-day period for specific species 
    # The function will use the API's speciesId parameter for each species
    print("\n=== Testing Species Detection Stats (7 days, specific species) ===")
    period = {"count": 7, "unit": "day"}
    species_ids = ["144", "111"]  # Example species IDs: Northern Cardinal, American Robin
    
    try:
        stats = get_species_detection_stats(config, period, species_ids=species_ids)
        print(f"Retrieved {len(stats)} species detection statistics:")
        pprint(stats)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_species_detection_stats() 