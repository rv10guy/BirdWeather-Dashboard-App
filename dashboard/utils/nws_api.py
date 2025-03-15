#!/usr/bin/env python3
"""
National Weather Service (NWS) API utilities for the BirdWeather Dashboard.

This module provides functions to interact with the NWS API,
primarily for retrieving weather data including current conditions and forecasts.
"""

import logging
import requests
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from flask import current_app
from dashboard.models import db
from dashboard.models.metadata import Metadata
from dashboard.models.weather import LocationWeatherConfig, CurrentConditions, Forecast

# NWS API base URL
NWS_API_BASE_URL = "https://api.weather.gov"

# Constants for unit conversions
CELSIUS_TO_FAHRENHEIT = lambda c: (c * 9/5) + 32 if c is not None else None
KMH_TO_MPH = lambda kmh: kmh * 0.621371 if kmh is not None else None
PASCAL_TO_HPA = lambda pa: pa / 100 if pa is not None else None
METERS_TO_MILES = lambda m: m * 0.000621371 if m is not None else None
MM_TO_INCHES = lambda mm: mm * 0.0393701 if mm is not None else None

# Required headers for NWS API
DEFAULT_HEADERS = {
    "accept": "application/geo+json",
    "User-Agent": "BirdWeatherDashboard/1.0 (https://github.com/yourname/birdweatherdashboard)"
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface.
    Uses the Haversine formula for accurate distance calculation.
    
    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees
        
    Returns:
        Distance in miles between the points
    """
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in miles (3,958.8 miles)
    r = 3958.8
    
    # Calculate distance
    return c * r


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO 8601 datetime string to Python datetime object.
    
    Args:
        iso_string: ISO 8601 datetime string
        
    Returns:
        datetime object with UTC timezone
    """
    # Handle Z suffix (UTC)
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1] + '+00:00'
    
    # Parse the ISO string
    dt = datetime.fromisoformat(iso_string)
    
    # Ensure UTC timezone if none specified
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt


def round_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """
    Round coordinates to 4 decimal places for NWS API compatibility.
    The NWS API requires coordinates to be rounded to 4 decimal places.
    
    Args:
        lat: Latitude value
        lon: Longitude value
        
    Returns:
        Tuple of (latitude, longitude) rounded to 4 decimal places
    """
    return round(lat, 4), round(lon, 4)


def get_nws_point_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Get NWS point metadata for the given coordinates.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Dictionary containing point metadata or empty dict if request fails
    """
    # Round coordinates to 4 decimal places (required by NWS API)
    lat, lon = round_coordinates(lat, lon)
    
    # Construct the URL
    url = f"{NWS_API_BASE_URL}/points/{lat},{lon}"
    
    try:
        # Make the request
        response = requests.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        
        # Parse the JSON response
        data = response.json()
        
        return {
            'wfo': data['properties'].get('cwa'),
            'grid_x': data['properties'].get('gridX'),
            'grid_y': data['properties'].get('gridY'),
            'forecast_url': data['properties'].get('forecast'),
            'observation_stations_url': data['properties'].get('observationStations')
        }
    
    except (requests.RequestException, ValueError, KeyError) as e:
        logging.error(f"Error fetching NWS point data for ({lat}, {lon}): {e}")
        return {}


def find_closest_station(observation_stations_url: str, lat: float, lon: float) -> Dict[str, Any]:
    """
    Find the closest weather observation station to the given coordinates.
    
    Args:
        observation_stations_url: URL to get the list of stations
        lat: Target latitude
        lon: Target longitude
        
    Returns:
        Dictionary with station information including 'station_id' and 'conditions_url'
    """
    try:
        # Get the list of stations
        response = requests.get(observation_stations_url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        
        data = response.json()
        stations = data.get('features', [])
        
        if not stations:
            logging.warning(f"No stations found at {observation_stations_url}")
            return {}
        
        # Find the closest station
        closest_station = None
        min_distance = float('inf')
        
        for station in stations:
            # Extract station coordinates (provided as [lon, lat])
            station_coords = station.get('geometry', {}).get('coordinates', [])
            if len(station_coords) < 2:
                continue
            
            station_lon, station_lat = station_coords[0], station_coords[1]
            station_id = station.get('properties', {}).get('stationIdentifier')
            
            if not all([station_lat, station_lon, station_id]):
                continue
            
            # Calculate distance
            distance = haversine_distance(lat, lon, station_lat, station_lon)
            
            # Update closest station if this one is closer
            if distance < min_distance:
                min_distance = distance
                closest_station = {
                    'station_id': station_id,
                    'distance': distance,
                    'conditions_url': f"{NWS_API_BASE_URL}/stations/{station_id}/observations/latest"
                }
        
        if closest_station:
            logging.info(f"Found closest station: {closest_station['station_id']} at {closest_station['distance']:.2f} miles")
            return closest_station
        else:
            logging.warning("No valid stations found")
            return {}
            
    except (requests.RequestException, ValueError, KeyError) as e:
        logging.error(f"Error finding closest station: {e}")
        return {}


def get_current_conditions(conditions_url: str) -> Dict[str, Any]:
    """
    Get current weather conditions from a station.
    
    Args:
        conditions_url: URL for the station's latest observations
        
    Returns:
        Dictionary with processed weather data in imperial units
    """
    try:
        # Make the request
        response = requests.get(conditions_url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        
        data = response.json()
        props = data.get('properties', {})
        
        # Extract timestamp
        timestamp_str = props.get('timestamp')
        if not timestamp_str:
            logging.warning("No timestamp in conditions data")
            return {}
        
        timestamp = parse_iso_datetime(timestamp_str)
        
        # Extract temperature (C to F)
        temp_c = props.get('temperature', {}).get('value')
        temp_f = CELSIUS_TO_FAHRENHEIT(temp_c)
        
        # Extract dew point (C to F)
        dewpoint_c = props.get('dewpoint', {}).get('value')
        dewpoint_f = CELSIUS_TO_FAHRENHEIT(dewpoint_c)
        
        # Extract wind data (km/h to mph, degrees)
        wind_speed_kmh = props.get('windSpeed', {}).get('value')
        wind_speed_mph = KMH_TO_MPH(wind_speed_kmh)
        wind_direction = props.get('windDirection', {}).get('value')
        
        wind_gust_kmh = props.get('windGust', {}).get('value')
        wind_gust_mph = KMH_TO_MPH(wind_gust_kmh)
        
        # Extract barometric pressure (Pa to hPa)
        pressure_pa = props.get('barometricPressure', {}).get('value')
        pressure_hpa = PASCAL_TO_HPA(pressure_pa)
        
        # Extract visibility (m to miles)
        visibility_m = props.get('visibility', {}).get('value')
        visibility_miles = METERS_TO_MILES(visibility_m)
        
        # Extract humidity (%)
        humidity = props.get('relativeHumidity', {}).get('value')
        
        # Extract precipitation data (mm to inches)
        precip_1h_mm = props.get('precipitationLastHour', {}).get('value')
        precip_1h_in = MM_TO_INCHES(precip_1h_mm)
        
        precip_3h_mm = props.get('precipitationLast3Hours', {}).get('value')
        precip_3h_in = MM_TO_INCHES(precip_3h_mm)
        
        precip_6h_mm = props.get('precipitationLast6Hours', {}).get('value')
        precip_6h_in = MM_TO_INCHES(precip_6h_mm)
        
        # Extract description and icon
        description = props.get('textDescription')
        icon = props.get('icon')
        
        # Extract or calculate feels like temperature
        # First check if windChill or heatIndex is available
        windchill_c = props.get('windChill', {}).get('value')
        heatindex_c = props.get('heatIndex', {}).get('value')
        
        # Convert to Fahrenheit if available
        windchill_f = CELSIUS_TO_FAHRENHEIT(windchill_c)
        heatindex_f = CELSIUS_TO_FAHRENHEIT(heatindex_c)
        
        # Determine feels like temperature
        if windchill_f is not None:
            feels_like = windchill_f
        elif heatindex_f is not None:
            feels_like = heatindex_f
        else:
            # Default to actual temperature if neither is available
            feels_like = temp_f
        
        # Compile all data
        return {
            'timestamp': timestamp,
            'temperature': temp_f,
            'dew_point': dewpoint_f,
            'feels_like': feels_like,
            'humidity': humidity,
            'wind_speed': wind_speed_mph,
            'wind_direction': wind_direction,
            'wind_gust': wind_gust_mph,
            'pressure': pressure_hpa,
            'visibility': visibility_miles,
            'description': description,
            'precipitation_last_hour': precip_1h_in,
            'precipitation_last_3_hours': precip_3h_in,
            'precipitation_last_6_hours': precip_6h_in,
            'icon': icon
        }
        
    except (requests.RequestException, ValueError, KeyError) as e:
        logging.error(f"Error fetching current conditions: {e}")
        return {}


def get_forecast(forecast_url: str) -> List[Dict[str, Any]]:
    """
    Get forecast data from NWS.
    
    Args:
        forecast_url: URL for the location's forecast
        
    Returns:
        List of dictionaries containing forecast periods
    """
    try:
        # Make the request
        response = requests.get(forecast_url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        
        data = response.json()
        periods = data.get('properties', {}).get('periods', [])
        
        if not periods:
            logging.warning(f"No forecast periods found at {forecast_url}")
            return []
        
        # Process each period
        processed_periods = []
        for period in periods:
            # Extract data
            period_number = period.get('number')
            name = period.get('name')
            start_time_str = period.get('startTime')
            end_time_str = period.get('endTime')
            is_daytime = period.get('isDaytime', True)
            temperature = period.get('temperature')  # Already in Fahrenheit
            wind_speed = period.get('windSpeed')
            wind_direction = period.get('windDirection')
            
            # Extract probability of precipitation (may be null)
            precip_data = period.get('probabilityOfPrecipitation', {})
            probability_of_precip = precip_data.get('value') if precip_data else None
            
            short_forecast = period.get('shortForecast')
            detailed_forecast = period.get('detailedForecast')
            icon = period.get('icon')
            
            # Parse times
            if start_time_str and end_time_str:
                start_time = parse_iso_datetime(start_time_str)
                end_time = parse_iso_datetime(end_time_str)
            else:
                continue  # Skip periods without valid times
            
            # Add to processed periods
            processed_periods.append({
                'period_number': period_number,
                'name': name,
                'start_time': start_time,
                'end_time': end_time,
                'is_daytime': is_daytime,
                'temperature': temperature,
                'wind_speed': wind_speed,
                'wind_direction': wind_direction,
                'probability_of_precip': probability_of_precip,
                'short_forecast': short_forecast,
                'detailed_forecast': detailed_forecast,
                'icon': icon
            })
        
        return processed_periods
        
    except (requests.RequestException, ValueError, KeyError) as e:
        logging.error(f"Error fetching forecast: {e}")
        return []


def get_or_update_weather_config(lat: float, lon: float) -> Optional[LocationWeatherConfig]:
    """
    Get or update the weather configuration for a location.
    This function implements the core logic for determining whether to update static metadata.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        LocationWeatherConfig instance or None if failed
    """
    try:
        # Get the current configuration or create a new one
        config = LocationWeatherConfig.get_for_coordinates(lat, lon)
        
        # Determine if we need to update the static metadata
        needs_update = False
        if config.last_lat is None or config.last_lon is None:
            # First run, need to calculate everything
            needs_update = True
            logging.info("First run for location, fetching all weather metadata")
        elif abs(config.last_lat - lat) > 0.01 or abs(config.last_lon - lon) > 0.01:
            # Coordinates have changed significantly (more than ~1km), update
            needs_update = True
            logging.info(f"Location changed from ({config.last_lat}, {config.last_lon}) to ({lat}, {lon}), updating metadata")
        
        if needs_update:
            # Fetch NWS point data
            point_data = get_nws_point_data(lat, lon)
            
            if not point_data:
                logging.error("Failed to fetch NWS point data")
                return None
            
            # Update config with point data
            config.wfo = point_data.get('wfo')
            config.grid_x = point_data.get('grid_x')
            config.grid_y = point_data.get('grid_y')
            config.forecast_url = point_data.get('forecast_url')
            
            # Find the closest observation station
            if point_data.get('observation_stations_url'):
                station_data = find_closest_station(point_data['observation_stations_url'], lat, lon)
                
                if station_data:
                    config.station_id = station_data.get('station_id')
                    config.conditions_url = station_data.get('conditions_url')
                else:
                    logging.warning("No suitable weather station found")
            
            # Update the last coordinates
            config.last_lat = lat
            config.last_lon = lon
            
            # Save to database
            db.session.commit()
            logging.info(f"Updated weather configuration for ({lat}, {lon})")
        
        return config
        
    except Exception as e:
        logging.error(f"Error updating weather configuration: {e}")
        return None


def update_current_conditions(config: LocationWeatherConfig) -> bool:
    """
    Update the current weather conditions for a location.
    
    Args:
        config: LocationWeatherConfig instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config.conditions_url:
        logging.error("No conditions URL available for weather update")
        return False
    
    try:
        # Fetch current conditions
        conditions_data = get_current_conditions(config.conditions_url)
        
        if not conditions_data or 'timestamp' not in conditions_data:
            logging.error("Failed to fetch or parse current conditions")
            return False
        
        # Create new conditions record
        conditions = CurrentConditions(
            location_id=config.id,
            timestamp=conditions_data.get('timestamp'),
            temperature=conditions_data.get('temperature'),
            dew_point=conditions_data.get('dew_point'),
            feels_like=conditions_data.get('feels_like'),
            humidity=conditions_data.get('humidity'),
            wind_speed=conditions_data.get('wind_speed'),
            wind_direction=conditions_data.get('wind_direction'),
            wind_gust=conditions_data.get('wind_gust'),
            pressure=conditions_data.get('pressure'),
            visibility=conditions_data.get('visibility'),
            description=conditions_data.get('description'),
            precipitation_last_hour=conditions_data.get('precipitation_last_hour'),
            precipitation_last_3_hours=conditions_data.get('precipitation_last_3_hours'),
            precipitation_last_6_hours=conditions_data.get('precipitation_last_6_hours'),
            icon=conditions_data.get('icon')
        )
        
        # Save to database
        db.session.add(conditions)
        db.session.commit()
        
        logging.info(f"Updated current conditions for location {config.id}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating current conditions: {e}")
        db.session.rollback()
        return False


def update_forecast(config: LocationWeatherConfig) -> bool:
    """
    Update the forecast for a location.
    
    Args:
        config: LocationWeatherConfig instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not config.forecast_url:
        logging.error("No forecast URL available for weather update")
        return False
    
    try:
        # Fetch forecast data
        forecast_data = get_forecast(config.forecast_url)
        
        if not forecast_data:
            logging.error("Failed to fetch or parse forecast data")
            return False
        
        # First, remove existing forecasts for this location
        Forecast.query.filter_by(location_id=config.id).delete()
        
        # Add new forecasts
        for period in forecast_data:
            forecast = Forecast(
                location_id=config.id,
                period_number=period.get('period_number'),
                name=period.get('name'),
                start_time=period.get('start_time'),
                end_time=period.get('end_time'),
                is_daytime=period.get('is_daytime'),
                temperature=period.get('temperature'),
                wind_speed=period.get('wind_speed'),
                wind_direction=period.get('wind_direction'),
                probability_of_precip=period.get('probability_of_precip'),
                short_forecast=period.get('short_forecast'),
                detailed_forecast=period.get('detailed_forecast'),
                icon=period.get('icon')
            )
            
            db.session.add(forecast)
        
        # Commit all changes
        db.session.commit()
        
        logging.info(f"Updated forecast for location {config.id}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating forecast: {e}")
        db.session.rollback()
        return False


def update_weather_data(config=None) -> Dict[str, Any]:
    """
    Main function to update all weather data.
    
    Args:
        config: Optional application configuration dictionary
        
    Returns:
        dict: Status information about the update process
    """
    status = {
        'success': False,
        'message': "",
        'current_conditions_updated': False,
        'forecast_updated': False
    }
    
    try:
        # Use a single app context for the entire operation
        with current_app.app_context():
            # Get station coordinates
            coordinates = Metadata.get_station_coordinates()
        
            if not coordinates or 'lat' not in coordinates or 'lon' not in coordinates:
                status['message'] = "No station coordinates available"
                logging.error("No station coordinates available for weather update")
                return status
        
            lat, lon = coordinates['lat'], coordinates['lon']
        
            # Get or update weather configuration
            weather_config = get_or_update_weather_config(lat, lon)
        
            if not weather_config:
                status['message'] = "Failed to get or update weather configuration"
                return status
        
            # Update current conditions
            conditions_success = update_current_conditions(weather_config)
            status['current_conditions_updated'] = conditions_success
        
            # Update forecast
            forecast_success = update_forecast(weather_config)
            status['forecast_updated'] = forecast_success
        
            # Set overall success status
            status['success'] = conditions_success or forecast_success
        
            if status['success']:
                status['message'] = "Weather data updated successfully"
            else:
                status['message'] = "Failed to update weather data"
        
        return status
        
    except Exception as e:
        logging.error(f"Error in weather update process: {e}")
        status['message'] = f"Error updating weather data: {str(e)}"
        return status 