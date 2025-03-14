"""
Database utility functions for the BirdWeather Dashboard.
"""
import os
import logging
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from dashboard.models import db
from dashboard.models.bird import Bird
from dashboard.models.metadata import Metadata
from dashboard.utils.birdweather_api import get_bird_detections, get_bird_species_info

def initialize_database(config):
    """
    Initialize the database if it doesn't exist.
    
    Args:
        config: Application configuration dictionary
        
    Returns:
        bool: True if the database was created, False otherwise
    """
    db_path = config.get("database", {}).get("path")
    if not db_path:
        logging.error("Database path not specified in configuration")
        return False
    
    # Create the directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Check if the database already exists
    if os.path.exists(db_path):
        logging.info(f"Database already exists at {db_path}")
        return False
    
    # Create the database
    try:
        with current_app.app_context():
            db.create_all()
        logging.info(f"Created new database at {db_path}")
        
        # Set the initial last detection date
        historical_days = config.get("database", {}).get("historical_days", 60)
        last_date = datetime.now(timezone.utc) - timedelta(days=historical_days)
        last_date_str = last_date.isoformat().replace('+00:00', 'Z')
        
        with current_app.app_context():
            Metadata.set_last_detection_date(last_date_str)
        logging.info(f"Set initial last detection date to {last_date_str}")
        
        return True
    except SQLAlchemyError as e:
        logging.error(f"Failed to create database: {e}")
        return False

def download_bird_image(url, filepath, is_thumbnail=False):
    """
    Download a bird image from a URL and save it to the filesystem.
    
    Args:
        url: URL of the image to download
        filepath: Path where the image should be saved
        is_thumbnail: Whether this is a thumbnail image
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    if not url:
        logging.warning(f"No {'thumbnail ' if is_thumbnail else ''}image URL provided")
        return False
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Download the image
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logging.info(f"Downloaded {'thumbnail ' if is_thumbnail else ''}image to {filepath}")
        return True
    except Exception as e:
        logging.error(f"Failed to download {'thumbnail ' if is_thumbnail else ''}image: {e}")
        return False

def add_bird_species(config, species_id):
    """
    Add a new bird species to the database.
    
    Args:
        config: Application configuration dictionary
        species_id: ID of the bird species to add
        
    Returns:
        Bird: The added Bird instance or None if failed
    """
    try:
        # Get species information from the API
        species_info = get_bird_species_info(config, species_id)
        if not species_info:
            logging.error(f"Failed to get species info for ID {species_id}")
            return None
        
        # Fix the species ID in the API data
        species_info['id'] = species_id
        
        # Create a new Bird instance
        bird = Bird.from_api_data(species_info)
        bird.common = False  # Initially mark as not common
        
        # Add to database
        with current_app.app_context():
            db.session.add(bird)
            db.session.commit()
            # Refresh the instance to ensure it's bound to the session
            db.session.refresh(bird)
        
        # Download images
        birds_img_dir = config.get("database", {}).get("birds_img_dir", "static/img/birds")
        base_path = Path(current_app.root_path) / birds_img_dir
        
        # Download main image
        if species_info.get('image_url'):
            main_image_path = base_path / f"{species_id}.jpg"
            download_bird_image(species_info.get('image_url'), main_image_path)
        
        # Download thumbnail
        if species_info.get('thumbnail_url'):
            thumbnail_path = base_path / f"{species_id}.thumbnail.jpg"
            download_bird_image(species_info.get('thumbnail_url'), thumbnail_path, is_thumbnail=True)
        
        logging.info(f"Added bird species {bird.common_name} ({species_id}) to database")
        return bird
    except Exception as e:
        logging.error(f"Failed to add bird species {species_id}: {e}")
        # Only rollback if we're in a transaction
        try:
            db.session.rollback()
        except:
            pass
        return None

def update_database(config):
    """
    Update the database with new bird detections.
    
    Args:
        config: Application configuration dictionary
        
    Returns:
        dict: Update statistics including counts of new detections and species
    """
    stats = {
        "detections_processed": 0,
        "new_species_added": 0,
        "total_detections": 0,
        "last_detection_date": None
    }
    
    try:
        # Get the date of the last detection
        with current_app.app_context():
            last_detection_date = Metadata.get_last_detection_date()
        
        if not last_detection_date:
            logging.error("No last detection date found in database")
            return stats
        
        logging.info(f"Starting database update from {last_detection_date}")
        
        # Calculate time period from last detection to now
        last_date = datetime.fromisoformat(last_detection_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_diff = (now - last_date).days + 1  # +1 to ensure we don't miss any detections
        
        # Prepare period for API request
        period = {"count": days_diff, "unit": "day"}
        
        # Get an initial count of detections for status updates
        try:
            detection_data = get_bird_detections(config, period, limit=1)
            stats["total_detections"] = detection_data.get("total_count", 0)
            logging.info(f"Found {stats['total_detections']} detections to process")
        except Exception as e:
            logging.error(f"Failed to get detection count: {e}")
            stats["total_detections"] = "unknown"
        
        # Process detections in batches
        batch_size = 100
        has_next_page = True
        end_cursor = None
        newest_detection_date = last_detection_date
        
        while has_next_page:
            try:
                # Get batch of detections with pagination cursor
                detection_data = get_bird_detections(config, period, limit=batch_size, after_cursor=end_cursor)
                detections = detection_data.get("detections", [])
                has_next_page = detection_data.get("has_next_page", False)
                end_cursor = detection_data.get("end_cursor")
                
                if not detections:
                    logging.info("No more detections to process")
                    break
                
                # Process each detection
                for detection in detections:
                    species_id = detection.get("species_id")
                    timestamp = detection.get("timestamp")
                    
                    # Update newest detection date if needed
                    if timestamp and timestamp > newest_detection_date:
                        newest_detection_date = timestamp
                    
                    # Check if species exists in database
                    with current_app.app_context():
                        # Use Session.get() instead of Query.get()
                        bird = db.session.get(Bird, species_id)
                        
                        # If species doesn't exist, add it
                        if not bird and species_id:
                            # Create a new session context for adding the bird
                            bird = add_bird_species(config, species_id)
                            if bird:
                                stats["new_species_added"] += 1
                    
                    stats["detections_processed"] += 1
                
                # Log progress
                if stats["total_detections"] != "unknown":
                    progress = (stats["detections_processed"] / stats["total_detections"]) * 100
                    logging.info(f"Processed {stats['detections_processed']} of {stats['total_detections']} detections ({progress:.1f}%)")
                else:
                    logging.info(f"Processed {stats['detections_processed']} detections")
                
            except Exception as e:
                logging.error(f"Error processing detection batch: {e}")
                break
        
        # Update the last detection date in the database
        if newest_detection_date and newest_detection_date > last_detection_date:
            with current_app.app_context():
                Metadata.set_last_detection_date(newest_detection_date)
            stats["last_detection_date"] = newest_detection_date
            logging.info(f"Updated last detection date to {newest_detection_date}")
        
        logging.info(f"Database update complete: {stats['detections_processed']} detections processed, {stats['new_species_added']} new species added")
        return stats
    
    except Exception as e:
        logging.error(f"Database update failed: {e}")
        return stats 