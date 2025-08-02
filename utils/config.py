# utils/config.py
import os

def get_bucket_name(default="mlops-zoomcamp-bucket-51"):
    return os.getenv("GCS_BUCKET_NAME", default)

def get_sendgrid_block(default="sendgrid-notification"):
    return os.getenv("GET_SENDGRID_BLOCK", default)