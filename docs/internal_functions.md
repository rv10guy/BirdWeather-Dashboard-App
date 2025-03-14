# BirdWeather Dashboard Internal Functions

This document describes the internal functions used by the BirdWeather Dashboard application to retrieve and process data from external APIs.

## Table of Contents

1. [BirdWeather API Functions](#birdweather-api-functions)
   1. [Daily Detection Counts](#daily-detection-counts)
   2. [Bird Detections](#bird-detections)
   3. [Bird Species Information](#bird-species-information)

---

## BirdWeather API Functions

These functions interact with the BirdWeather GraphQL API to retrieve bird detection data and related information.

### Daily Detection Counts

**Function**: `get_daily_detection_counts`

**Purpose**: Retrieves daily bird detection counts from the BirdWeather API for a specific time period and optionally filtered by species.

**Module**: `dashboard.utils.birdweather_api`

**Signature**:
```python
def get_daily_detection_counts(
    config: Dict[str, Any],
    period: Dict[str, Union[int, str]],
    species_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]
```

**Parameters**:
- `config`: Configuration dictionary containing API settings
- `period`: Dictionary specifying the time period, e.g. `{"count": 7, "unit": "day"}`
- `species_ids`: Optional list of species IDs to filter by

**Returns**:
- List of dictionaries containing date and detection count data
- Each dictionary has the format: `{"date": "YYYY-MM-DD", "total": int}`

**Exceptions**:
- `ValueError`: If the API configuration is missing or invalid, or if the API returns an error
- `requests.RequestException`: If the API request fails due to network issues

**Example Usage**:

```python
from dashboard.utils.birdweather_api import get_daily_detection_counts

# Get configuration
config = load_config()

# Get counts for the last 7 days for all species
period = {"count": 7, "unit": "day"}
counts = get_daily_detection_counts(config, period)

# Get counts for the last month for a specific species
period = {"count": 1, "unit": "month"}
species_counts = get_daily_detection_counts(config, period, species_ids=["144"])
```

**Example Output**:

```python
[
    {
        "date": "2025-02-26",
        "total": 8
    },
    {
        "date": "2025-02-27",
        "total": 12
    },
    {
        "date": "2025-02-28",
        "total": 5
    },
    {
        "date": "2025-03-01",
        "total": 10
    },
    {
        "date": "2025-03-02",
        "total": 7
    },
    {
        "date": "2025-03-03",
        "total": 15
    },
    {
        "date": "2025-03-04",
        "total": 3
    }
]
```

**Notes**:
- The function requires a valid API key in the configuration
- The time period is specified using a count and a unit (day, week, month, year)
- If no species IDs are provided, the API returns counts for all species
- The station ID is taken from the configuration and does not need to be explicitly provided

**GraphQL Query**:
```graphql
query dailyDetectionCounts($period: InputDuration, $stationIds: [ID!], $speciesIds: [ID!]) {
    dailyDetectionCounts(period: $period, stationIds: $stationIds, speciesIds: $speciesIds) {
        date
        total
    }
}
```

### Bird Detections

**Function**: `get_bird_detections`

**Purpose**: Retrieves detailed bird detection data from the BirdWeather API for a specific time period and optionally filtered by species.

**Module**: `dashboard.utils.birdweather_api`

**Signature**:
```python
def get_bird_detections(
    config: Dict[str, Any],
    period: Dict[str, Union[int, str]],
    species_ids: Optional[List[str]] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]
```

**Parameters**:
- `config`: Configuration dictionary containing API settings
- `period`: Dictionary specifying the time period, e.g. `{"count": 7, "unit": "day"}`
- `species_ids`: Optional list of species IDs to filter by
- `limit`: Optional limit on the number of detections to return (useful for pagination or limiting result size)

**Returns**:
- Dictionary containing detection data with the following structure:
  ```python
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
  ```

**Exceptions**:
- `ValueError`: If the API configuration is missing or invalid, or if the API returns an error
- `requests.RequestException`: If the API request fails due to network issues

**Example Usage**:

```python
from dashboard.utils.birdweather_api import get_bird_detections

# Get configuration
config = load_config()

# Get recent detections for all species (limited to 10)
period = {"count": 7, "unit": "day"}
detections = get_bird_detections(config, period, limit=10)

# Get detections for a specific species
period = {"count": 1, "unit": "day"}
species_detections = get_bird_detections(config, period, species_ids=["144"], limit=5)
```

**Example Output**:

```python
{
    "detections": [
        {
            "confidence": 0.5061336159706116,
            "probability": 0.9992398023605347,
            "score": 8.262290717452016,
            "timestamp": "2025-03-13T18:01:35-05:00",
            "soundscape_url": "https://media.birdweather.com/soundscapes/3e295b19c491517d002d7f238b4b6364",
            "species_id": "144"
        },
        {
            "confidence": 0.6848335862159729,
            "probability": 0.9992398023605347,
            "score": 9.117563109435785,
            "timestamp": "2025-03-13T18:01:23-05:00",
            "soundscape_url": "https://media.birdweather.com/soundscapes/c2f56f29650f36a5366cb6cceb554f5b",
            "species_id": "144"
        }
    ],
    "has_next_page": true,
    "end_cursor": "MTc0MTkwNjc2MQ",
    "total_count": 781
}
```

**Notes**:
- The function requires a valid API key in the configuration
- The time period is specified using a count and a unit (day, week, month, year)
- If no species IDs are provided, the API returns detections for all species
- The station ID is taken from the configuration and does not need to be explicitly provided
- The result includes pagination information for handling large result sets
- Using the `limit` parameter is recommended as stations can have thousands of detections in a day

**GraphQL Query**:
```graphql
query detections($period: InputDuration, $stationIds: [ID!], $speciesIds: [ID!]) {
    detections(period: $period, stationIds: $stationIds, speciesIds: $speciesIds, first: 10) {
        edges {
            node {
                confidence
                probability
                score
                timestamp
                soundscape {
                    url
                }
                species {
                    id
                }
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
        totalCount
    }
}
```

### Bird Species Information

**Function**: `get_bird_species_info`

**Purpose**: Retrieves detailed information about a specific bird species from the BirdWeather API, including its name, images, external links, and Wikipedia summary.

**Module**: `dashboard.utils.birdweather_api`

**Signature**:
```python
def get_bird_species_info(
    config: Dict[str, Any],
    species_id: str
) -> Dict[str, Any]
```

**Parameters**:
- `config`: Configuration dictionary containing API settings
- `species_id`: The ID of the bird species to retrieve information for

**Returns**:
- Dictionary containing species information with the following structure:
  ```python
  {
      "birdweather_url": "URL to the species page on BirdWeather",
      "color": "Hex color code associated with the species",
      "common_name": "Common name of the bird species",
      "ebird_url": "URL to the species page on eBird",
      "image_url": "URL to a full-size image of the species",
      "scientific_name": "Scientific name of the bird species",
      "thumbnail_url": "URL to a thumbnail image of the species",
      "wikipedia_summary": "Summary of the species from Wikipedia",
      "wikipedia_url": "URL to the species page on Wikipedia"
  }
  ```

**Exceptions**:
- `ValueError`: If the API configuration is missing or invalid, or if the species ID is invalid
- `requests.RequestException`: If the API request fails due to network issues

**Example Usage**:

```python
from dashboard.utils.birdweather_api import get_bird_species_info

# Get configuration
config = load_config()

# Get information about Northern Cardinal (species ID 144)
species_info = get_bird_species_info(config, "144")

# Access specific information
print(f"Bird: {species_info['common_name']} ({species_info['scientific_name']})")
print(f"Image: {species_info['image_url']}")
print(f"Description: {species_info['wikipedia_summary'][:100]}...")
```

**Example Output**:

```python
{
    "birdweather_url": "https://app.birdweather.com/species/northern-cardinal",
    "color": "#0161b0",
    "common_name": "Northern Cardinal",
    "ebird_url": "https://ebird.org/species/norcar",
    "image_url": "https://media.birdweather.com/species/144/NorthernCardinal-standard-823c8a4c9a2440b918aeee186d795296.jpg",
    "scientific_name": "Cardinalis cardinalis",
    "thumbnail_url": "https://media.birdweather.com/species/144/NorthernCardinal-thumbnail-a7b853614903f78e58b41703c018e9e2.jpg",
    "wikipedia_summary": "The northern cardinal (Cardinalis cardinalis) is a bird in the genus Cardinalis; it is also known colloquially as the redbird, common cardinal, red cardinal, or just cardinal (which was its name prior to 1985). It can be found in southeastern Canada, through the eastern United States from Maine to Minnesota to Texas, and south through Mexico, Belize, and Guatemala. It is also an introduced species in a few locations such as Bermuda and Hawaii. Its habitat includes woodlands, gardens, shrublands, and wetlands.\nThe northern cardinal is a mid-sized songbird with a body length of 21–23 cm (8.3–9.1 in). It has a distinctive crest on the head and a mask on the face which is black in the male and gray in the female. The male is a vibrant red, while the female is a reddish olive color. The northern cardinal is mainly granivorous, but also feeds on insects and fruit. The male behaves territorially, marking out his territory with song. During courtship, the male feeds seed to the female beak-to-beak. A clutch of three to four eggs is laid, and two to four clutches are produced each year. It was once prized as a pet, but its sale as a cage bird was banned in the United States by the Migratory Bird Treaty Act of 1918.",
    "wikipedia_url": "https://en.wikipedia.org/wiki/Northern_cardinal"
}
```

**Notes**:
- The function requires a valid API key in the configuration
- The species ID must be a valid identifier in the BirdWeather database
- The function transforms the camelCase API response keys to snake_case for consistency with Python naming conventions
- The Wikipedia summary can be quite lengthy and may need to be truncated for display purposes

**GraphQL Query**:
```graphql
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
```

--- 