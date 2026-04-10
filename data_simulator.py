import random
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import City, AirQualityRecord, get_aqi_level, CITIES_DATA


class AirQualitySimulator:
    """空气质量数据模拟器"""
    
    # 各城市基础污染水平（模拟不同城市的工业/地理特征）
    CITY_BASE_PROFILES = {
        "北京": {"base_aqi": 85, "variance": 40, "pollution_type": "pm25"},
        "上海": {"base_aqi": 75, "variance": 30, "pollution_type": "pm25"},
        "广州": {"base_aqi": 65, "variance": 25, "pollution_type": "no2"},
        "深圳": {"base_aqi": 55, "variance": 20, "pollution_type": "o3"},
        "天津": {"base_aqi": 90, "variance": 35, "pollution_type": "pm25"},
        "重庆": {"base_aqi": 80, "variance": 30, "pollution_type": "pm25"},
        "成都": {"base_aqi": 95, "variance": 35, "pollution_type": "pm25"},
        "武汉": {"base_aqi": 85, "variance": 30, "pollution_type": "pm25"},
        "西安": {"base_aqi": 100, "variance": 40, "pollution_type": "pm25"},
        "杭州": {"base_aqi": 70, "variance": 25, "pollution_type": "pm25"},
        "南京": {"base_aqi": 80, "variance": 30, "pollution_type": "pm25"},
        "郑州": {"base_aqi": 110, "variance": 45, "pollution_type": "pm25"},
        "长沙": {"base_aqi": 75, "variance": 25, "pollution_type": "pm25"},
        "沈阳": {"base_aqi": 85, "variance": 35, "pollution_type": "pm10"},
        "青岛": {"base_aqi": 70, "variance": 25, "pollution_type": "pm10"},
        "济南": {"base_aqi": 95, "variance": 35, "pollution_type": "pm25"},
        "哈尔滨": {"base_aqi": 90, "variance": 40, "pollution_type": "pm10"},
        "长春": {"base_aqi": 85, "variance": 35, "pollution_type": "pm10"},
        "石家庄": {"base_aqi": 120, "variance": 50, "pollution_type": "pm25"},
        "太原": {"base_aqi": 105, "variance": 40, "pollution_type": "pm25"},
        "昆明": {"base_aqi": 50, "variance": 15, "pollution_type": "o3"},
        "贵阳": {"base_aqi": 60, "variance": 20, "pollution_type": "no2"},
        "南宁": {"base_aqi": 65, "variance": 20, "pollution_type": "pm10"},
        "福州": {"base_aqi": 55, "variance": 18, "pollution_type": "o3"},
        "厦门": {"base_aqi": 50, "variance": 15, "pollution_type": "o3"},
        "合肥": {"base_aqi": 80, "variance": 30, "pollution_type": "pm25"},
        "南昌": {"base_aqi": 70, "variance": 25, "pollution_type": "pm25"},
        "兰州": {"base_aqi": 95, "variance": 35, "pollution_type": "pm10"},
        "乌鲁木齐": {"base_aqi": 100, "variance": 40, "pollution_type": "pm10"},
        "呼和浩特": {"base_aqi": 85, "variance": 35, "pollution_type": "pm10"},
    }
    
    # IAQI 计算 breakpoints (根据 GB 3095-2012)
    BREAKPOINTS = {
        "pm25": [(0, 35, 0, 50), (35, 75, 50, 100), (75, 115, 100, 150), 
                 (115, 150, 150, 200), (150, 250, 200, 300), (250, 500, 300, 500)],
        "pm10": [(0, 50, 0, 50), (50, 150, 50, 100), (150, 250, 100, 150),
                 (250, 350, 150, 200), (350, 420, 200, 300), (420, 600, 300, 500)],
        "so2": [(0, 50, 0, 50), (50, 150, 50, 100), (150, 475, 100, 150),
                (475, 800, 150, 200), (800, 1600, 200, 300), (1600, 2620, 300, 500)],
        "no2": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 150),
                (180, 280, 150, 200), (280, 565, 200, 300), (565, 940, 300, 500)],
        "co": [(0, 2, 0, 50), (2, 4, 50, 100), (4, 14, 100, 150),
               (14, 24, 150, 200), (24, 36, 200, 300), (36, 60, 300, 500)],
        "o3": [(0, 100, 0, 50), (100, 160, 50, 100), (160, 215, 100, 150),
               (215, 265, 150, 200), (265, 800, 200, 300)],
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_iaqi(self, pollutant: str, concentration: float) -> int:
        """计算单项污染物的 IAQI"""
        if pollutant not in self.BREAKPOINTS:
            return 0
        
        for bp_low, bp_high, iaqi_low, iaqi_high in self.BREAKPOINTS[pollutant]:
            if bp_low <= concentration <= bp_high:
                iaqi = ((iaqi_high - iaqi_low) / (bp_high - bp_low)) * (concentration - bp_low) + iaqi_low
                return int(round(iaqi))
        
        # 超出范围，返回最大值
        return 500
    
    def generate_pollutant_data(self, city_name: str, base_aqi: int) -> dict:
        """生成六项污染物浓度数据"""
        profile = self.CITY_BASE_PROFILES.get(city_name, {"base_aqi": 70, "variance": 30, "pollution_type": "pm25"})
        pollution_type = profile["pollution_type"]
        
        # 根据基础AQI反推各项污染物浓度
        ratio = base_aqi / 100.0
        
        # 生成各项污染物浓度（带随机波动）
        pm25 = max(5, base_aqi * 0.6 + random.gauss(0, base_aqi * 0.15))
        pm10 = max(10, base_aqi * 0.9 + random.gauss(0, base_aqi * 0.2))
        so2 = max(3, base_aqi * 0.3 + random.gauss(0, base_aqi * 0.1))
        no2 = max(10, base_aqi * 0.4 + random.gauss(0, base_aqi * 0.12))
        co = max(0.3, base_aqi * 0.03 + random.gauss(0, base_aqi * 0.01))
        o3 = max(20, 80 + random.gauss(0, 30))
        
        # 根据城市污染类型调整
        if pollution_type == "pm25":
            pm25 *= 1.2
        elif pollution_type == "pm10":
            pm10 *= 1.3
        elif pollution_type == "no2":
            no2 *= 1.4
        elif pollution_type == "o3":
            o3 *= 1.3
        
        return {
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "so2": round(so2, 1),
            "no2": round(no2, 1),
            "co": round(co, 2),
            "o3": round(o3, 1),
        }
    
    def calculate_aqi(self, pollutants: dict) -> tuple:
        """计算 AQI 和首要污染物"""
        iaqi_values = {}
        
        for pollutant, concentration in pollutants.items():
            iaqi_values[pollutant] = self.calculate_iaqi(pollutant, concentration)
        
        # AQI 取最大值
        aqi = max(iaqi_values.values())
        
        # 找出首要污染物
        primary_pollutants = [p for p, v in iaqi_values.items() if v == aqi and v > 50]
        primary_pollutant = ",".join(primary_pollutants) if primary_pollutants else None
        
        return aqi, primary_pollutant
    
    def generate_current_data(self) -> list:
        """生成当前时刻所有城市的空气质量数据"""
        records = []
        cities = self.db.query(City).all()
        
        for city in cities:
            profile = self.CITY_BASE_PROFILES.get(city.name, {"base_aqi": 70, "variance": 30, "pollution_type": "pm25"})
            
            # 添加时间波动（模拟早晚高峰、天气影响）
            hour = datetime.now().hour
            time_factor = 1.0
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # 早晚高峰
                time_factor = 1.15
            elif 0 <= hour <= 5:  # 夜间
                time_factor = 0.85
            
            # 随机波动
            variance = profile["variance"]
            base_aqi = profile["base_aqi"] * time_factor + random.gauss(0, variance * 0.3)
            base_aqi = max(15, min(500, base_aqi))  # 限制在合理范围
            
            # 生成污染物数据
            pollutants = self.generate_pollutant_data(city.name, base_aqi)
            
            # 计算AQI
            aqi, primary_pollutant = self.calculate_aqi(pollutants)
            
            record = AirQualityRecord(
                city_id=city.id,
                timestamp=datetime.now(),
                pm25=pollutants["pm25"],
                pm10=pollutants["pm10"],
                so2=pollutants["so2"],
                no2=pollutants["no2"],
                co=pollutants["co"],
                o3=pollutants["o3"],
                aqi=aqi,
                aqi_level=get_aqi_level(aqi),
                primary_pollutant=primary_pollutant
            )
            records.append(record)
        
        return records
    
    def generate_historical_data(self, days: int = 7):
        """生成历史数据（用于初始化）"""
        records = []
        cities = self.db.query(City).all()
        now = datetime.now()
        
        for day_offset in range(days, -1, -1):
            date = now - timedelta(days=day_offset)
            
            # 每天生成24小时的数据（每小时的整点）
            for hour in range(24):
                timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # 跳过未来的时间
                if timestamp > now:
                    continue
                
                for city in cities:
                    profile = self.CITY_BASE_PROFILES.get(city.name, {"base_aqi": 70, "variance": 30, "pollution_type": "pm25"})
                    
                    # 时间因子
                    time_factor = 1.0
                    if 7 <= hour <= 9 or 17 <= hour <= 19:
                        time_factor = 1.15
                    elif 0 <= hour <= 5:
                        time_factor = 0.85
                    
                    # 添加日期波动（模拟天气变化）
                    day_factor = 1 + 0.2 * math.sin(day_offset * 0.5 + city.id)
                    
                    variance = profile["variance"]
                    base_aqi = profile["base_aqi"] * time_factor * day_factor + random.gauss(0, variance * 0.4)
                    base_aqi = max(15, min(500, base_aqi))
                    
                    pollutants = self.generate_pollutant_data(city.name, base_aqi)
                    aqi, primary_pollutant = self.calculate_aqi(pollutants)
                    
                    record = AirQualityRecord(
                        city_id=city.id,
                        timestamp=timestamp,
                        pm25=pollutants["pm25"],
                        pm10=pollutants["pm10"],
                        so2=pollutants["so2"],
                        no2=pollutants["no2"],
                        co=pollutants["co"],
                        o3=pollutants["o3"],
                        aqi=aqi,
                        aqi_level=get_aqi_level(aqi),
                        primary_pollutant=primary_pollutant
                    )
                    records.append(record)
        
        return records
    
    def save_records(self, records: list):
        """保存记录到数据库"""
        for record in records:
            self.db.add(record)
        self.db.commit()
    
    def get_latest_records(self) -> list:
        """获取各城市最新的空气质量数据"""
        from sqlalchemy import func
        
        # 子查询：获取每个城市的最新记录时间
        subquery = self.db.query(
            AirQualityRecord.city_id,
            func.max(AirQualityRecord.timestamp).label('max_timestamp')
        ).group_by(AirQualityRecord.city_id).subquery()
        
        # 主查询：获取最新记录
        latest_records = self.db.query(AirQualityRecord).join(
            subquery,
            (AirQualityRecord.city_id == subquery.c.city_id) &
            (AirQualityRecord.timestamp == subquery.c.max_timestamp)
        ).all()
        
        return latest_records
