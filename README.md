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
  - $ gcloud projects create dhakacity-forecast-mlops25 --name="DhakaCity Precipitation Forecast" --set-as-default

- Get the id of your billing account.
  - $ gcloud billing accounts list

- Link billing
  - gcloud beta billing projects link dhakacity-forecast-0725 \
       --billing-account=<your-billing-id>

- Enable APIs:
  - gcloud services enable compute.googleapis.com \
       iam.googleapis.com \
       storage.googleapis.com \
       cloudresourcemanager.googleapis.com

- Grant Roles to the Service Account
  - $ gcloud config list account
  - $ gcloud projects add-iam-policy-binding dhakacity-forecast-0725 \
         --member="serviceAccount:<Your-service-account>" \
         --role="roles/owner"

- your donwloaded key file for the service account
  - $ gcloud auth activate-service-account --key-file=.gcp/<Your-key-file.json>

- Verify it's active
  - $ gcloud config list account

- Enabling Cloud Resource Manager API 
  - $ gcloud config set project dhakacity-forecast-0725

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

## 🔁 Workflow Summary

### `fetch_and_upload_flow`

| Task | Description |
|------|-------------|
| ⬇️ Fetch | Pull historical hourly weather data from Open-Meteo |
| 📁 Save | Save CSV locally, then upload to **GCS** |
| ✅ Notify | Send a completion email via **SendGrid** |

### `model_train_flow`

| Task | Description |
|------|-------------|
| 🧠 Train | Train XGBoost model on 20 years of weather data |
| 🔍 Evaluate | Evaluate RMSE, MAE, R² |
| 📦 Log | Store metrics, artifacts, params in **MLflow** |
| ✅ Notify | Send model training summary via **SendGrid** |

### `daily_forecast_drift_check_flow`

| Task | Description |
|------|-------------|
| 📅 Daily Run | Pull latest data and make predictions |
| 📈 Compare | Compare against past model metrics |
| ⚠️ Notify | Send drift alert if deviation exceeds threshold |

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



### 1. Create and Configure GCP Project

When you open grafana for the first time after running the deployments. Add datasource prometheus and select the time last 1 hour by editing the windows in the dashboards.
