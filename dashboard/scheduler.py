"""
Scheduler functionality for the BirdWeather Dashboard.

This module provides scheduled task functionality, including periodic 
weather data updates.
"""

import logging
from flask_apscheduler import APScheduler
from dashboard.utils.database import update_weather

# Create the scheduler
scheduler = APScheduler()

def init_scheduler(app, config):
    """
    Initialize the scheduler with the Flask app.
    
    Args:
        app: Flask application instance
        config: Configuration dictionary
    """
    # Configure the scheduler
    app.config['SCHEDULER_API_ENABLED'] = False
    app.config['SCHEDULER_TIMEZONE'] = 'UTC'
    
    # Initialize the scheduler with the app
    scheduler.init_app(app)
    
    # Add weather update job - runs every 10 minutes
    interval_minutes = config.get('weather', {}).get('update_interval_minutes', 10)
    
    @scheduler.task('interval', id='update_weather', minutes=interval_minutes)
    def scheduled_weather_update():
        """Update weather data from NWS API."""
        try:
            logging.info(f"Running scheduled weather update (every {interval_minutes} minutes)")
            # Use a single app_context for the entire operation
            with app.app_context():
                result = update_weather(config)
            
            if result.get('success', False):
                logging.info("Weather update successful")
                
                # Log specific update details
                if result.get('current_conditions_updated'):
                    logging.info("Updated current weather conditions")
                if result.get('forecast_updated'):
                    logging.info("Updated weather forecast")
            else:
                logging.error(f"Weather update failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            logging.error(f"Error during scheduled weather update: {e}")
    
    # Start the scheduler
    scheduler.start()
    logging.info(f"Started weather update scheduler (interval: {interval_minutes} minutes)")
    
    return scheduler 