# utils/config.py
import os

def get_bucket_name(default="mlops-zoomcamp-bucket-42"):
    return os.getenv("GCS_BUCKET_NAME", default)
