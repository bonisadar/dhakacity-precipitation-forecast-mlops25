# app/model.py
import mlflow
from mlflow.tracking import MlflowClient

# Make sure this points to your actual MLflow tracking server
mlflow.set_tracking_uri("http://34.131.48.251:5000")  # Change to VM IP in deployment

def get_champion_metrics(model_name="dhaka_city_precipitation_xgb"):
    client = MlflowClient()
    
    # Get the latest version of the registered model
    versions = client.get_latest_versions(model_name, stages=["None", "Staging", "Production"])
    
    # Just grab the highest version (assuming you want latest regardless of stage)
    latest_version = sorted(versions, key=lambda v: int(v.version))[-1]
    
    run = client.get_run(latest_version.run_id)
    return run.data.metrics

def load_model(model_name="dhaka_city_precipitation_xgb"):
    client = MlflowClient()
    
    # Get the latest version (no alias)
    versions = client.get_latest_versions(model_name, stages=["None", "Staging", "Production"])
    
    # Again, get the highest version
    latest_version = sorted(versions, key=lambda v: int(v.version))[-1]
    
    model_uri = f"runs:/{latest_version.run_id}/model"
    return mlflow.pyfunc.load_model(model_uri)

    return model

