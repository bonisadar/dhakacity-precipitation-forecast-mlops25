import os

assert os.path.exists(__file__), f"{__file__} not found!"

# Set Prefect API URL (default localhost)
os.environ["PREFECT_API_URL"] = os.getenv(
    "PREFECT_API_URL", "http://127.0.0.1:4200/api"
)

from datetime import datetime

import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
import xgboost as xgb
from google.cloud import storage
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from prefect import flow, get_run_logger, task
from prefect.blocks.notifications import SendgridEmail
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split

from utils.config import get_bucket_name, get_sendgrid_block

# ---------------- TASKS ----------------


@task(log_prints=True)
def download_from_gcs(blob_name, local_path):
    logger = get_run_logger()
    bucket_name = get_bucket_name()
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    logger.info(f"Downloaded gs://{bucket_name}/{blob_name} to {local_path}")
    return local_path


@task(log_prints=True)
def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df["time"] = pd.to_datetime(df["time"])
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek
    df["month"] = df["time"].dt.month

    for lag in range(1, 7):
        df[f"temp_lag_{lag}"] = df["temperature_2m"].shift(lag)

    df["humidity_ewm3"] = df["relative_humidity_2m"].ewm(span=3).mean()
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["week_of_year"] = df["time"].dt.isocalendar().week
    df["week_sin"] = np.sin(2 * np.pi * df["week_of_year"] / 52)
    df["week_cos"] = np.cos(2 * np.pi * df["week_of_year"] / 52)
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9]).astype(int)

    df = df.drop(columns=["time"])

    X = df.drop(columns=["precipitation"])
    y = df["precipitation"]
    return X, y


@task(log_prints=True)
def train_model(X, y):
    logger = get_run_logger()
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("dhaka_city_precipitation_forecast_v9")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = xgb.XGBRegressor(objective="reg:squarederror", random_state=42)
    search = GridSearchCV(
        model,
        {
            "n_estimators": [200],
            "max_depth": [7],
            "learning_rate": [0.01],
            "subsample": [0.8],
            "colsample_bytree": [0.8],
        },
        scoring="neg_mean_absolute_error",
        cv=2,
    )

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        search.fit(X_train, y_train)
        best_model = search.best_estimator_
        y_pred = best_model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "mse": mean_squared_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred),
        }

        mlflow.log_metrics(metrics)
        mlflow.log_params(search.best_params_)

        with open("features.txt", "w") as f:
            f.write("\n".join(X_train.columns))
        mlflow.log_artifact("features.txt")
        np.savetxt("y_pred.txt", y_pred)
        mlflow.log_artifact("y_pred.txt")

        signature = infer_signature(X_test, y_pred)

        # Log model artifacts
        mlflow.xgboost.log_model(
            best_model,
            artifact_path="model",
            input_example=X_test.iloc[:5],
            signature=signature,
        )

        # Register the model manually using run_id
        model_uri = f"runs:/{run_id}/model"
        registered_model = mlflow.register_model(
            model_uri=model_uri, name="dhaka_city_precipitation_xgb"
        )

        model_version = registered_model.version

    logger.info(f"Logged new model metrics: {metrics}")
    return metrics, y_pred, model_version


@task(log_prints=True)
def fetch_champion_mae(model_name="dhaka_city_precipitation_xgb"):
    logger = get_run_logger()
    client = MlflowClient()

    try:
        version = client.get_model_version_by_alias(model_name, "champion")
        run = client.get_run(version.run_id)
        return run.data.metrics.get("mae", float("inf"))
    except mlflow.exceptions.RestException:
        logger.info("No existing champion. This will be the first one.")
        return None


@task(log_prints=True)
def push_metrics_to_prometheus(metrics):
    logger = get_run_logger()
    registry = CollectorRegistry()

    Gauge("model_mae", "Model MAE", registry=registry).set(metrics["mae"])
    Gauge("model_r2", "Model R²", registry=registry).set(metrics["r2"])
    Gauge("model_mse", "Model MSE", registry=registry).set(metrics["mse"])

    push_to_gateway(
        "http://127.0.0.1:9091", job="dhaka_weather_model", registry=registry
    )
    logger.info("Metrics pushed to Prometheus via Pushgateway.")


@task(log_prints=True)
def compare_and_update_alias(new_mae, new_version):
    logger = get_run_logger()
    client = MlflowClient()
    old_mae = fetch_champion_mae()

    if old_mae is None or new_mae < old_mae:
        client.set_registered_model_alias(
            "dhaka_city_precipitation_xgb", "champion", new_version
        )
        logger.info("New model promoted as champion.")
        return "New model promoted as champion."
    else:
        logger.info("Old model retained as champion.")
        return "Old model retained (new model not promoted)."


# ---------------- FLOW ----------------


@flow(name="train_and_compare")
def train_and_compare():
    logger = get_run_logger()
    flow_start_time = datetime.now()

    blob_name = "raw/raw_dhaka_weather.csv"
    local_path = "/tmp/latest_weather.csv"
    df_path = download_from_gcs(blob_name, local_path)
    df = pd.read_csv(df_path)

    X, y = engineer_features(df)
    metrics_new, _, model_version = train_model(X, y)

    result = compare_and_update_alias(metrics_new["mae"], model_version)
    push_metrics_to_prometheus(metrics_new)

    flow_end_time = datetime.now()
    sendgrid_block = SendgridEmail.load(get_sendgrid_block())

    body = "☁️ Dhaka Precipitation Forecast Model Training Completed"
    subject = (
        f"Dhaka City Precipitation Forecast Training\n\n"
        f"Start Time: {flow_start_time}\n"
        f"End Time: {flow_end_time}\n\n"
        f"Model Metrics:\n"
        f" - MAE: {metrics_new['mae']:.4f}\n"
        f" - MSE: {metrics_new['mse']:.4f}\n"
        f" - R²:  {metrics_new['r2']:.4f}\n\n"
        f"Model Selection Result:\n"
        f"{result}\n"
    )

    try:
        sendgrid_block.notify(subject, body)
        logger.info("Notification sent via SendGrid.")
    except Exception as e:
        logger.error(f"SendGrid notification failed: {e}")


if __name__ == "__main__":
    train_and_compare()
