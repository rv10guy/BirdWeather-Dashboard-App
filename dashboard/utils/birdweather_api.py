#!/usr/bin/env python3
"""
BirdWeather API utilities for the BirdWeather Dashboard.

This module provides functions to interact with the BirdWeather GraphQL API,
primarily for retrieving bird detection data and related information.
"""

import logging
import requests
from typing import Dict, List, Optional, Any, Union


def get_daily_detection_counts(
    config: Dict[str, Any],
    period: Dict[str, Union[int, str]],
    species_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve daily bird detection counts from the BirdWeather API.
    
    Args:
        config: Configuration dictionary containing API settings
        period: Dictionary specifying the time period, e.g. {"count": 7, "unit": "day"}
        species_ids: Optional list of species IDs to filter by
    
    Returns:
        List of dictionaries containing date and detection count data
        Each dictionary has the format: {"date": "YYYY-MM-DD", "total": int}
    
    Raises:
        ValueError: If the API configuration is missing or invalid
        requests.RequestException: If the API request fails
    """
    # Validate configuration
    if not config or "api" not in config or "birdweather" not in config["api"]:
        raise ValueError("Missing BirdWeather API configuration")
    
    api_config = config["api"]["birdweather"]
    api_url = api_config.get("url")
    api_key = api_config.get("key")
    station_id = api_config.get("station_id")
    
    if not all([api_url, api_key, station_id]):
        raise ValueError("Incomplete BirdWeather API configuration")
    
    # Prepare GraphQL query
    query = """
    query dailyDetectionCounts($period: InputDuration, $stationIds: [ID!], $speciesIds: [ID!]) {
        dailyDetectionCounts(period: $period, stationIds: $stationIds, speciesIds: $speciesIds) {
            date
            total
        }
    }
    """
    
    # Prepare variables for the query
    variables = {
        "stationIds": [station_id],
        "period": period
    }
    
    # Add species IDs if provided
    if species_ids:
        variables["speciesIds"] = species_ids
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Make the API request
    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Check for errors in the response
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            logging.error(f"BirdWeather API error: {error_msg}")
            raise ValueError(f"BirdWeather API error: {error_msg}")
        
        # Extract and return the daily detection counts
        if "data" in data and "dailyDetectionCounts" in data["data"]:
            return data["data"]["dailyDetectionCounts"]
        else:
            logging.warning("No daily detection count data found in API response")
            return []
            
    except requests.RequestException as e:
        logging.error(f"Failed to fetch daily detection counts: {e}")
        raise


def get_bird_detections(
    config: Dict[str, Any],
    period: Dict[str, Union[int, str]],
    species_ids: Optional[List[str]] = None,
    limit: Optional[int] = None,
    after_cursor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve detailed bird detections from the BirdWeather API.
    
    Args:
        config: Configuration dictionary containing API settings
        period: Dictionary specifying the time period, e.g. {"count": 7, "unit": "day"}
        species_ids: Optional list of species IDs to filter by
        limit: Optional limit on the number of detections to return
        after_cursor: Optional cursor for pagination
    
    Returns:
        Dictionary containing detection data with the following structure:
        {
            "detections": [
                {
                    "confidence": float,
                    "probability": float,
                    "score": float,
                    "timestamp": "ISO-8601 timestamp",
                    "soundscape_url": "URL to soundscape audio",
                    "species_id": "species identifier"
                },
                ...
            ],
            "has_next_page": bool,
            "end_cursor": "pagination cursor",
            "total_count": int
        }
    
    Raises:
        ValueError: If the API configuration is missing or invalid
        requests.RequestException: If the API request fails
    """
    # Validate configuration
    if not config or "api" not in config or "birdweather" not in config["api"]:
        raise ValueError("Missing BirdWeather API configuration")
    
    api_config = config["api"]["birdweather"]
    api_url = api_config.get("url")
    api_key = api_config.get("key")
    station_id = api_config.get("station_id")
    
    if not all([api_url, api_key, station_id]):
        raise ValueError("Incomplete BirdWeather API configuration")
    
    # Prepare GraphQL query with optional limit parameter and cursor
    limit_param = f", first: {limit}" if limit else ""
    after_param = f", after: \"{after_cursor}\"" if after_cursor else ""
    
    query = f"""
    query detections($period: InputDuration, $stationIds: [ID!], $speciesIds: [ID!]) {{
        detections(period: $period, stationIds: $stationIds, speciesIds: $speciesIds{limit_param}{after_param}) {{
            edges {{
                node {{
                    confidence
                    probability
                    score
                    timestamp
                    soundscape {{
                        url
                    }}
                    species {{
                        id
                    }}
                }}
            }}
            pageInfo {{
                hasNextPage
                endCursor
            }}
            totalCount
        }}
    }}
    """
    
    # Prepare variables for the query
    variables = {
        "stationIds": [station_id],
        "period": period
    }
    
    # Add species IDs if provided
    if species_ids:
        variables["speciesIds"] = species_ids
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Make the API request
    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Check for errors in the response
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            logging.error(f"BirdWeather API error: {error_msg}")
            raise ValueError(f"BirdWeather API error: {error_msg}")
        
        # Extract the detection data
        if "data" in data and "detections" in data["data"]:
            detections_data = data["data"]["detections"]
            
            # Transform the data into a more usable format
            result = {
                "detections": [],
                "has_next_page": detections_data["pageInfo"]["hasNextPage"],
                "end_cursor": detections_data["pageInfo"]["endCursor"],
                "total_count": detections_data["totalCount"]
            }
            
            # Process each detection
            for edge in detections_data.get("edges", []):
                node = edge.get("node", {})
                if node:
                    detection = {
                        "confidence": node.get("confidence"),
                        "probability": node.get("probability"),
                        "score": node.get("score"),
                        "timestamp": node.get("timestamp"),
                        "soundscape_url": node.get("soundscape", {}).get("url"),
                        "species_id": node.get("species", {}).get("id")
                    }
                    result["detections"].append(detection)
            
            return result
        else:
            logging.warning("No detection data found in API response")
            return {"detections": [], "has_next_page": False, "end_cursor": None, "total_count": 0}
            
    except requests.RequestException as e:
        logging.error(f"Failed to fetch bird detections: {e}")
        raise


def get_bird_species_info(
    config: Dict[str, Any],
    species_id: str
) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific bird species from the BirdWeather API.
    
    Args:
        config: Configuration dictionary containing API settings
        species_id: The ID of the bird species to retrieve information for
    
    Returns:
        Dictionary containing species information with the following structure:
        {
            "birdweather_url": URL to the species page on BirdWeather,
            "color": Hex color code associated with the species,
            "common_name": Common name of the bird species,
            "ebird_url": URL to the species page on eBird,
            "image_url": URL to a full-size image of the species,
            "scientific_name": Scientific name of the bird species,
            "thumbnail_url": URL to a thumbnail image of the species,
            "wikipedia_summary": Summary of the species from Wikipedia,
            "wikipedia_url": URL to the species page on Wikipedia
        }
    
    Raises:
        ValueError: If the API configuration is missing or invalid, or if the species ID is invalid
        requests.RequestException: If the API request fails
    """
    # Validate configuration
    if not config or "api" not in config or "birdweather" not in config["api"]:
        raise ValueError("Missing BirdWeather API configuration")
    
    api_config = config["api"]["birdweather"]
    api_url = api_config.get("url")
    api_key = api_config.get("key")
    
    if not all([api_url, api_key, species_id]):
        raise ValueError("Incomplete API configuration or missing species ID")
    
    # Prepare GraphQL query
    query = """
    query species($id: ID!) {
        species(id: $id) {
            birdweatherUrl
            color
            commonName
            ebirdUrl
            imageUrl
            scientificName
            thumbnailUrl
            wikipediaSummary
            wikipediaUrl
        }
    }
    """
    
    # Prepare variables for the query
    variables = {"id": species_id}
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Make the API request
    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        
        # Check for errors in the response
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            logging.error(f"BirdWeather API error: {error_msg}")
            raise ValueError(f"BirdWeather API error: {error_msg}")
        
        # Extract the species data
        if "data" in data and "species" in data["data"]:
            species_data = data["data"]["species"]
            
            # Transform the data into a more consistent format with snake_case keys
            result = {
                "birdweather_url": species_data.get("birdweatherUrl"),
                "color": species_data.get("color"),
                "common_name": species_data.get("commonName"),
                "ebird_url": species_data.get("ebirdUrl"),
                "image_url": species_data.get("imageUrl"),
                "scientific_name": species_data.get("scientificName"),
                "thumbnail_url": species_data.get("thumbnailUrl"),
                "wikipedia_summary": species_data.get("wikipediaSummary"),
                "wikipedia_url": species_data.get("wikipediaUrl")
            }
            
            return result
        else:
            logging.warning(f"No species data found for ID {species_id}")
            return {}
            
    except requests.RequestException as e:
        logging.error(f"Failed to fetch bird species info: {e}")
        raise 