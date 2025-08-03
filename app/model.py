# app/model.py
import mlflow
from mlflow.tracking import MlflowClient

# Set your tracking URI — adjust for deployment
mlflow.set_tracking_uri("http://34.131.121.93:5000")  # Replace with your actual VM IP

def get_champion_metrics(model_name="dhaka_city_precipitation_xgb"):
    """
    Fetch metrics of the model version currently aliased as 'champion'.
    """
    client = MlflowClient()

    # Get model version tagged with alias 'champion'
    version = client.get_model_version_by_alias(model_name, "champion")
    run = client.get_run(version.run_id)
    return run.data.metrics

def load_model(model_name="dhaka_city_precipitation_xgb"):
    """
    Load the model version currently aliased as 'champion'.
    """
    client = MlflowClient()

    # Get model version tagged with alias 'champion'
    version = client.get_model_version_by_alias(model_name, "champion")
    model_uri = f"runs:/{version.run_id}/model"
    
    return mlflow.pyfunc.load_model(model_uri)
