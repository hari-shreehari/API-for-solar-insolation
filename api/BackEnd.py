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

gradio_client = GradioClient("ShreehariS754/X-Helios-Gradio")

@app.get("/")
async def root():
    return {"message": "Blank Space"}

class DataRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int

@app.post("/api/get-data/")
async def get_data(request: DataRequest):
    year = request.year
    month = request.month
    day = request.day
    hour = request.hour

    # Validate year
    if not (2009 <= year <= 2023):
        return JSONResponse(
            content={"status": "error", "message": "Year must be between 2009 and 2023"},
            status_code=400
        )

    try:
        # Query the Supabase table using the provided parameters
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
            gradio_prediction = round((float(gradio_response.split()[-1])/(30*24))*1000, 3)

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
