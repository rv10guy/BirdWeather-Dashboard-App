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


def get_species_detection_stats(
    config: Dict[str, Any],
    period: Dict[str, Union[int, str]],
    station_id: Optional[str] = None,
    species_ids: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve comprehensive detection statistics for bird species from the BirdWeather API.
    
    This function combines data from two API queries:
    1. topSpecies - to get the count of detections for each species
    2. detections - to get the most recent detection details (timestamp, confidence, etc.)
    
    Args:
        config: Configuration dictionary containing API settings
        period: Dictionary specifying the time period, e.g. {"count": 7, "unit": "day"}
        station_id: Optional station ID to override the one in config
        species_ids: Optional list of species IDs to filter by
        limit: Optional limit on the number of species to return (for pagination)
    
    Returns:
        List of dictionaries containing detection statistics with the following structure:
        [
            {
                "species_id": "Species identifier",
                "count": int,  # Number of detections in the period
                "latest_detection": "ISO-8601 timestamp",
                "probability": float,  # Probability from the most recent detection
                "confidence": float,  # Confidence from the most recent detection
                "score": float  # Score from the most recent detection
            },
            ...
        ]
    
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
    config_station_id = api_config.get("station_id")
    
    # Use provided station_id or fall back to config
    station_id = station_id or config_station_id
    
    if not all([api_url, api_key, station_id]):
        raise ValueError("Incomplete BirdWeather API configuration or missing station ID")
    
    # Prepare headers for all API requests
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    result = []
    
    # If species_ids is provided, we'll process each species individually
    # If not, we'll get all top species in one request
    if species_ids:
        for species_id in species_ids:
            # Step 1: Get the count for this specific species using the topSpecies query with speciesId
            top_species_query = """
            query topSpecies($period: InputDuration, $stationIds: [ID!], $speciesId: ID) {
                topSpecies(period: $period, stationIds: $stationIds, speciesId: $speciesId) {
                    count
                    species {
                        id
                    }
                }
            }
            """
            
            # Prepare variables for the top species query
            variables = {
                "stationIds": [station_id],
                "period": period,
                "speciesId": species_id
            }
            
            try:
                # Make the topSpecies API request
                response = requests.post(
                    api_url,
                    json={"query": top_species_query, "variables": variables},
                    headers=headers
                )
                response.raise_for_status()
                
                # Parse the response
                data = response.json()
                
                # Check for errors in the response
                if "errors" in data:
                    error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                    logging.error(f"BirdWeather API error (topSpecies for {species_id}): {error_msg}")
                    continue  # Skip this species but continue with others
                
                # Extract the top species data
                if "data" not in data or "topSpecies" not in data["data"] or not data["data"]["topSpecies"]:
                    logging.warning(f"No top species data found for species {species_id}")
                    continue  # Skip this species but continue with others
                
                # Since we're querying for a specific species, we should only get one result
                # But topSpecies always returns a list, so we need to find our species in it
                species_data = None
                for item in data["data"]["topSpecies"]:
                    if item.get("species", {}).get("id") == species_id:
                        species_data = item
                        break
                
                if not species_data:
                    logging.warning(f"Species {species_id} not found in topSpecies response")
                    continue  # Skip this species but continue with others
                
                count = species_data.get("count", 0)
                
                # Step 2: Get the most recent detection for this species
                species_stats = get_species_detection_details(api_url, headers, station_id, species_id, period, count)
                if species_stats:
                    result.append(species_stats)
                    
            except requests.RequestException as e:
                logging.error(f"Failed to fetch detection statistics for species {species_id}: {e}")
                continue  # Skip this species but continue with others
    else:
        # No specific species IDs provided, get all top species
        top_species_query = """
        query topSpecies($period: InputDuration, $stationIds: [ID!]) {
            topSpecies(period: $period, stationIds: $stationIds) {
                count
                species {
                    id
                }
            }
        }
        """
        
        # Prepare variables for the top species query
        variables = {
            "stationIds": [station_id],
            "period": period
        }
        
        try:
            # Make the topSpecies API request
            response = requests.post(
                api_url,
                json={"query": top_species_query, "variables": variables},
                headers=headers
            )
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Check for errors in the response
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                logging.error(f"BirdWeather API error (topSpecies): {error_msg}")
                raise ValueError(f"BirdWeather API error: {error_msg}")
            
            # Extract the top species data
            if "data" not in data or "topSpecies" not in data["data"]:
                logging.warning("No top species data found in API response")
                return []
            
            top_species_data = data["data"]["topSpecies"]
            
            # Apply limit if provided
            if limit is not None and limit > 0:
                top_species_data = top_species_data[:limit]
            
            # Process each species from the topSpecies response
            for species_item in top_species_data:
                species_id = species_item.get("species", {}).get("id")
                count = species_item.get("count", 0)
                
                if not species_id:
                    continue
                
                # Get detailed detection metrics for this species
                species_stats = get_species_detection_details(api_url, headers, station_id, species_id, period, count)
                if species_stats:
                    result.append(species_stats)
                
        except requests.RequestException as e:
            logging.error(f"Failed to fetch species detection statistics: {e}")
            raise
    
    return result

def get_species_detection_details(
    api_url: str, 
    headers: Dict[str, str], 
    station_id: str, 
    species_id: str, 
    period: Dict[str, Union[int, str]],
    count: int
) -> Optional[Dict[str, Any]]:
    """
    Helper function to get detailed detection metrics for a specific species.
    
    Args:
        api_url: The GraphQL API URL
        headers: API request headers including authorization
        station_id: Station ID to query
        species_id: Species ID to query
        period: Time period for the query
        count: Count of detections from the topSpecies query
        
    Returns:
        Dictionary with detection statistics or None if an error occurs
    """
    # Get the most recent detection for this species
    detection_query = """
    query detections($period: InputDuration, $stationIds: [ID!], $speciesId: ID) {
        detections(period: $period, stationIds: $stationIds, speciesId: $speciesId, first: 1) {
            edges {
                node {
                    confidence
                    probability
                    score
                    timestamp
                    species {
                        id
                    }
                }
            }
            totalCount
        }
    }
    """
    
    # Prepare variables for the detection query
    detection_variables = {
        "stationIds": [station_id],
        "speciesId": species_id,
        "period": period
    }
    
    try:
        # Make the detection API request
        detection_response = requests.post(
            api_url,
            json={"query": detection_query, "variables": detection_variables},
            headers=headers
        )
        detection_response.raise_for_status()
        
        # Parse the detection response
        detection_data = detection_response.json()
        
        # Check for errors in the detection response
        if "errors" in detection_data:
            error_msg = detection_data["errors"][0].get("message", "Unknown GraphQL error")
            logging.error(f"BirdWeather API error (detections for {species_id}): {error_msg}")
            return None
        
        # Initialize with default values
        confidence = None
        probability = None
        score = None
        timestamp = None
        
        # Extract the detection data if available
        if ("data" in detection_data and 
            "detections" in detection_data["data"] and 
            "edges" in detection_data["data"]["detections"] and
            detection_data["data"]["detections"]["edges"]):
            
            detection_node = detection_data["data"]["detections"]["edges"][0].get("node", {})
            
            if detection_node:
                confidence = detection_node.get("confidence")
                probability = detection_node.get("probability")
                score = detection_node.get("score")
                timestamp = detection_node.get("timestamp")
        
        # Return the merged data
        return {
            "species_id": species_id,
            "count": count,
            "latest_detection": timestamp,
            "probability": probability,
            "confidence": confidence,
            "score": score
        }
            
    except requests.RequestException as e:
        logging.error(f"Failed to fetch detection details for species {species_id}: {e}")
        return None 