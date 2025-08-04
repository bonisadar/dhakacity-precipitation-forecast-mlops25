# 🌧️ Dhaka City 24-Hour Precipitation Forecast - MLOps Zoomcamp

## Problem Statement

This project aims to forecast **24-hour precipitation in Dhaka city** using a regression model trained on **20 years of historical weather data** sourced from the [Open-Meteo API](https://open-meteo.com/). 

---

## Project Overview

Rainfall in Bangladesh can cause severe urban disruption. The goal is to:
- Forecast rainfall for the next 24 hours in **Dhaka**.
- Retrain the model monthly on freshly fetched weather data.
- Detect drift daily to monitor model health.
- Send **email notifications** (via SendGrid) for model status and alerts.
- Momitor model metrics in Grafana.
- Model deployed using GCP Cloud Run/Services

---

## Tech Stack
#### OS: Ubuntu 24.04.2 LTS x86_64 (Local Machine)
#### The VM in GCP 

**Boot disk source image: ubuntu-minimal-2404-noble-amd64-v20250701**

**Boot disk architecture: X86_64**

**Machine type: e2-standard-2 (2 vCPUs, 8 GB Memory)**

| Layer                     | Tool / Framework                |
|---------------------------|---------------------------------|
| Cloud Infrastructure      | **Google Cloud Platform (GCP)** |
| Orchestration             | **Prefect 2.x**                 |
| Experiment Tracking       | **MLflow**                      |
| Data Fetching             | **Open-Meteo API**              |
| Model                     | **XGBoost Regression**          |
| Infra-as-Code             | **Terraform**                   |
| Monitoring & Notification | **Grafana, SendGrid**           |
| Scheduling                | **Prefect Scheduled Flows**     |
| Cloud Deployment          | **GCP Cloud Run/services**      |

---
## Setup Instructions
> Assumes `gcloud`, `terraform` already installed in local environment. If not:

- $ make setup_cloud_dev 

## Manually create (From your local machine)
- A GCP service account with billing enabled.
- A Project ID linked to the billing.
- Granting necessary permissions

If need help. Click here [here](assets/gcp-setup-instructions.md). Follow them step-by-step before running the pipeline!

## Infrastructure Setup (via Terraform)

#### Provisioned resources in GCP:
- A **GCS bucket** for data and MLflow artifacts.
- A **Cloud SQL PostgreSQL (v17)** instance with:
  - `mlflowdb` for tracking runs/artifacts.
  - `prefectdb` for Prefect orchestration.
- A **Compute Engine VM** with static IP to host:
  - Prefect server
  - MLflow UI
  - Training workflows
- **Firewall policies** for all network ports (Perfect, Mlflow etc.).

---
#### From your local machine
- $ git clone https://github.com/bonisadar/dhakacity-precipitation-forecast-mlops25

- $ export GOOGLE_APPLICATION_CREDENTIALS="/mnt/your/path/to the service-account-key-file/.gcp/name-of-keyfile.json"

### DO NOT forget to change the bucket-name and preject ID inside the terraform.tfvars

* $ make terraform_all

   - **Remember the password1 entered during prompt**

**If all goes accordingly you should see the outputs, copy the two IP addresses**
**db_public_ip is the postgresql instance ip, other on is VM static IP**
**You need to update the Makefile variables accordingly**

### Accessing your VM in GCP
* You can access your GCP VM either through the Google Cloud Console using the browser-based SSH (easier) or
 - $ gcloud compute instances start mlops-vm --zone=asia-south2-a
 - $ gcloud compute ssh mlops-vm --zone=asia-south2-a

#### During first loging into VM
 - $ source ~/miniconda3/etc/profile.d/conda.sh
 - $ conda activate mlopsenv
* Make sure necessary libraries are installed correctly.
  - $ pip freeze | grep -E 'numpy|pandas|scikit-learn|xgboost|fastapi|uvicorn|google-cloud-storage|psycopg|pyarrow|fastparquet|mlflow|prefect|requests'

**If no miniconda3 dir found only projects is there then run:**
 - $ make setup-vm

## 🔁 Workflow Summary

- Open a terminal from your local machine where you stored the your-service-key.json file and use the command: 

  - $ gcloud compute scp your-service-key.json bonisadar@mlops-vm:/home/bonisadar/ --zone=asia-south2-a

- to upload the key file to the VM (Or just upload the file via upload button if you are using browser-based SSH to access the VM)

  - $ make move-creds  (Don't forget to update your Makefile variables as necessary)
 

### From inside your VM
- Move to project directory $ cd projects/dhakacity-precipitation-forecast-mlops25
- $ export GOOGLE_APPLICATION_CREDENTIALS="/home/bonisadar/projects/dhakacity-precipitation-forecast-mlops25/.gcp/your-service-key.json"

### Initializing pushgateway, prometheus and Grafana
#### Add Your User to the docker Group
- sudo usermod -aG docker $USER

  **Then log out and log back in (Just type $ exit and log in again).**
- $ make docker-init

## Starting Prefect
**After activating the virtual env inside your VM**
 - $ tmux

* Set the database connection URL
  - $ export PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password1@your-postgresql-ip:5432/prefectdb
* Set the Prefect API URL 
  - export PREFECT_API_URL="http://your-vm-static-ip:4200/api"
  
#### Manually create the folders once, give yourself write access.
  - $ sudo mkdir -p /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build

  - $ sudo chown -R bonisadar:bonisadar /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build

  - $ prefect server start --host 0.0.0.0 --port 4200

  - **$ Ctrl+B, C (Opens a new terminal, assuming you are using tmux)**

  - $ export PREFECT_API_URL=http://your-vm-static-ip:4200/api (Then you can access http://your-vm-static-ip:4200 from your local computer)

----------
  **If Prefect UI isn't accessible from your laptop**

  Inside your VM run

  * $ ps aux | grep prefect (Check prefect is actually running)
  * $ sudo netstat -tuln | grep 4200 (Double check)

    Expected output:

    tcp        0      0 0.0.0.0:4200      0.0.0.0:*       LISTEN

    Then again run 

    $  export PREFECT_API_URL=http://your-vm-static-ip:4200/api 

    The problem should solve now.
----------

**You need to log into SendGrid and get a access key and also verify a sender email and register a receiver email for the email notification to work (The code will just run fine without it). Open prefect UI create a SendGrid notification block using the key from sendgrid. Also, create a worker type process name first_worker.**

### DO NOT forget to change the  bucket-name and sendgrid-block-name in config.py inside utils.

# Starting mlflow server
 - mlflow server \
  --backend-store-uri postgresql+psycopg2://postgres:password1@your-postgresql-ip:5432/mlflowdb \
  --default-artifact-root gs://your-GCP-bucket/mlflow-artifacts \
  --host 0.0.0.0 \
  --port 5000

 - Ctrl+B , C
 - $ export MLFLOW_TRACKING_URI=http://your-vm-static-ip:5000 

 ---------------------------------------------------------------------------------
 **Useful tmux syntax**

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

 ---------------------------------------------------------------------------------

### `fetch_and_upload_flow`

| Task | Description |
|------|-------------|
| Fetch | Pull historical hourly weather data from Open-Meteo |
| Save | Save CSV locally, then upload to **GCS** |
| Notify | Send a completion email via **SendGrid** |

* $ prefect deploy fetch_and_upload_data.py:fetch_and_upload_flow -n open-meteo-data-fetcher -p "first_worker"
* $ export GOOGLE_APPLICATION_CREDENTIALS="/home/bonisadar/dhakacity-precipitation-forecast-mlops25/.gcp/ml-pipeline-orchestration-17.json"
* $ prefect deployment run 'fetch-and-upload-flow/open-meteo-data-fetcher'

* Check you spam folder for the email notification.

### `model_train_flow`

| Task | Description |
|------|-------------|
| Train | Train XGBoost model on 20 years of weather data |
| Evaluate | Evaluate RMSE, MAE, R² |
| Log | Store metrics, artifacts, params in **MLflow** |
| Monitoring | Pushes model metrics to **Prometheus** |
| Promoting | If new model metrics are better then promotes |
| Notify | Send model training summary via **SendGrid** |

* $ prefect deploy train_and_compare.py:train_and_compare -n dhaka-precipitation-forecast-test -p "first_worker"
* $ prefect deployment run 'train_and_compare/dhaka-precipitation-forecast-test'

http://34.131.121.93:9091 access prometheus from local machine

http://34.131.121.93:3000 access grafana from local machine

## Model Training flow

![Model train flow](assets/train.png)


When you open grafana for the first time after running the deployments. Go to the dashboard named ML Model metrics, select the time last 1 hour by editing the windows in the dashboards.

### `drift_monitoring_flow`

| Task | Description |
|------|-------------|
| Daily Run | Fetches weather data from 3 days ago and make predictions |
| Compare | Compare against past model metrics |
| Notify | Send drift alert if deviation exceeds threshold |

* $ prefect deploy monitor_drift.py:drift_monitoring_flow -n drift-monitoring-deployment-test -p "first_worker"
* $ prefect deployment run 'drift_monitoring_flow/drift-monitoring-deployment-test'

## Drift monitor flow

![Monitor drift flow](assets/monitor.png)

## Mlflow UI

![Mlfolw UI](assets/mlflow.png)

## Pushgateway Model Metrics

![Model metrics](assets/pushgateway.png)



When exiting

$ tmux kill-server

$ docker compose stop/start

---

## Notification

- **SendGrid Email Block** integrated with Prefect
- Emails triggered:
  - After successful data fetch
  - After model training
  - On drift detection

---

## Scheduling

| Flow                     | Schedule           |
|--------------------------|--------------------|
| `fetch_and_upload_data`  | **1st of every month at 4 PM PM UTC** |
| `train-and-compare` | **2nd of every month at 4 PM UTC** |
| `drift-monitoring-flow` | **Every day at 11 AM UTC** |
---

## Deployment

**The model is deployed using GCP Cloud Run/Services**

## Step 1 select GitHub

![Select gitHub](assets/deploy1.png)

## Step 2 setup cloud build
#### Manage connect repo - add the repo you want to deploy from

![Setup cloud build](assets/deploy2.png)

## Step 3 
#### Don't forget to select the correct branch name (master in this case)

![brach name](assets/deploy4.png)

## Running Build

![running build](assets/deploy8.png)

#### After successful bulid - Go to Cloud Run Console - Click your service: dhakacity-precipitation-forecast-mlops25 - Right at the top - you'll see the API endpoint.

## Welcome screen

![welcome screen](assets/welcome.png)

## Just add '/predict' at the end of the URL
![Predictions](assets/predictions.png)

#### Do not maually delete the resources created by the terraform
- $ export GOOGLE_APPLICATION_CREDENTIALS="/home/bonisadar/dhakacity-precipitation-forecast-mlops25/.gcp/ml-pipeline-orchestration-17.json"
- $ terraform destroy
- $ terraform state list   # <- lists all tracked resources 

    (If something remains)

- $ terraform state rm google_sql_database.mlflow_database
- $ terraform state rm google_sql_user.mlflow_user
- $ terraform state rm google_sql_database_instance.mlflow_db_instance
- $ terraform state rm google_storage_bucket.mlflow_bucket
- $ terraform state rm google_compute_address.mlops_vm_static_ip
