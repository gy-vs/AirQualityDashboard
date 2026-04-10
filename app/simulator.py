import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

CITIES = [
    ("北京", "北京市"), ("上海", "上海市"), ("广州", "广东省"), ("深圳", "广东省"),
    ("成都", "四川省"), ("杭州", "浙江省"), ("武汉", "湖北省"), ("西安", "陕西省"),
    ("重庆", "重庆市"), ("南京", "江苏省"), ("天津", "天津市"), ("苏州", "江苏省"),
    ("长沙", "湖南省"), ("郑州", "河南省"), ("济南", "山东省"), ("青岛", "山东省"),
    ("哈尔滨", "黑龙江省"), ("沈阳", "辽宁省"), ("长春", "吉林省"), ("大连", "辽宁省"),
    ("合肥", "安徽省"), ("福州", "福建省"), ("厦门", "福建省"), ("南昌", "江西省"),
    ("南宁", "广西壮族自治区"), ("昆明", "云南省"), ("贵阳", "贵州省"), ("兰州", "甘肃省"),
    ("乌鲁木齐", "新疆维吾尔自治区"), ("呼和浩特", "内蒙古自治区")
]

def calculate_aqi(pm25, pm10, so2, no2, co, o3):
    def get_aqi_level(concentration, breakpoints):
        for i, (c_low, c_high, aqi_low, aqi_high) in enumerate(breakpoints):
            if c_low <= concentration <= c_high:
                return round(((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low)
        return 500
    
    pm25_breaks = [(0, 12, 0, 50), (12.1, 35, 51, 100), (35.1, 55, 101, 150),
                   (55.1, 150, 151, 200), (150.1, 250, 201, 300), (250.1, 500, 301, 500)]
    pm10_breaks = [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
                   (255, 354, 151, 200), (355, 424, 201, 300), (425, 600, 301, 500)]
    so2_breaks = [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
                  (186, 304, 151, 200), (305, 604, 201, 300), (605, 1000, 301, 500)]
    no2_breaks = [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
                  (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2000, 301, 500)]
    co_breaks = [(0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
                 (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)]
    o3_breaks = [(0, 160, 0, 50), (161, 200, 51, 100), (201, 300, 101, 150),
                 (301, 400, 151, 200), (401, 800, 201, 300), (801, 1200, 301, 500)]
    
    aqi_values = [
        get_aqi_level(pm25, pm25_breaks),
        get_aqi_level(pm10, pm10_breaks),
        get_aqi_level(so2, so2_breaks),
        get_aqi_level(no2, no2_breaks),
        get_aqi_level(co, co_breaks),
        get_aqi_level(o3, o3_breaks)
    ]
    
    return max(aqi_values)

def initialize_cities():
    db = SessionLocal()
    existing_cities = db.query(models.City).count()
    if existing_cities == 0:
        for city_name, province in CITIES:
            city = models.City(name=city_name, province=province)
            db.add(city)
        db.commit()
    db.close()

def generate_air_quality_data():
    db = SessionLocal()
    cities = db.query(models.City).all()
    
    for city in cities:
        pm25 = random.uniform(5, 200) + random.uniform(-20, 20)
        pm25 = max(5, min(300, pm25))
        pm10 = random.uniform(10, 250) + random.uniform(-30, 30)
        pm10 = max(10, min(400, pm10))
        so2 = random.uniform(2, 80)
        no2 = random.uniform(10, 120)
        co = random.uniform(0.5, 10)
        o3 = random.uniform(20, 250)
        
        aqi = calculate_aqi(pm25, pm10, so2, no2, co, o3)
        
        data = models.AirQualityData(
            city_id=city.id,
            pm25=round(pm25, 2),
            pm10=round(pm10, 2),
            so2=round(so2, 2),
            no2=round(no2, 2),
            co=round(co, 2),
            o3=round(o3, 2),
            aqi=aqi,
            timestamp=datetime.utcnow()
        )
        db.add(data)
    
    db.commit()
    db.close()

def generate_historical_data():
    db = SessionLocal()
    cities = db.query(models.City).all()
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    
    current_time = start_time
    while current_time <= end_time:
        for city in cities:
            pm25 = random.uniform(5, 200)
            pm10 = random.uniform(10, 250)
            so2 = random.uniform(2, 80)
            no2 = random.uniform(10, 120)
            co = random.uniform(0.5, 10)
            o3 = random.uniform(20, 250)
            aqi = calculate_aqi(pm25, pm10, so2, no2, co, o3)
            
            data = models.AirQualityData(
                city_id=city.id,
                pm25=round(pm25, 2),
                pm10=round(pm10, 2),
                so2=round(so2, 2),
                no2=round(no2, 2),
                co=round(co, 2),
                o3=round(o3, 2),
                aqi=aqi,
                timestamp=current_time
            )
            db.add(data)
        
        current_time += timedelta(hours=1)
    
    db.commit()
    db.close()
