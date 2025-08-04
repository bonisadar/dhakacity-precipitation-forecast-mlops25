# VARIABLES (edit these! Some them you will get after performing terraform)
VM_IP=34.131.112.33
PG_IP=34.27.125.126
password1=123zxc
PREFECT_DB_URL=postgresql+asyncpg://postgres:$(password1)@$(PG_IP):5432/prefectdb
MLFLOW_DB_URL=postgresql+psycopg2://postgres:$(password1)@$(PG_IP):5432/mlflowdb
GCS_BUCKET=mlops-zoomcamp-bucket-95
SENDGRID_BLOCK_NAME=your-sendgrid-block-name
SERVICE_KEY=ml-pipeline-orchestration-17.json
PROJECT_DIR=$(HOME)/projects/dhakacity-precipitation-forecast-mlops25/.gcp
CREDENTIALS_PATH=$(HOME)/projects/dhakacity-precipitation-forecast-mlops25/.gcp/$(SERVICE_KEY)


.PHONY: setup_cloud_dev install_gcloud install_terraform verify_gcloud verify_terraform \
        terraform_init terraform_fmt terraform_validate terraform_plan terraform_apply terraform_all \
        help setup_prefect_ui start_prefect_api start_mlflow check_ports set_env_vars \
        deploy_fetch_data run_fetch_data deploy_train run_train deploy_drift run_drift deploy_all run_all export_credentials

# =============================
# 1. Google Cloud Dev Setup
# =============================

setup_cloud_dev: install_gcloud install_terraform verify_gcloud verify_terraform

install_gcloud:
	@echo "Updating system and installing dependencies..."
	sudo apt update && sudo apt install apt-transport-https ca-certificates gnupg curl -y
	@echo "Adding Google Cloud SDK repo and GPG key..."
	echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
	@echo "Installing Google Cloud SDK..."
	sudo apt update && sudo apt install google-cloud-sdk -y

verify_gcloud:
	@echo "Verifying gcloud installation..."
	gcloud version

install_terraform:
	@echo "Adding Terraform repo and GPG key..."
	wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
	echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $$(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
	@echo "Installing Terraform..."
	sudo apt update && sudo apt install terraform -y

verify_terraform:
	@echo "Verifying Terraform installation..."
	terraform -version

# =============================
# 2. Terraform Workflow
# =============================

terraform_all:
	@$(MAKE) terraform_init || { echo "❌ terraform_init failed"; exit 1; }
	@$(MAKE) terraform_fmt || { echo "❌ terraform_fmt failed"; exit 1; }
	@$(MAKE) terraform_validate || { echo "❌ terraform_validate failed"; exit 1; }
	@$(MAKE) terraform_plan || { echo "❌ terraform_plan failed"; exit 1; }
	@$(MAKE) terraform_apply || { echo "❌ terraform_apply failed"; exit 1; }

terraform_init:
	@echo "Please make sure terraform.tfvars has different GCS_BUCKET value and project ID."
	@read -p "🔄 Press Enter after updating terraform.tfvars..." DUMMY_INPUT
	@echo "Running terraform init..."
	terraform init


terraform_fmt:
	@echo "Formatting Terraform files..."
	terraform fmt

terraform_validate:
	@echo "Validating Terraform configuration..."
	terraform validate

terraform_plan:
	@echo "Planning Terraform deployment..."
	terraform plan -out=tfplan

terraform_apply:
	@echo "Applying Terraform plan (will prompt for password if needed)..."
	terraform apply tfplan

# =============================
# 3. Manual installation
# =============================

.PHONY: setup-vm

setup-vm:
	cd projects/dhakacity-precipitation-forecast-mlops25 && \
	chmod +x gcp_startup.sh && \
	./gcp_startup.sh

# =============================
# 4. Moving credentials
# =============================

move-creds:
	@echo "Moving service account key to .gcp folder..."
	@mkdir -p $(PROJECT_DIR)
	@mv -v $(HOME)/$(SERVICE_KEY) $(PROJECT_DIR)/
	@echo "Done moving credentials to $(PROJECT_DIR)."


# ===================================
# 4. Initializing Prometheus, Grafana
# ===================================
docker-init:
	@echo "Making setup_monitoring.sh executable..."
	@chmod +x setup_monitoring.sh
	@echo "Running setup_monitoring.sh..."
	@./setup_monitoring.sh


# =============================
# 5. Prefect and Mlflow 
# =============================

help:
	@echo "Available commands:"
	@echo "  make setup_prefect_ui   - Prepares folders and permissions for Prefect UI"
	@echo "  make start_prefect_api  - Starts Prefect API server in tmux"
	@echo "  make start_mlflow       - Starts MLflow tracking server in tmux"
	@echo "  make set_env_vars       - Export necessary env vars in current shell"
	@echo "  make start-services     - Runs all"

setup_prefect_ui:
	sudo mkdir -p /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build
	sudo chown -R bonisadar:bonisadar /home/bonisadar/miniconda3/envs/mlopsenv/lib/python3.10/site-packages/prefect/server/ui_build

start_prefect_api:
	tmux new-session -d -s prefect_server '\
	export GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_PATH) && \
	export PREFECT_API_DATABASE_CONNECTION_URL=$(PREFECT_DB_URL) && \
	export PREFECT_API_URL=http://$(VM_IP):4200/api && \
	prefect server start --host 0.0.0.0 --port 4200'

start_mlflow:
	tmux new-session -d -s mlflow_server '\
	export GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_PATH) && \
	export MLFLOW_TRACKING_URI=http://$(VM_IP):5000 && \
	mlflow server \
	  --backend-store-uri=$(MLFLOW_DB_URL) \
	  --default-artifact-root=gs://$(GCS_BUCKET)/mlflow-artifacts \
	  --host 0.0.0.0 --port 5000'


set_env_vars:
	export PREFECT_API_DATABASE_CONNECTION_URL=$(PREFECT_DB_URL)
	export PREFECT_API_URL=http://$(VM_IP):4200/api
	export MLFLOW_TRACKING_URI=http://$(VM_IP):5000

mlflow-ui:
	@echo "Open http://$(VM_IP):5000 in your browser to access MLflow UI"

prefect-ui:
	@echo "Open http://$(VM_IP):4200 in your browser to access Prefect UI"

start-services: setup_prefect_ui start_prefect_api start_mlflow check_ports set_env_vars mlflow-ui prefect-ui

# ==============================
# 6. Kill services
# ==============================

stop-services:
	@tmux kill-session -t prefect_server || true
	@tmux kill-session -t mlflow_server || true
	@echo "All services stopped."


# ==============================
# 6. Credentials and Deployments
# ==============================

export_credentials:
	export GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_PATH)

deploy_fetch_data:
	prefect deploy fetch_and_upload_data.py:fetch_and_upload_flow -n open-meteo-data-fetcher -p "first_worker"

run_fetch_data:
	prefect deployment run 'fetch-and-upload-flow/open-meteo-data-fetcher'

deploy_train:
	prefect deploy train_and_compare.py:train_and_compare -n dhaka-precipitation-forecast-test -p "first_worker"

run_train:
	prefect deployment run 'train_and_compare/dhaka-precipitation-forecast-test'

deploy_drift:
	prefect deploy monitor_drift.py:drift_monitoring_flow -n drift-monitoring-deployment-test -p "first_worker"

run_drift:
	prefect deployment run 'drift_monitoring_flow/drift-monitoring-deployment-test'

deploy_all: deploy_fetch_data deploy_train deploy_drift

run_all: run_fetch_data run_train run_drift
