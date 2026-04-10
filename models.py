from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

# 30个主要城市数据
CITIES_DATA = [
    {"name": "北京", "province": "北京市", "lat": 39.9042, "lng": 116.4074},
    {"name": "上海", "province": "上海市", "lat": 31.2304, "lng": 121.4737},
    {"name": "广州", "province": "广东省", "lat": 23.1291, "lng": 113.2644},
    {"name": "深圳", "province": "广东省", "lat": 22.5431, "lng": 114.0579},
    {"name": "天津", "province": "天津市", "lat": 39.0842, "lng": 117.2009},
    {"name": "重庆", "province": "重庆市", "lat": 29.5630, "lng": 106.5516},
    {"name": "成都", "province": "四川省", "lat": 30.5728, "lng": 104.0668},
    {"name": "武汉", "province": "湖北省", "lat": 30.5928, "lng": 114.3055},
    {"name": "西安", "province": "陕西省", "lat": 34.3416, "lng": 108.9398},
    {"name": "杭州", "province": "浙江省", "lat": 30.2741, "lng": 120.1551},
    {"name": "南京", "province": "江苏省", "lat": 32.0603, "lng": 118.7969},
    {"name": "郑州", "province": "河南省", "lat": 34.7466, "lng": 113.6253},
    {"name": "长沙", "province": "湖南省", "lat": 28.2280, "lng": 112.9388},
    {"name": "沈阳", "province": "辽宁省", "lat": 41.8057, "lng": 123.4315},
    {"name": "青岛", "province": "山东省", "lat": 36.0671, "lng": 120.3826},
    {"name": "济南", "province": "山东省", "lat": 36.6512, "lng": 117.1201},
    {"name": "哈尔滨", "province": "黑龙江省", "lat": 45.8038, "lng": 126.5349},
    {"name": "长春", "province": "吉林省", "lat": 43.8171, "lng": 125.3235},
    {"name": "石家庄", "province": "河北省", "lat": 38.0428, "lng": 114.5149},
    {"name": "太原", "province": "山西省", "lat": 37.8706, "lng": 112.5489},
    {"name": "昆明", "province": "云南省", "lat": 25.0389, "lng": 102.7183},
    {"name": "贵阳", "province": "贵州省", "lat": 26.6470, "lng": 106.6302},
    {"name": "南宁", "province": "广西壮族自治区", "lat": 22.8170, "lng": 108.3665},
    {"name": "福州", "province": "福建省", "lat": 26.0745, "lng": 119.2965},
    {"name": "厦门", "province": "福建省", "lat": 24.4798, "lng": 118.0894},
    {"name": "合肥", "province": "安徽省", "lat": 31.8206, "lng": 117.2272},
    {"name": "南昌", "province": "江西省", "lat": 28.6820, "lng": 115.8579},
    {"name": "兰州", "province": "甘肃省", "lat": 36.0611, "lng": 103.8343},
    {"name": "乌鲁木齐", "province": "新疆维吾尔自治区", "lat": 43.8256, "lng": 87.6168},
    {"name": "呼和浩特", "province": "内蒙古自治区", "lat": 40.8414, "lng": 111.7519},
]


class City(Base):
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    province = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    
    air_quality_records = relationship("AirQualityRecord", back_populates="city", cascade="all, delete-orphan")


class AirQualityRecord(Base):
    __tablename__ = "air_quality_records"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 六项污染物浓度
    pm25 = Column(Float, nullable=False)  # PM2.5 (μg/m³)
    pm10 = Column(Float, nullable=False)  # PM10 (μg/m³)
    so2 = Column(Float, nullable=False)   # SO2 (μg/m³)
    no2 = Column(Float, nullable=False)   # NO2 (μg/m³)
    co = Column(Float, nullable=False)    # CO (mg/m³)
    o3 = Column(Float, nullable=False)    # O3 (μg/m³)
    
    # AQI 综合指数
    aqi = Column(Integer, nullable=False, index=True)
    aqi_level = Column(String(20), nullable=False, index=True)  # 优/良/轻度/中度/重度/严重
    primary_pollutant = Column(String(20), nullable=True)  # 首要污染物
    
    city = relationship("City", back_populates="air_quality_records")
    
    __table_args__ = (
        Index('idx_city_timestamp', 'city_id', 'timestamp'),
    )


# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/air_quality.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建表并插入城市数据"""
    # 确保数据目录存在
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已有城市数据
        if db.query(City).count() == 0:
            for city_data in CITIES_DATA:
                city = City(**city_data)
                db.add(city)
            db.commit()
            print(f"已初始化 {len(CITIES_DATA)} 个城市数据")
    finally:
        db.close()


def get_aqi_level(aqi: int) -> str:
    """根据AQI值获取空气质量等级"""
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


def get_aqi_color(aqi: int) -> str:
    """根据AQI值获取颜色"""
    if aqi <= 50:
        return "#00e400"  # 绿色
    elif aqi <= 100:
        return "#ffff00"  # 黄色
    elif aqi <= 150:
        return "#ff7e00"  # 橙色
    elif aqi <= 200:
        return "#ff0000"  # 红色
    elif aqi <= 300:
        return "#99004c"  # 紫色
    else:
        return "#7e0023"  # 褐红色
