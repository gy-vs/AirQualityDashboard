import csv
import io
import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    init_db, get_db, City, AirQualityRecord, 
    get_aqi_level, get_aqi_color, CITIES_DATA
)
from data_simulator import AirQualitySimulator

# 初始化数据库
init_db()

app = FastAPI(title="城市空气质量监控仪表盘")

# 模板和静态文件
templates = Jinja2Templates(directory="templates")

# 创建静态文件目录
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("data", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """应用启动时生成历史数据"""
    db = next(get_db())
    simulator = AirQualitySimulator(db)
    
    # 检查是否已有数据
    count = db.query(AirQualityRecord).count()
    if count == 0:
        print("正在生成历史数据...")
        records = simulator.generate_historical_data(days=7)
        simulator.save_records(records)
        print(f"已生成 {len(records)} 条历史记录")
    else:
        print(f"数据库已有 {count} 条记录，跳过历史数据生成")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """仪表盘首页"""
    simulator = AirQualitySimulator(db)
    latest_records = simulator.get_latest_records()
    
    # 检查是否有严重污染城市（AQI > 200）
    severe_cities = [r for r in latest_records if r.aqi > 200]
    warning_cities = [r for r in latest_records if 150 < r.aqi <= 200]
    
    # 获取所有省份用于筛选
    provinces = sorted(list(set(c["province"] for c in CITIES_DATA)))
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "records": latest_records,
        "severe_cities": severe_cities,
        "warning_cities": warning_cities,
        "provinces": provinces,
        "get_aqi_color": get_aqi_color,
        "get_aqi_level": get_aqi_level,
    })


@app.get("/city/{city_name}", response_class=HTMLResponse)
async def city_detail(request: Request, city_name: str, db: Session = Depends(get_db)):
    """城市详情页"""
    city = db.query(City).filter(City.name == city_name).first()
    if not city:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"城市 '{city_name}' 不存在"
        })
    
    # 获取最新数据
    latest = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_id == city.id
    ).order_by(AirQualityRecord.timestamp.desc()).first()
    
    # 获取24小时历史数据
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    hourly_data = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_id == city.id,
        AirQualityRecord.timestamp >= twenty_four_hours_ago
    ).order_by(AirQualityRecord.timestamp.asc()).all()
    
    # 获取最近7天每日平均AQI
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_avg = db.query(
        func.date(AirQualityRecord.timestamp).label('date'),
        func.avg(AirQualityRecord.aqi).label('avg_aqi'),
        func.max(AirQualityRecord.aqi).label('max_aqi'),
        func.min(AirQualityRecord.aqi).label('min_aqi')
    ).filter(
        AirQualityRecord.city_id == city.id,
        AirQualityRecord.timestamp >= seven_days_ago
    ).group_by(func.date(AirQualityRecord.timestamp)).all()
    
    return templates.TemplateResponse("city_detail.html", {
        "request": request,
        "city": city,
        "latest": latest,
        "hourly_data": hourly_data,
        "daily_avg": daily_avg,
        "get_aqi_color": get_aqi_color,
    })


@app.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    city: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """历史数据查询页面"""
    cities = db.query(City).order_by(City.name).all()
    
    records = []
    if city and start_date and end_date:
        city_obj = db.query(City).filter(City.name == city).first()
        if city_obj:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            
            records = db.query(AirQualityRecord).filter(
                AirQualityRecord.city_id == city_obj.id,
                AirQualityRecord.timestamp >= start,
                AirQualityRecord.timestamp < end
            ).order_by(AirQualityRecord.timestamp.desc()).all()
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "cities": cities,
        "selected_city": city,
        "start_date": start_date,
        "end_date": end_date,
        "records": records,
        "get_aqi_color": get_aqi_color,
    })


@app.get("/api/cities")
async def get_cities(db: Session = Depends(get_db)):
    """获取所有城市列表"""
    cities = db.query(City).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "province": c.province,
            "lat": c.lat,
            "lng": c.lng
        }
        for c in cities
    ]


@app.get("/api/current")
async def get_current_data(
    province: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取当前空气质量数据"""
    simulator = AirQualitySimulator(db)
    records = simulator.get_latest_records()
    
    result = []
    for r in records:
        if province and r.city.province != province:
            continue
        result.append({
            "city": r.city.name,
            "province": r.city.province,
            "lat": r.city.lat,
            "lng": r.city.lng,
            "aqi": r.aqi,
            "aqi_level": r.aqi_level,
            "aqi_color": get_aqi_color(r.aqi),
            "pm25": r.pm25,
            "pm10": r.pm10,
            "so2": r.so2,
            "no2": r.no2,
            "co": r.co,
            "o3": r.o3,
            "primary_pollutant": r.primary_pollutant,
            "timestamp": r.timestamp.isoformat(),
        })
    
    # 按AQI排序（从高到低）
    result.sort(key=lambda x: x["aqi"], reverse=True)
    
    return result


@app.get("/api/city/{city_name}/hourly")
async def get_city_hourly(city_name: str, db: Session = Depends(get_db)):
    """获取城市24小时历史数据"""
    city = db.query(City).filter(City.name == city_name).first()
    if not city:
        return {"error": "City not found"}
    
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    records = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_id == city.id,
        AirQualityRecord.timestamp >= twenty_four_hours_ago
    ).order_by(AirQualityRecord.timestamp.asc()).all()
    
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "hour": r.timestamp.strftime("%H:%M"),
            "aqi": r.aqi,
            "pm25": r.pm25,
            "pm10": r.pm10,
            "so2": r.so2,
            "no2": r.no2,
            "co": r.co,
            "o3": r.o3,
        }
        for r in records
    ]


@app.get("/api/city/{city_name}/daily")
async def get_city_daily(city_name: str, days: int = 7, db: Session = Depends(get_db)):
    """获取城市每日平均AQI"""
    city = db.query(City).filter(City.name == city_name).first()
    if not city:
        return {"error": "City not found"}
    
    start_date = datetime.now() - timedelta(days=days)
    daily_data = db.query(
        func.date(AirQualityRecord.timestamp).label('date'),
        func.avg(AirQualityRecord.aqi).label('avg_aqi'),
        func.max(AirQualityRecord.aqi).label('max_aqi'),
        func.min(AirQualityRecord.aqi).label('min_aqi')
    ).filter(
        AirQualityRecord.city_id == city.id,
        AirQualityRecord.timestamp >= start_date
    ).group_by(func.date(AirQualityRecord.timestamp)).order_by('date').all()
    
    return [
        {
            "date": str(d.date),
            "avg_aqi": round(d.avg_aqi, 1),
            "max_aqi": d.max_aqi,
            "min_aqi": d.min_aqi,
        }
        for d in daily_data
    ]


@app.get("/api/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    """获取污染预警信息"""
    simulator = AirQualitySimulator(db)
    records = simulator.get_latest_records()
    
    severe = []
    warning = []
    
    for r in records:
        if r.aqi > 200:
            severe.append({
                "city": r.city.name,
                "aqi": r.aqi,
                "level": r.aqi_level,
                "color": get_aqi_color(r.aqi),
            })
        elif r.aqi > 150:
            warning.append({
                "city": r.city.name,
                "aqi": r.aqi,
                "level": r.aqi_level,
                "color": get_aqi_color(r.aqi),
            })
    
    return {
        "severe": severe,
        "warning": warning,
        "has_severe": len(severe) > 0,
        "has_warning": len(warning) > 0,
    }


@app.get("/api/export")
async def export_data(
    city: str,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """导出历史数据为CSV"""
    city_obj = db.query(City).filter(City.name == city).first()
    if not city_obj:
        return {"error": "City not found"}
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    
    records = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_id == city_obj.id,
        AirQualityRecord.timestamp >= start,
        AirQualityRecord.timestamp < end
    ).order_by(AirQualityRecord.timestamp.desc()).all()
    
    # 生成CSV内容
    lines = []
    # 添加BOM以支持Excel中文显示
    lines.append('\ufeff' + ','.join([
        "时间", "城市", "AQI", "空气质量等级", "PM2.5", "PM10", 
        "SO2", "NO2", "CO", "O3", "首要污染物"
    ]))
    
    for r in records:
        line = ','.join([
            r.timestamp.strftime("%Y-%m-%d %H:%M"),
            city_obj.name,
            str(r.aqi),
            r.aqi_level,
            str(r.pm25),
            str(r.pm10),
            str(r.so2),
            str(r.no2),
            str(r.co),
            str(r.o3),
            r.primary_pollutant or "无"
        ])
        lines.append(line)
    
    csv_content = '\n'.join(lines)
    
    # 对中文文件名进行URL编码
    from urllib.parse import quote
    safe_filename = quote(f"{city}_air_quality_{start_date}_{end_date}.csv")
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        }
    )


@app.post("/api/refresh")
async def refresh_data(db: Session = Depends(get_db)):
    """手动刷新数据（生成新的当前时刻数据）"""
    simulator = AirQualitySimulator(db)
    records = simulator.generate_current_data()
    simulator.save_records(records)
    return {"message": f"已生成 {len(records)} 条新记录"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
