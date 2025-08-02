import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://127.0.0.1:5000")
client = MlflowClient()

# 1. Print all experiments (optional overview)
for exp in client.search_experiments():
    print(f"Experiment: {exp.name} | ID: {exp.experiment_id}")

# 2. Fetch the 'champion' version of the registered model
model_name = "model"  # this must match your registered model name exactly

try:
    champion = client.get_model_version_by_alias(name=model_name, alias="champion")
    print(f"\n🏆 Champion model:")
    print(f"Model name: {champion.name}")
    print(f"Version: {champion.version}")
    print(f"Stage: {champion.current_stage}")
    print(f"Run ID: {champion.run_id}")
    print(f"Source path: {champion.source}")
except Exception as e:
    print(f"❌ Failed to find champion model: {e}")
