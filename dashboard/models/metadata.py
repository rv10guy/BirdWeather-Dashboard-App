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