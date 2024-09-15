from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from gradio_client import Client as GradioClient

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

@app.get("/")
async def root():
    return {"message": "Blank Space"}

class DataRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int

def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def is_valid_day(year, month, day):
    days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if month == 2:
        if is_leap_year(year):
            return 1 <= day <= 29
        else:
            return 1 <= day <= 28
    return 1 <= day <= days_in_month.get(month, 31)

@app.post("/api/get-data/")
async def get_data(request: DataRequest):
    year = request.year
    month = request.month
    day = request.day
    hour = request.hour

    if month < 0 or day < 0 or hour < 0:
        return JSONResponse(
            content={"status": "error", "message": "Month, day, and hour must be non-negative values"},
            status_code=400
        )

    if not (1 <= month <= 12):
        return JSONResponse(
            content={"status": "error", "message": "Month must be between 1 and 12"},
            status_code=400
        )

    if not is_valid_day(year, month, day):
        return JSONResponse(
            content={"status": "error", "message": f"Invalid day for the month {month}. Please enter a valid day."},
            status_code=400
        )

    if not (0 <= hour < 24):
        return JSONResponse(
            content={"status": "error", "message": "Hour must be between 0 and 23"},
            status_code=400
        )

    try:
        if not (2009 <= year <= 2023):
            client = GradioClient("ShreehariS754/Timely_Solar_Predictor")
            result = client.predict(
                year=year,
                month=month,
                day=day,
                hour=hour,
                api_name="/predict"
            )
            
            final_prediction = round(float(result), 3) if float(result) > 10 else 0

            return {
                "status": "success",
                "data": {
                    "solar_insolation": f"{final_prediction} watts/hr"
                }
            }
            
        gradio_client = GradioClient("ShreehariS754/X-Helios-Gradio")
        response = supabase.table("Hourly_weather").select("*").eq("year", year).eq("month", month).eq("day", day).eq("hour", hour).execute()
        data = response.dict().get('data', [])

        if not data:
            return JSONResponse(
                content={"status": "error", "message": "Data not found"},
                status_code=404
            )

        weather_data = data[0]

        for key in weather_data:
            try:
                weather_data[key] = float(weather_data[key])
            except ValueError:
                continue

        factors_to_check = ['clearsky_dhi', 'clearsky_dni', 'clearsky_ghi', 'clearsky_gti', 'dhi', 'dni', 'ghi', 'gti']
        if all(weather_data[factor] == 0 for factor in factors_to_check) or all(v == 0 for v in weather_data.values()):
            gradio_prediction = 0
        else:
            gradio_response = gradio_client.predict(
                weather_data['air_temp'],
                weather_data['albedo'],
                weather_data['azimuth'],
                weather_data['clearsky_dhi'],
                weather_data['clearsky_dni'],
                weather_data['clearsky_ghi'],
                weather_data['clearsky_gti'],
                weather_data['cloud_opacity'],
                weather_data['dhi'],
                weather_data['dni'],
                weather_data['ghi'],
                weather_data['gti'],
                weather_data['precipitation_rate'],
                weather_data['relative_humidity'],
                weather_data['zenith'],
                api_name="/predict"
            )
            gradio_prediction = round((float(gradio_response.split()[-1]) / (30 * 24)) * 1000, 3)

        return {
            "status": "success",
            "data": {
                "weather_data": data,
                "solar_insolation": f"{gradio_prediction} watts/hr"
            }
        }

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Error fetching data or making prediction: {str(e)}"},
            status_code=500
        )
