from fastapi import FastAPI, Depends, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models, crud, simulator
from contextlib import asynccontextmanager
import threading
import time
import io
import csv
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    simulator.initialize_cities()
    
    def run_simulator():
        while True:
            simulator.generate_air_quality_data()
            time.sleep(10)
    
    simulator_thread = threading.Thread(target=run_simulator, daemon=True)
    simulator_thread.start()
    
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.cache = None

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.get("/api/cities")
def get_cities(db: Session = Depends(get_db)):
    return crud.get_all_cities(db)

@app.get("/api/provinces")
def get_provinces(db: Session = Depends(get_db)):
    return crud.get_all_provinces(db)

@app.get("/api/aqi-ranking")
def get_aqi_ranking(province: str = None, db: Session = Depends(get_db)):
    return crud.get_latest_aqi_ranking(db, province)

@app.get("/api/city/{city_id}/detail")
def get_city_detail(city_id: int, db: Session = Depends(get_db)):
    return crud.get_city_air_quality_detail(db, city_id)

@app.get("/api/city/{city_id}/history")
def get_city_history(city_id: int, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    if start_date and end_date:
        return crud.get_city_history_data_by_date_range(db, city_id, start_date, end_date)
    return crud.get_city_history_data_by_date_range(db, city_id, 
        (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d'),
        datetime.utcnow().strftime('%Y-%m-%d'))

@app.get("/api/city/{city_id}/export")
def export_city_data(city_id: int, start_date: str, end_date: str, db: Session = Depends(get_db)):
    from datetime import datetime
    
    history_data = crud.get_city_history_data_by_date_range(db, city_id, start_date, end_date)
    city = db.query(models.City).filter(models.City.id == city_id).first()
    
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'AQI', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'])
    for row in history_data:
        writer.writerow([
            row['timestamp'],
            row['aqi'],
            row['pm25'],
            row['pm10'],
            row['so2'],
            row['no2'],
            row['co'],
            row['o3']
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={city.name}_air_quality_{start_date}_{end_date}.csv"}
    )

@app.get("/api/city/{city_id}/24h-trends")
def get_24h_trends(city_id: int, db: Session = Depends(get_db)):
    return crud.get_24h_trends(db, city_id)
