"""
Bird model for the BirdWeather Dashboard database.
"""
from datetime import datetime, timezone
from . import db

class Bird(db.Model):
    """
    Model representing a bird species.
    """
    __tablename__ = 'birds'
    
    species_id = db.Column(db.String(50), primary_key=True)
    common = db.Column(db.Boolean, default=False)
    birdweather_url = db.Column(db.String(255))
    common_name = db.Column(db.String(100))
    ebird_url = db.Column(db.String(255))
    scientific_name = db.Column(db.String(100))
    wikipedia_summary = db.Column(db.Text)
    wikipedia_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                           onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Bird {self.common_name} ({self.species_id})>"
    
    @classmethod
    def from_api_data(cls, api_data):
        """
        Create a Bird model instance from API data.
        
        Args:
            api_data: Dictionary with bird species data from API
            
        Returns:
            Bird model instance
        """
        return cls(
            species_id=api_data.get('id'),
            birdweather_url=api_data.get('birdweather_url'),
            common_name=api_data.get('common_name'),
            ebird_url=api_data.get('ebird_url'),
            scientific_name=api_data.get('scientific_name'),
            wikipedia_summary=api_data.get('wikipedia_summary'),
            wikipedia_url=api_data.get('wikipedia_url')
        ) 