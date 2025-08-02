import os
assert os.path.exists(__file__), f"{__file__} not found!"

# Set dynamically from env or fallback
os.environ["PREFECT_API_URL"] = os.getenv("PREFECT_API_URL", "http://127.0.0.1:4200/api")


from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prefect import flow, task, get_run_logger
from google.cloud import storage
import pandas as pd
import numpy as np
import mlflow
from mlflow.tracking import MlflowClient
import mlflow.xgboost
import xgboost as xgb
from mlflow.models import infer_signature
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from utils.config import get_bucket_name
from prefect.blocks.notifications import SendgridEmail

# -------------- TASK DEFINITIONS ----------------

@task(log_prints=True)
def ensure_model_registered(model_name="dhaka_city_precipitation_xgb"):
    logger = get_run_logger()
    client = MlflowClient()
    try:
        client.get_registered_model(model_name)
        logger.info(f"Model '{model_name}' already registered.")
    except mlflow.exceptions.RestException as e:
        if "RESOURCE_DOES_NOT_EXIST" in str(e):
            logger.info(f"Registering new model: {model_name}")
            client.create_registered_model(model_name)
        else:
            logger.error("Unexpected error while checking model registration.")
            raise

@task
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
def upload_y_pred_to_gcs(local_file, destination_blob_name):
    logger = get_run_logger()
    bucket_name = get_bucket_name()
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file)
    logger.info(f"Uploaded {local_file} to gs://{bucket_name}/{destination_blob_name}")

@task(log_prints=True)
def fetch_last_model_metrics(model_name="dhaka_city_precipitation_xgb"):
    logger = get_run_logger()
    client = MlflowClient()
    versions = client.get_latest_versions(model_name, stages=[])
    if len(versions) < 1:
        logger.info("No previous model version found.")
        return None, None

    previous_version = sorted(versions, key=lambda v: int(v.version))[-1]
    previous_run = client.get_run(previous_version.run_id)
    metrics = previous_run.data.metrics
    logger.info(f"Previous version {previous_version.version} metrics: {metrics}")
    return metrics, int(previous_version.version)

@task(log_prints=True)
def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    df['time'] = pd.to_datetime(df['time'])
    df['hour'] = df['time'].dt.hour
    df['day_of_week'] = df['time'].dt.dayofweek
    df['month'] = df['time'].dt.month

    for lag in range(1, 7):
        df[f'temp_lag_{lag}'] = df['temperature_2m'].shift(lag)

    df['humidity_ewm3'] = df['relative_humidity_2m'].ewm(span=3).mean()
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['week_of_year'] = df['time'].dt.isocalendar().week
    df['week_sin'] = np.sin(2 * np.pi * df['week_of_year'] / 52)
    df['week_cos'] = np.cos(2 * np.pi * df['week_of_year'] / 52)
    df['is_monsoon'] = df['month'].isin([6, 7, 8, 9]).astype(int)
    df = df.drop(columns=['time'])

    X = df.drop(columns=['precipitation'])
    y = df['precipitation']
    return X, y


@task(log_prints=True)
def train_model(X, y):
    logger = get_run_logger()
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("dhaka_city_precipitation_forecast_v9")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    search = GridSearchCV(model, {
        'n_estimators': [200],
        'max_depth': [7, 10],
        'learning_rate': [0.1, 0.01],
        'subsample': [0.8],
        'colsample_bytree': [0.8]
    }, scoring='neg_mean_absolute_error', cv=3)

    with mlflow.start_run() as run:
        search.fit(X_train, y_train)
        best_model = search.best_estimator_
        y_pred = best_model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "mse": mean_squared_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred)
        }

        mlflow.log_metrics(metrics)
        mlflow.log_params(search.best_params_)

        # Create the file before logging
        with open("features.txt", "w") as f:
            f.write("\n".join(X_train.columns))

   
        mlflow.log_artifact("features.txt")
        np.savetxt("y_pred.txt", y_pred)
        mlflow.log_artifact("y_pred.txt")

        signature = infer_signature(X_test, y_pred)
        mlflow.xgboost.log_model(
            best_model,
            artifact_path="model",
            input_example=X_test.iloc[:5],
            signature=signature,
            registered_model_name="dhaka_city_precipitation_xgb"
        )

    logger.info(f"Logged new model metrics: {metrics}")
    return metrics, y_pred


@task(log_prints=True)
def push_metrics_to_prometheus(metrics):
    logger = get_run_logger()
    registry = CollectorRegistry()

    Gauge('model_mae', 'Model MAE', registry=registry).set(metrics['mae'])
    Gauge('model_r2', 'Model R²', registry=registry).set(metrics['r2'])
    Gauge('model_mse', 'Model MSE', registry=registry).set(metrics['mse'])

    push_to_gateway('http://127.0.0.1:9091', job='dhaka_weather_model', registry=registry)
    logger.info("Metrics pushed to Prometheus via Pushgateway.")

@task(log_prints=True)
def compare_and_alias(metrics_new, metrics_old, current_version):
    logger = get_run_logger()

    if not metrics_old or metrics_new['mae'] < metrics_old.get('mae', float('inf')):
        logger.info("New model is better. Assigning alias 'champion'.")
        client = MlflowClient()
        client.set_registered_model_alias("dhaka_city_precipitation_xgb", "champion", current_version)
    else:
        logger.info("Old model performs better. Not updating alias.")
        return "Old model retained (new model not promoted)"

# -------------- FLOW ----------------

@flow(name="train_and_compare")
def train_and_compare():
    logger = get_run_logger()
    flow_start_time = datetime.now()

    blob_name = 'raw/raw_dhaka_weather.csv'
    local_path = '/tmp/latest_weather.csv'

    path = download_from_gcs(blob_name, local_path)
    df = pd.read_csv(path)
    X, y = engineer_features(df)
    
    metrics_new, _ = train_model(X, y)
    ensure_model_registered("dhaka_city_precipitation_xgb") 
    metrics_old, prev_version = fetch_last_model_metrics()

    compare_result = compare_and_alias(metrics_new, metrics_old, current_version=prev_version + 1 if prev_version else 1)
    push_metrics_to_prometheus(metrics_new)
    flow_end_time = datetime.now()

    sendgrid_block = SendgridEmail.load("send-grid-notification-test")

    body = "☁️ Dhaka Precipitation forecast Model Training Completed"
    subject = (
        f"Dhaka City Precipitation forecast model training completed\n\n"
        f"📅 Start Time: {flow_start_time}\n"
        f"⏰ End Time: {flow_end_time}\n\n"
        f"📊 Model Metrics:\n"
        f" - MAE: {metrics_new['mae']:.4f}\n"
        f" - MSE: {metrics_new['mse']:.4f}\n"
        f" - R²:  {metrics_new['r2']:.4f}\n\n"
        f"🌀 Model Selection Result:\n"
        f"{compare_result}\n"
    )

    try:
        sendgrid_block.notify(subject, body)
        logger.info("Notification sent via SendGrid.")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

if __name__ == "__main__":
    train_and_compare()
