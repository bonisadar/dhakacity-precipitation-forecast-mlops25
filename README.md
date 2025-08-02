# 🌧️ Dhaka City 24-Hour Precipitation Forecast - MLOps Pipeline

## 🚀 Project Overview

This project aims to forecast **24-hour precipitation in Dhaka city** using a regression model trained on **20 years of historical weather data** sourced from the [Open-Meteo API](https://open-meteo.com/). 

---

## 📊 Problem Statement

Rainfall in Bangladesh can cause severe urban disruption. The goal is to:
- Forecast rainfall for the next 24 hours in **Dhaka**.
- Retrain the model monthly on freshly fetched weather data.
- Detect drift daily to monitor model health.
- Send **email notifications** (via SendGrid) for model status and alerts.

---

## 🔧 Tech Stack

| Layer                     | Tool / Framework                |
|---------------------------|---------------------------------|
| Cloud Infrastructure      | **Google Cloud Platform (GCP)** |
| Orchestration             | **Prefect 2.x**                 |
| Experiment Tracking       | **MLflow**                      |
| Data Fetching             | **Open-Meteo API**              |
| Model                     | **XGBoost Regression**          |
| Infra-as-Code             | **Terraform**                   |
| Monitoring & Notification | **SendGrid**, Drift metrics     |
| Scheduling                | **Prefect Scheduled Flows**     |

---
## Setup Instructions
> Assumes `gcloud`, `terraform` already installed. If not:

1. Install Google Cloud SDK (gcloud CLI)
Google Cloud SDK includes gcloud, gsutil, and bq.
# Update and install dependencies
sudo apt update && sudo apt install apt-transport-https ca-certificates gnupg curl -y

# Add the Google Cloud SDK repo and GPG key
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

# Update again and install
sudo apt update && sudo apt install google-cloud-sdk -y

# Verify
gcloud version

2. Install Terraform
follow instructions: https://developer.hashicorp.com/terraform/install
or,
For Linus Ubuntu/Debian
$ wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

$ echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

$ sudo apt update && sudo apt install terraform

2. Verify Installation

$ terraform -version

Terraform v1.12.2
on linux_amd64


## Manually create
- A GCP service account with billing enabled if trial expired.

- Authenticating with the gcolud CLI
  - $ gcloud auth login

- Create a project. 
  - $ gcloud projects create dhakacity-forecast-mlops25 --name="Precipitation Forecast" --set-as-default

- Get the id of your billing account.
  - $ gcloud billing accounts list

- Link billing
  - gcloud beta billing projects link dhakacity-forecast-mlops25 \
       --billing-account=your-billing-id

- Enable APIs:
  - gcloud services enable compute.googleapis.com \
       iam.googleapis.com \
       storage.googleapis.com \
       cloudresourcemanager.googleapis.com

- Grant Roles to the Service Account
  - $ gcloud config list account
  - $ gcloud projects add-iam-policy-binding dhakacity-forecast-mlops25 \
         --member="serviceAccount:Your-service-account" \
         --role="roles/owner"

- your donwloaded key file for the service account
  - $ gcloud auth activate-service-account --key-file=.gcp/Your-key-file.json

- Verify it's active
  - $ gcloud config list account

- Enabling Cloud Resource Manager API 
  - $ gcloud config set project dhakacity-forecast-mlops25

Open the API activation link in your browser: Click enable wait for a few minutes

- Quick sanity check:
  - $ gcloud projects list

## Infrastructure Setup (via Terraform)

Provisioned resources in GCP:
- A **GCS bucket** for data and MLflow artifacts.
- A **Cloud SQL PostgreSQL (v17)** instance with:
  - `mlflowdb` for tracking runs/artifacts.
  - `prefectdb` for Prefect orchestration.
- A **Compute Engine VM** to host:
  - Prefect server
  - MLflow UI
  - Training workflows
- A **Service Account** with IAM roles and generated credentials.

---
$ export GOOGLE_APPLICATION_CREDENTIALS="/mnt/your/path/to the service-account-key-file.json/.gcp/ml-pipeline-orchestration-17.json"

$ terraform init
$ terraform fmt 
$ terraform validate 
$ terraform plan -out=tfplan
 - Remember the password1 entered during prompt
$ terraform apply "tfplan"

* db_public_ip is the postgresql instance ip
* You can either access you VM in GCP via GCP UI (easier) or
 - $ gcloud compute instances start mlops-vm --zone=asia-south2-a
 - $ gcloud compute ssh mlops-vm --zone=asia-south2-a

* During first loging into VM
 - source ~/miniconda3/etc/profile.d/conda.sh
 - conda activate mlopsenv
* Make sure necessary libraries are installed correctly.
 - pip freeze | grep -E 'numpy|pandas|scikit-learn|xgboost|fastapi|uvicorn|google-cloud-storage|psycopg|pyarrow|fastparquet|mlflow|prefect|requests'

## 🔁 Workflow Summary

- Open a terminal from your local machine where you stored the key.json file and use this to upload the key file to the VM
  gcloud compute scp \
    your-service-key.json \
    mlops-vm:~/projects/dhakacity-precipitation-forecast-mlops/.gcp \
    --zone=asia-south2-a
* From inside your VM
- Move to project directory cd projects/dhakacity-precipitation-forecast-mlops25
- $ export GOOGLE_APPLICATION_CREDENTIALS="/home/bonisadar/projects/dhakacity-precipitation-forecast-mlops25/.gcp/ml-pipeline-orchestration-17.json"

# Initializing pushgateway, prometheus and grafana
* Add Your User to the docker Group
- sudo usermod -aG docker $USER
  Then log out and log back in
- Initialize docker by following setup_monitoring.sh instructions

# Starting Prefect
** After activating the virtual env 
 - $ tmux

* Set the database connection URL
  - $ export PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password1@your-postgresql-ip:5432/prefectdb
* Set the Prefect API URL 
  - export PREFECT_API_URL="http://your-vm-static-ip/api"
* Manually create the folders once, give yourself write access.
  - $ sudo mkdir -p /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build
  - $ sudo chown -R bonisadar:bonisadar /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build
  - $ prefect server start --host 0.0.0.0 --port 4200
  - $ Ctrl+B, C (Opens a new terminal)
  - $ export PREFECT_API_URL=http://your-vm-static-ip:4200/api (Then you can access http://34.131.121.93:4200 from your local computer)

* You need to log into SendGrid and get a access key and also verify a sender email and register a receiver email for the email notification to work (The code will just run fine without it). Open prefect UI create a SendGrid notification block using the key from sendgrid. Also, create a worker type process name first_worker.

DO NOT forget to change the  bucket-name and sendgrid-block-name in config.py inside utils.

# Starting mlflow server
 - mlflow server \
  --backend-store-uri postgresql+psycopg2://postgres:password1@your-postgresql-ip:5432/mlflowdb \
  --default-artifact-root gs://mlops-zoomcamp-bucket-51/mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000

 - Ctrl+B , C
 - $ export MLFLOW_TRACKING_URI=http://34.131.121.93:5000 

 ----------------------------------------------------------------------------------------------
  Ctrl + B, W → shows all windows in the current session (select with arrow keys and Enter).
    Ctrl + B, N → go to Next window.
    Ctrl + B, P → go to Previous window.

  To detach
    Ctrl + B, D

  To list all tmux sessions:
   tmux ls
  
  Attach to session 0:
    tmux attach -t 0

  Kill All Sessions
   tmux kill-server
 ----------------------------------------------------------------------------------------------

### `fetch_and_upload_flow`

| Task | Description |
|------|-------------|
| ⬇️ Fetch | Pull historical hourly weather data from Open-Meteo |
| 📁 Save | Save CSV locally, then upload to **GCS** |
| ✅ Notify | Send a completion email via **SendGrid** |

$ prefect deploy fetch_and_upload_data.py:fetch_and_upload_flow -n open-meteo-data-fetcher -p "first_worker"
$ export GOOGLE_APPLICATION_CREDENTIALS="/home/bonisadar/dhakacity-precipitation-forecast-mlops25/.gcp/ml-pipeline-orchestration-17.json"
$ prefect deployment run 'fetch-and-upload-flow/open-meteo-data-fetcher'

* Check you spam folder for the email notification.

### `model_train_flow`

| Task | Description |
|------|-------------|
| 🧠 Train | Train XGBoost model on 20 years of weather data |
| 🔍 Evaluate | Evaluate RMSE, MAE, R² |
| 📦 Log | Store metrics, artifacts, params in **MLflow** |
| ✅ Notify | Send model training summary via **SendGrid** |

$ prefect deploy train_and_compare.py:train_and_compare -n dhaka-precipitation-forecast-test -p "first_worker"
$ prefect deployment run 'train_and_compare/dhaka-precipitation-forecast-test'

When you open grafana for the first time after running the deployments. Add datasource prometheus and select the time last 1 hour by editing the windows in the dashboards.

### `daily_forecast_drift_check_flow`

| Task | Description |
|------|-------------|
| 📅 Daily Run | Pull latest data and make predictions |
| 📈 Compare | Compare against past model metrics |
| ⚠️ Notify | Send drift alert if deviation exceeds threshold |

$ prefect deploy monitor_drift.py:drift_monitoring_flow -n drift-monitoring-deployment-test -p "first_worker"
$ prefect deployment run 'drift_monitoring_flow/drift-monitoring-deployment-test'

When exiting
tmux kill-server
docker compose stop/start
---

## 📬 Notification

- **SendGrid Email Block** integrated with Prefect
- Emails triggered:
  - After successful data fetch
  - After model training
  - On drift detection

---

## 📅 Scheduling

| Flow                     | Schedule           |
|--------------------------|--------------------|
| `fetch_and_upload_flow`  | **1st of every month at 10 PM** |
| `daily_forecast_drift_check_flow` | **Every day at 10 AM** |

---

When you open grafana for the first time after running the deployments. Add datasource prometheus and select the time last 1 hour by editing the windows in the dashboards.
