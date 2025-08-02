# app/main.py
import os
from fastapi import FastAPI
from app.predict import forecast_next_24_hours

app = FastAPI()

@app.get("/")
def root():
    return {"message": "🌦️ Welcome to the Dhaka City Precipitation Forecast API!"}

@app.get("/predict")
def predict():
    return forecast_next_24_hours()

# 👇 Add this only if you're running this file directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

