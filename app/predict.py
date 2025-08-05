# app/predict.py
import pandas as pd

from app.model import load_model
from app.utils import engineer_features, fetch_weather

model = load_model()


def forecast_next_24_hours():
    df = fetch_weather()
    X = engineer_features(df)

    # Make predictions
    preds = model.predict(X)

    # Clip negative predictions and round
    preds = [max(0, round(p, 2)) for p in preds]

    # Add predictions to dataframe
    df["predicted_precipitation"] = preds

    # Add timestamp column
    if "time" in df.columns:
        df["hour"] = pd.to_datetime(df["time"])
    else:
        df["hour"] = pd.date_range(
            start=pd.Timestamp.now(), periods=len(preds), freq="H"
        )

    # Add unit
    df["unit"] = "mm"

    # Format result
    result = (
        df[["hour", "predicted_precipitation", "unit"]]
        .rename(columns={"hour": "timestamp"})
        .to_dict(orient="records")
    )

    return result
