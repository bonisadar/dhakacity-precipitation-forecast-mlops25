import os
from datetime import datetime, timedelta
from prefect import flow, task, get_run_logger
from utils.config import get_bucket_name
from data_fetcher import fetch_weather_data, get_dynamic_date_range
from google.cloud import storage
from prefect.blocks.notifications import SendgridEmail

@task
def save_to_local(df, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)
    return file_path

@task
def upload_to_gcs(file_path, destination_blob_name, bucket_name):
    logger = get_run_logger()
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    logger.info(f"Uploaded {file_path} to gs://{bucket_name}/{destination_blob_name}")


@flow
def fetch_and_upload_flow():
    logger = get_run_logger()
    flow_start_time = datetime.now()

    # Dynamically get the bucket name from env or fallback
    bucket_name = get_bucket_name()

    # Weather parameters
    hourly_vars = [
        'temperature_2m', 'relative_humidity_2m', 'dewpoint_2m',
        'apparent_temperature', 'cloudcover', 'cloudcover_low',
        'windspeed_10m', 'winddirection_10m', 'surface_pressure',
        'vapour_pressure_deficit', 'weathercode', 'wet_bulb_temperature_2m',
        'precipitation', 'is_day'
    ]

    # Dynamic date range (last 20 years)
    start_date, end_date = get_dynamic_date_range(days_back=7300, buffer_days=2)

    # Fetch data
    df = fetch_weather_data(23.8041, 90.4152, hourly_vars, start_date, end_date)

    # Local save
    local_file = f"../data/raw_dhaka_weather_{start_date}_to_{end_date}.csv"
    save_to_local(df, local_file)

    # Upload to GCS
    upload_to_gcs(local_file, f'raw/raw_dhaka_weather.csv', bucket_name)

    flow_end_time = datetime.now()

    # Count missing values
    missing_count = df.isnull().sum().sum()
    has_missing = missing_count > 0

    sendgrid_block = SendgridEmail.load("send-grid-notification-test")


    subject = "☁️ Training data collection via Open-meteo API"
    message = (
        "✅ Weather data flow completed!\n\n"
        f"📅 Start Time: {flow_start_time}\n"
        f"⏰ End Time: {flow_end_time}\n"
        f"📊 Date Range: {start_date} to {end_date}\n"
        f"📁 File saved as: {local_file}\n"
        f"☁️ Uploaded to: gs://{bucket_name}/raw/raw_dhaka_weather.csv\n\n"
        f"🔍 Missing values found: {missing_count}\n"
        f"{'⚠️ Check data quality!' if has_missing else '🎉 No missing data detected!'}"
    )

    try:
        sendgrid_block.notify(subject, message)
        logger.info("Notification sent via SendGrid.")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


if __name__ == "__main__":
    fetch_and_upload_flow()

