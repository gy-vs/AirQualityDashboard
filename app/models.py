from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    province = Column(String, index=True)

class AirQualityData(Base):
    __tablename__ = "air_quality_data"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    pm25 = Column(Float)
    pm10 = Column(Float)
    so2 = Column(Float)
    no2 = Column(Float)
    co = Column(Float)
    o3 = Column(Float)
    aqi = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    city = relationship("City")
