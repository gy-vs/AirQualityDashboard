from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import io
import csv
from .models import SessionLocal, City, AirQualityRecord, get_aqi_level, get_level_color
from .simulator import init_data

app = FastAPI(title="城市空气质量监控仪表盘")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    init_data()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/cities")
def get_cities():
    provinces = list(set([city["province"] for city in City.CITIES]))
    provinces.sort()
    return {
        "cities": City.CITIES,
        "provinces": provinces
    }

def get_latest_data(db: Session, province: str = None):
    latest_records = []
    for city in City.CITIES:
        if province and city["province"] != province:
            continue
        record = db.query(AirQualityRecord).filter(
            AirQualityRecord.city_name == city["name"]
        ).order_by(desc(AirQualityRecord.timestamp)).first()
        if record:
            latest_records.append({
                "city_name": record.city_name,
                "province": record.province,
                "aqi": record.aqi,
                "level": record.level,
                "color": get_level_color(record.level),
                "timestamp": record.timestamp.isoformat(),
                "pm25": record.pm25,
                "pm10": record.pm10,
                "so2": record.so2,
                "no2": record.no2,
                "co": record.co,
                "o3": record.o3
            })
    latest_records.sort(key=lambda x: x["aqi"], reverse=True)
    return latest_records

@app.get("/api/latest")
def get_latest_data_api(province: str = None, db: Session = Depends(get_db)):
    return get_latest_data(db, province)

@app.get("/api/ranking")
def get_aqi_ranking(province: str = None, db: Session = Depends(get_db)):
    data = get_latest_data(db, province)
    return data

@app.get("/api/high-pollution")
def get_high_pollution_cities(db: Session = Depends(get_db)):
    data = get_latest_data(db, None)
    high_aqi = [d for d in data if d["aqi"] > 150]
    critical = [d for d in data if d["aqi"] > 200]
    return {
        "high_aqi_count": len(high_aqi),
        "critical_count": len(critical),
        "high_aqi_cities": high_aqi,
        "critical_cities": critical
    }

@app.get("/api/city/{city_name}/24h")
def get_city_24h(city_name: str, db: Session = Depends(get_db)):
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    records = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_name == city_name,
        AirQualityRecord.timestamp >= start_time,
        AirQualityRecord.timestamp <= end_time
    ).order_by(AirQualityRecord.timestamp).all()
    
    timestamps = []
    pm25_data = []
    pm10_data = []
    so2_data = []
    no2_data = []
    co_data = []
    o3_data = []
    
    for r in records:
        timestamps.append(r.timestamp.strftime("%H:%M"))
        pm25_data.append(float(r.pm25))
        pm10_data.append(float(r.pm10))
        so2_data.append(float(r.so2))
        no2_data.append(float(r.no2))
        co_data.append(float(r.co))
        o3_data.append(float(r.o3))
    
    return {
        "timestamps": timestamps,
        "pm25": pm25_data,
        "pm10": pm10_data,
        "so2": so2_data,
        "no2": no2_data,
        "co": co_data,
        "o3": o3_data
    }

@app.get("/api/city/{city_name}/7d")
def get_city_7d(city_name: str, db: Session = Depends(get_db)):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    records = db.query(
        func.date(AirQualityRecord.timestamp).label('date'),
        func.avg(AirQualityRecord.aqi).label('avg_aqi'),
        func.max(AirQualityRecord.aqi).label('max_aqi')
    ).filter(
        AirQualityRecord.city_name == city_name,
        AirQualityRecord.timestamp >= start_time,
        AirQualityRecord.timestamp <= end_time
    ).group_by('date').order_by('date').all()
    
    dates = []
    avg_aqi = []
    max_aqi = []
    
    for r in records:
        dates.append(str(r.date))
        avg_aqi.append(round(float(r.avg_aqi), 1))
        max_aqi.append(round(float(r.max_aqi), 1))
    
    return {
        "dates": dates,
        "avg_aqi": avg_aqi,
        "max_aqi": max_aqi
    }

@app.get("/api/city/{city_name}/radar")
def get_city_radar(city_name: str, db: Session = Depends(get_db)):
    record = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_name == city_name
    ).order_by(desc(AirQualityRecord.timestamp)).first()
    
    if record:
        max_values = {"pm25": 250, "pm10": 350, "so2": 800, "no2": 700, "co": 15, "o3": 400}
        return {
            "indicators": [
                {"name": "PM2.5", "max": max_values["pm25"]},
                {"name": "PM10", "max": max_values["pm10"]},
                {"name": "SO2", "max": max_values["so2"]},
                {"name": "NO2", "max": max_values["no2"]},
                {"name": "CO", "max": max_values["co"]},
                {"name": "O3", "max": max_values["o3"]}
            ],
            "values": [
                float(record.pm25),
                float(record.pm10),
                float(record.so2),
                float(record.no2),
                float(record.co),
                float(record.o3)
            ]
        }
    return {"indicators": [], "values": []}

def query_history_data(city: str, start_date: str, end_date: str, db: Session):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        return {"error": "Invalid date format"}
    
    records = db.query(AirQualityRecord).filter(
        AirQualityRecord.city_name == city,
        AirQualityRecord.timestamp >= start,
        AirQualityRecord.timestamp < end
    ).order_by(AirQualityRecord.timestamp).all()
    
    result = []
    for r in records:
        result.append({
            "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "aqi": r.aqi,
            "level": r.level,
            "pm25": r.pm25,
            "pm10": r.pm10,
            "so2": r.so2,
            "no2": r.no2,
            "co": r.co,
            "o3": r.o3
        })
    return result

@app.get("/api/history")
def get_history_data(
    city: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db)
):
    return query_history_data(city, start_date, end_date, db)

@app.get("/api/export")
def export_csv(
    city: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db)
):
    data = query_history_data(city, start_date, end_date, db)
    if "error" in data:
        return data
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Timestamp", "AQI", "Level", "PM2.5", "PM10", "SO2", "NO2", "CO", "O3"])
    for row in data:
        writer.writerow([
            row["timestamp"],
            row["aqi"],
            row["level"],
            row["pm25"],
            row["pm10"],
            row["so2"],
            row["no2"],
            row["co"],
            row["o3"]
        ])
    
    output.seek(0)
    from urllib.parse import quote
    safe_filename = quote(f"air_quality_{city}_{start_date}_{end_date}.csv")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"}
    )

@app.get("/city/{city_name}", response_class=HTMLResponse)
async def city_detail(request: Request, city_name: str):
    return templates.TemplateResponse("city.html", {"request": request, "city_name": city_name})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})
