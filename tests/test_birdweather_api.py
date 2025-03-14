#!/usr/bin/env python3
"""
Tests for the BirdWeather API utilities.
"""
import os
import sys
import yaml
import logging
from pathlib import Path

# Add the parent directory to sys.path to allow importing dashboard
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.utils.birdweather_api import get_daily_detection_counts, get_bird_detections, get_bird_species_info

def load_config():
    """Load configuration from the config.yaml file."""
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return {}

def test_daily_detection_counts():
    """Test the get_daily_detection_counts function."""
    # Load configuration
    config = load_config()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Testing get_daily_detection_counts function...")
    
    try:
        # Test with all species for the last 7 days
        period = {"count": 7, "unit": "day"}
        print(f"Getting detection counts for all species in the last {period['count']} {period['unit']}s...")
        
        all_counts = get_daily_detection_counts(config, period)
        print(f"Retrieved {len(all_counts)} days of counts for all species:")
        for count in all_counts:
            print(f"  {count['date']}: {count['total']} detections")
        
        # Test with a specific species for the last 7 days
        species_id = "144"  # American Robin (example)
        print(f"\nGetting detection counts for species {species_id} in the last {period['count']} {period['unit']}s...")
        
        species_counts = get_daily_detection_counts(config, period, species_ids=[species_id])
        print(f"Retrieved {len(species_counts)} days of counts for species {species_id}:")
        for count in species_counts:
            print(f"  {count['date']}: {count['total']} detections")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def test_bird_detections():
    """Test the get_bird_detections function."""
    # Load configuration
    config = load_config()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Testing get_bird_detections function...")
    
    try:
        # Test with all species for the last 7 days, limited to 5 results
        period = {"count": 7, "unit": "day"}
        limit = 5
        print(f"Getting {limit} detections for all species in the last {period['count']} {period['unit']}s...")
        
        all_detections = get_bird_detections(config, period, limit=limit)
        print(f"Retrieved {len(all_detections['detections'])} detections out of {all_detections['total_count']} total:")
        for i, detection in enumerate(all_detections['detections'], 1):
            print(f"  {i}. Species {detection['species_id']} at {detection['timestamp']} (Score: {detection['score']:.2f})")
        
        # Test with a specific species for the last 7 days, limited to 5 results
        species_id = "144"  # American Robin (example)
        print(f"\nGetting {limit} detections for species {species_id} in the last {period['count']} {period['unit']}s...")
        
        species_detections = get_bird_detections(config, period, species_ids=[species_id], limit=limit)
        print(f"Retrieved {len(species_detections['detections'])} detections out of {species_detections['total_count']} total:")
        for i, detection in enumerate(species_detections['detections'], 1):
            print(f"  {i}. Detected at {detection['timestamp']} (Score: {detection['score']:.2f})")
            print(f"     Confidence: {detection['confidence']:.4f}, Probability: {detection['probability']:.4f}")
            print(f"     Soundscape: {detection['soundscape_url']}")
        
        print(f"\nPagination info: Has next page: {species_detections['has_next_page']}, End cursor: {species_detections['end_cursor']}")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def test_bird_species_info():
    """Test the get_bird_species_info function."""
    # Load configuration
    config = load_config()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Testing get_bird_species_info function...")
    
    try:
        # Test with Northern Cardinal (species ID 144)
        species_id = "144"
        print(f"Getting species information for species ID {species_id}...")
        
        species_info = get_bird_species_info(config, species_id)
        if species_info:
            print(f"Retrieved information for {species_info['common_name']} ({species_info['scientific_name']}):")
            print(f"  Color: {species_info['color']}")
            print(f"  BirdWeather URL: {species_info['birdweather_url']}")
            print(f"  eBird URL: {species_info['ebird_url']}")
            print(f"  Wikipedia URL: {species_info['wikipedia_url']}")
            print(f"  Image URL: {species_info['image_url']}")
            print(f"  Thumbnail URL: {species_info['thumbnail_url']}")
            
            # Print a truncated version of the Wikipedia summary
            summary = species_info['wikipedia_summary']
            max_length = 200
            if summary and len(summary) > max_length:
                print(f"  Wikipedia Summary: {summary[:max_length]}...")
            else:
                print(f"  Wikipedia Summary: {summary}")
        else:
            print(f"No information found for species ID {species_id}")
        
        # Test with another species ID (American Robin - species ID 208)
        species_id = "208"
        print(f"\nGetting species information for species ID {species_id}...")
        
        species_info = get_bird_species_info(config, species_id)
        if species_info:
            print(f"Retrieved information for {species_info['common_name']} ({species_info['scientific_name']}):")
            print(f"  Color: {species_info['color']}")
            # Print a truncated version of the Wikipedia summary
            summary = species_info['wikipedia_summary']
            max_length = 200
            if summary and len(summary) > max_length:
                print(f"  Wikipedia Summary: {summary[:max_length]}...")
            else:
                print(f"  Wikipedia Summary: {summary}")
        else:
            print(f"No information found for species ID {species_id}")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    # Choose which test to run based on command-line argument
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        if test_name == "detections":
            success = test_bird_detections()
        elif test_name == "species":
            success = test_bird_species_info()
        else:
            success = test_daily_detection_counts()
    else:
        success = test_daily_detection_counts()
    
    sys.exit(0 if success else 1) 