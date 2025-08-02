# =========================
# variables.tf
# =========================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-south2"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "asia-south2-a"
}

variable "bucket_name" {
  description = "Name of the GCS bucket"
  type        = string
}

variable "bucket_location" {
  description = "GCS bucket region"
  type        = string
  default     = "ASIA"
}

variable "vm_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "mlops-vm"
}

variable "machine_type" {
  description = "Machine type for the VM"
  type        = string
  default     = "e2-standard-2"
}

variable "boot_image" {
  description = "Boot image for VM"
  type        = string
  default     = "ubuntu-minimal-2404-noble-amd64-v20250701"
}

variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "mlflow-db-instance"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "mlflowdb"
}

variable "prefect_db_name" {
  description = "Name of the Prefect database"
  type        = string
  default     = "prefectdb"
}


variable "db_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "sa_roles" {
  description = "Roles to assign to the service account"
  type        = list(string)
  default = [
    "roles/storage.admin",
    "roles/logging.logWriter",
    "roles/cloudsql.client",
    "roles/compute.admin",
    "roles/ml.admin"
  ]
}
