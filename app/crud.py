from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from . import models
from datetime import datetime, timedelta
from typing import List, Dict

def get_all_cities(db: Session):
    cities = db.query(models.City).all()
    return [{"id": c.id, "name": c.name, "province": c.province} for c in cities]

def get_all_provinces(db: Session):
    provinces = db.query(models.City.province).distinct().all()
    return [p[0] for p in provinces]

def get_latest_aqi_ranking(db: Session, province: str = None):
    subquery = db.query(
        models.AirQualityData.city_id,
        func.max(models.AirQualityData.timestamp).label("latest_timestamp")
    ).group_by(models.AirQualityData.city_id).subquery()
    
    query = db.query(
        models.City.id,
        models.City.name,
        models.City.province,
        models.AirQualityData.aqi,
        models.AirQualityData.pm25,
        models.AirQualityData.pm10,
        models.AirQualityData.so2,
        models.AirQualityData.no2,
        models.AirQualityData.co,
        models.AirQualityData.o3,
        models.AirQualityData.timestamp
    ).join(
        subquery,
        (models.AirQualityData.city_id == subquery.c.city_id) & 
        (models.AirQualityData.timestamp == subquery.c.latest_timestamp)
    ).join(models.City)
    
    if province:
        query = query.filter(models.City.province == province)
    
    results = query.order_by(desc(models.AirQualityData.aqi)).all()
    
    return [
        {
            "city_id": r.id,
            "city_name": r.name,
            "province": r.province,
            "aqi": r.aqi,
            "pm25": r.pm25,
            "pm10": r.pm10,
            "so2": r.so2,
            "no2": r.no2,
            "co": r.co,
            "o3": r.o3,
            "timestamp": r.timestamp.isoformat()
        }
        for r in results
    ]

def get_city_air_quality_detail(db: Session, city_id: int):
    city = db.query(models.City).filter(models.City.id == city_id).first()
    if not city:
        return None
    
    latest_data = db.query(models.AirQualityData).filter(
        models.AirQualityData.city_id == city_id
    ).order_by(desc(models.AirQualityData.timestamp)).first()
    
    if not latest_data:
        return None
    
    return {
        "city_id": city.id,
        "city_name": city.name,
        "province": city.province,
        "aqi": latest_data.aqi,
        "pm25": latest_data.pm25,
        "pm10": latest_data.pm10,
        "so2": latest_data.so2,
        "no2": latest_data.no2,
        "co": latest_data.co,
        "o3": latest_data.o3,
        "timestamp": latest_data.timestamp.isoformat()
    }

def get_24h_trends(db: Session, city_id: int):
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    
    data = db.query(models.AirQualityData).filter(
        models.AirQualityData.city_id == city_id,
        models.AirQualityData.timestamp >= twenty_four_hours_ago
    ).order_by(models.AirQualityData.timestamp).all()
    
    return [
        {
            "timestamp": d.timestamp.isoformat(),
            "pm25": d.pm25,
            "pm10": d.pm10,
            "so2": d.so2,
            "no2": d.no2,
            "co": d.co,
            "o3": d.o3
        }
        for d in data
    ]

def get_city_history_data_by_date_range(db: Session, city_id: int, start_date: str, end_date: str):
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
    
    data = db.query(models.AirQualityData).filter(
        models.AirQualityData.city_id == city_id,
        models.AirQualityData.timestamp >= start,
        models.AirQualityData.timestamp <= end
    ).order_by(models.AirQualityData.timestamp).all()
    
    return [
        {
            "timestamp": d.timestamp.isoformat(),
            "aqi": d.aqi,
            "pm25": d.pm25,
            "pm10": d.pm10,
            "so2": d.so2,
            "no2": d.no2,
            "co": d.co,
            "o3": d.o3
        }
        for d in data
    ]
