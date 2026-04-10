import random
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import City, AirQualityRecord, get_aqi_level, SessionLocal
import threading

PM25_WEIGHT = 0.15
PM10_WEIGHT = 0.1
SO2_WEIGHT = 0.05
NO2_WEIGHT = 0.1
CO_WEIGHT = 0.001
O3_WEIGHT = 0.1

def calculate_aqi_from_pollutants(pm25, pm10, so2, no2, co, o3):
    aqi = (pm25 * PM25_WEIGHT +
           pm10 * PM10_WEIGHT +
           so2 * SO2_WEIGHT +
           no2 * NO2_WEIGHT +
           co * CO_WEIGHT * 1000 +
           o3 * O3_WEIGHT) * 2
    return min(int(aqi), 500)

def generate_realistic_data(city_name):
    city_base_levels = {
        "北京": {"base": 120, "var": 80},
        "上海": {"base": 80, "var": 60},
        "广州": {"base": 70, "var": 50},
        "深圳": {"base": 60, "var": 40},
        "成都": {"base": 90, "var": 70},
        "杭州": {"base": 65, "var": 50},
        "武汉": {"base": 85, "var": 65},
        "西安": {"base": 110, "var": 80},
        "重庆": {"base": 95, "var": 75},
        "南京": {"base": 75, "var": 55},
        "天津": {"base": 100, "var": 70},
        "苏州": {"base": 70, "var": 50},
        "长沙": {"base": 80, "var": 60},
        "郑州": {"base": 115, "var": 85},
        "青岛": {"base": 60, "var": 45},
        "大连": {"base": 55, "var": 40},
        "沈阳": {"base": 95, "var": 75},
        "哈尔滨": {"base": 105, "var": 80},
        "长春": {"base": 90, "var": 70},
        "济南": {"base": 100, "var": 75},
        "太原": {"base": 130, "var": 90},
        "合肥": {"base": 80, "var": 60},
        "福州": {"base": 55, "var": 40},
        "厦门": {"base": 50, "var": 35},
        "南昌": {"base": 75, "var": 55},
        "南宁": {"base": 55, "var": 40},
        "贵阳": {"base": 45, "var": 35},
        "昆明": {"base": 40, "var": 30},
        "兰州": {"base": 140, "var": 100},
        "乌鲁木齐": {"base": 135, "var": 95},
    }
    
    city_config = city_base_levels.get(city_name, {"base": 80, "var": 60})
    base_aqi = city_config["base"]
    variation = city_config["var"]
    
    hour = datetime.now().hour
    if 7 <= hour <= 10 or 17 <= hour <= 20:
        base_aqi *= 1.3
    
    day_factor = random.uniform(0.7, 1.3)
    current_aqi = int((base_aqi + random.randint(-variation, variation)) * day_factor)
    current_aqi = max(10, min(500, current_aqi))
    
    pm25 = current_aqi * random.uniform(0.8, 1.2)
    pm10 = current_aqi * random.uniform(0.7, 1.1)
    so2 = random.uniform(5, 80)
    no2 = random.uniform(10, 120)
    co = random.uniform(0.5, 4.5)
    o3 = random.uniform(20, 200)
    
    calculated_aqi = calculate_aqi_from_pollutants(pm25, pm10, so2, no2, co, o3)
    final_aqi = int(current_aqi * 0.6 + calculated_aqi * 0.4)
    final_aqi = max(0, min(500, final_aqi))
    
    return {
        "pm25": round(pm25, 2),
        "pm10": round(pm10, 2),
        "so2": round(so2, 2),
        "no2": round(no2, 2),
        "co": round(co, 2),
        "o3": round(o3, 2),
        "aqi": final_aqi,
    }

def insert_data_point(db: Session, city, timestamp: datetime):
    data = generate_realistic_data(city["name"])
    
    db_record = AirQualityRecord(
        city_name=city["name"],
        city_code=city["code"],
        province=city["province"],
        aqi=data["aqi"],
        pm25=data["pm25"],
        pm10=data["pm10"],
        so2=data["so2"],
        no2=data["no2"],
        co=data["co"],
        o3=data["o3"],
        level=get_aqi_level(data["aqi"]),
        timestamp=timestamp,
        created_at=datetime.utcnow()
    )
    db.add(db_record)

def generate_historical_data(db: Session, days: int = 7):
    print(f"Generating {days} days of historical data...")
    for city in City.CITIES:
        for day in range(days):
            for hour in range(24):
                timestamp = datetime.now() - timedelta(days=day, hours=hour)
                insert_data_point(db, city, timestamp)
    db.commit()
    print("Historical data generation completed!")

def start_real_time_simulation():
    def simulation_loop():
        db = SessionLocal()
        try:
            while True:
                print("Updating real-time data...")
                for city in City.CITIES:
                    insert_data_point(db, city, datetime.now())
                db.commit()
                time.sleep(60)
        finally:
            db.close()
    
    thread = threading.Thread(target=simulation_loop, daemon=True)
    thread.start()
    print("Real-time simulation started!")

def init_data():
    db = SessionLocal()
    try:
        count = db.query(AirQualityRecord).count()
        if count == 0:
            generate_historical_data(db, days=7)
        start_real_time_simulation()
    finally:
        db.close()
