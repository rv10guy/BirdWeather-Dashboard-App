# Dashboard Application

A customizable dashboard application for data visualization and monitoring.

## Setup

1. Clone the repository
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

## Development

- Run tests: `pytest`
- Build documentation: `cd docs && make html`

## License

[Your chosen license] 