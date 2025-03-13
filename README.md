# BirdWeather Dashboard

A dashboard application for displaying bird sightings and weather data, designed to run on a Raspberry Pi in kiosk mode.

## Features

- Display current weather conditions
- Show recent bird sightings
- Visualize correlations between bird activity and weather patterns
- Responsive design that works well on various screen sizes

## Tech Stack

- **Backend**: Flask (Python 3.8+)
- **Frontend**: HTML5 with Jinja2 templating, Bootstrap 5, custom CSS, and Vanilla JavaScript
- **Data**: SQLite database for storing bird and weather data
- **Display**: Designed to run in Chromium kiosk mode on Raspberry Pi

## Setup

1. Clone the repository
   ```
   git clone https://github.com/rv10guy/BirdWeather-Dashboard-App.git
   cd BirdWeather-Dashboard-App
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example configuration:
   ```
   cp config/config.example.yaml config/config.yaml
   ```

5. Edit `config/config.yaml` with your settings

6. Run the application:
   ```
   python -m dashboard.app
   ```

7. Access the dashboard at `http://localhost:8080` (or the port specified in your config)

## Development

- Run tests: `pytest`
- Build documentation: `cd docs && make html`

## License

MIT License 