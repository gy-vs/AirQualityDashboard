from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./air_quality.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class City:
    CITIES = [
        {"name": "北京", "province": "北京", "code": "110000"},
        {"name": "上海", "province": "上海", "code": "310000"},
        {"name": "广州", "province": "广东", "code": "440100"},
        {"name": "深圳", "province": "广东", "code": "440300"},
        {"name": "成都", "province": "四川", "code": "510100"},
        {"name": "杭州", "province": "浙江", "code": "330100"},
        {"name": "武汉", "province": "湖北", "code": "420100"},
        {"name": "西安", "province": "陕西", "code": "610100"},
        {"name": "重庆", "province": "重庆", "code": "500000"},
        {"name": "南京", "province": "江苏", "code": "320100"},
        {"name": "天津", "province": "天津", "code": "120000"},
        {"name": "苏州", "province": "江苏", "code": "320500"},
        {"name": "长沙", "province": "湖南", "code": "430100"},
        {"name": "郑州", "province": "河南", "code": "410100"},
        {"name": "青岛", "province": "山东", "code": "370200"},
        {"name": "大连", "province": "辽宁", "code": "210200"},
        {"name": "沈阳", "province": "辽宁", "code": "210100"},
        {"name": "哈尔滨", "province": "黑龙江", "code": "230100"},
        {"name": "长春", "province": "吉林", "code": "220100"},
        {"name": "济南", "province": "山东", "code": "370100"},
        {"name": "太原", "province": "山西", "code": "140100"},
        {"name": "合肥", "province": "安徽", "code": "340100"},
        {"name": "福州", "province": "福建", "code": "350100"},
        {"name": "厦门", "province": "福建", "code": "350200"},
        {"name": "南昌", "province": "江西", "code": "360100"},
        {"name": "南宁", "province": "广西", "code": "450100"},
        {"name": "贵阳", "province": "贵州", "code": "520100"},
        {"name": "昆明", "province": "云南", "code": "530100"},
        {"name": "兰州", "province": "甘肃", "code": "620100"},
        {"name": "乌鲁木齐", "province": "新疆", "code": "650100"},
    ]

class AirQualityRecord(Base):
    __tablename__ = "air_quality_records"

    id = Column(Integer, primary_key=True, index=True)
    city_name = Column(String, index=True)
    city_code = Column(String, index=True)
    province = Column(String, index=True)
    aqi = Column(Integer)
    pm25 = Column(Float)
    pm10 = Column(Float)
    so2 = Column(Float)
    no2 = Column(Float)
    co = Column(Float)
    o3 = Column(Float)
    level = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_aqi_level(aqi):
    if aqi <= 50:
        return "优"
    elif aqi <= 100:
        return "良"
    elif aqi <= 150:
        return "轻度污染"
    elif aqi <= 200:
        return "中度污染"
    elif aqi <= 300:
        return "重度污染"
    else:
        return "严重污染"

def get_level_color(level):
    colors = {
        "优": "#00e400",
        "良": "#ffff00",
        "轻度污染": "#ff7e00",
        "中度污染": "#ff0000",
        "重度污染": "#99004c",
        "严重污染": "#7e0023"
    }
    return colors.get(level, "#00e400")

Base.metadata.create_all(bind=engine)
