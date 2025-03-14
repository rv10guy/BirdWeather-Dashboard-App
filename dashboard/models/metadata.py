"""
Metadata model for the BirdWeather Dashboard database.
"""
from . import db

class Metadata(db.Model):
    """
    Model for storing application metadata.
    """
    __tablename__ = 'metadata'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255))
    
    def __repr__(self):
        return f"<Metadata {self.key}: {self.value}>"
    
    @classmethod
    def get_last_detection_date(cls):
        """
        Get the date of the last bird detection.
        
        Returns:
            ISO format date string or None if not found
        """
        record = db.session.get(cls, 'last_detection_date')
        return record.value if record else None
    
    @classmethod
    def set_last_detection_date(cls, date_str):
        """
        Set the date of the last bird detection.
        
        Args:
            date_str: ISO format date string
            
        Returns:
            The updated or new Metadata instance
        """
        record = db.session.get(cls, 'last_detection_date')
        if record:
            record.value = date_str
        else:
            record = cls(key='last_detection_date', value=date_str)
            db.session.add(record)
        
        db.session.commit()
        return record 
    
    @classmethod
    def get_station_coordinates(cls):
        """
        Get the station coordinates (latitude and longitude).
        
        Returns:
            dict: Dictionary containing 'lat' and 'lon' or None if not found
        """
        lat_record = db.session.get(cls, 'station_latitude')
        lon_record = db.session.get(cls, 'station_longitude')
        
        if lat_record and lon_record:
            try:
                return {
                    'lat': float(lat_record.value),
                    'lon': float(lon_record.value)
                }
            except (ValueError, TypeError):
                return None
        return None
    
    @classmethod
    def set_station_coordinates(cls, lat, lon):
        """
        Set the station coordinates (latitude and longitude).
        
        Args:
            lat: Latitude as float
            lon: Longitude as float
            
        Returns:
            dict: Dictionary containing the updated coordinates
        """
        # Update or create latitude record
        lat_record = db.session.get(cls, 'station_latitude')
        if lat_record:
            lat_record.value = str(lat)
        else:
            lat_record = cls(key='station_latitude', value=str(lat))
            db.session.add(lat_record)
        
        # Update or create longitude record
        lon_record = db.session.get(cls, 'station_longitude')
        if lon_record:
            lon_record.value = str(lon)
        else:
            lon_record = cls(key='station_longitude', value=str(lon))
            db.session.add(lon_record)
        
        db.session.commit()
        return {'lat': lat, 'lon': lon} 