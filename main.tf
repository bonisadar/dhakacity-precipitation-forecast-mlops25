# =========================
# main.tf
# =========================

provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS Bucket for MLflow Artifacts
resource "google_storage_bucket" "mlflow_bucket" {
  name     = var.bucket_name
  location = var.bucket_location
}

# VM static ip
resource "google_compute_address" "mlops_vm_sta_ip" {
  name   = "mlops-vm-sta-ip"
  region = var.region
}



# PostgreSQL Cloud SQL Instance allowing only the VM
resource "google_sql_database_instance" "mlflow_db_instance" {
  name             = "mlflow-db-instance"
  database_version = "POSTGRES_17"
  region           = "us-central1"

  settings {
    edition = "ENTERPRISE" # required for perf-optimized tiers
    # Custom machine type (2 vCPUs, 7.5GB RAM)
    tier = "db-custom-2-7680"

    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "mlops-vm"
        value = google_compute_address.mlops_vm_sta_ip.address
      }
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    availability_type = "ZONAL"

    disk_type = "PD_SSD"
    disk_size = 100 # in GB
  }

  deletion_protection = false
}


resource "google_sql_user" "mlflow_user" {
  name     = var.db_user
  instance = google_sql_database_instance.mlflow_db_instance.name
  password = var.db_password

  depends_on = [google_sql_database_instance.mlflow_db_instance]
}

resource "google_sql_database" "mlflow_database" {
  name     = var.db_name
  instance = google_sql_database_instance.mlflow_db_instance.name

  depends_on = [google_sql_database_instance.mlflow_db_instance]
}

resource "google_sql_database" "prefect_database" {
  name     = var.prefect_db_name
  instance = google_sql_database_instance.mlflow_db_instance.name

  depends_on = [google_sql_database_instance.mlflow_db_instance]
}

# VM Instance
resource "google_compute_instance" "mlops_vm" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = 40
    }
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip = google_compute_address.mlops_vm_sta_ip.address
    }
  }

  metadata = {
    startup-script = file("startup-script.sh")
  }

  service_account {
    email  = google_service_account.mlops_sa.email
    scopes = ["cloud-platform"]
  }

  tags = ["mlflow", "grafana", "pushgateway", "prometheus", "forecast-app", "postgres", "prefect"]
}



################# Service Account
resource "google_service_account" "mlops_sa" {
  account_id   = "mlops-vm-sa"
  display_name = "MLOps VM Service Account"
}

###################### IAM Binding
resource "google_project_iam_member" "sa_roles" {
  for_each = toset(var.sa_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.mlops_sa.email}"
}

############## Firewall Rules #################

resource "google_compute_firewall" "mlflow_firewall" {
  name    = "allow-mlflow"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["mlflow"]
}

resource "google_compute_firewall" "grafana_firewall" {
  name    = "allow-grafana"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["3000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["grafana"]
}

resource "google_compute_firewall" "allow_pushgateway" {
  name    = "allow-pushgateway"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["9090"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["pushgateway"]
}

resource "google_compute_firewall" "allow_prometheus" {
  name    = "allow-prometheus"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["9091"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["prometheus"]
}

resource "google_compute_firewall" "allow_forecast_app" {
  name    = "allow-forecast-app"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["forecast-app"]
}

resource "google_compute_firewall" "allow_postgres" {
  name    = "allow-postgres"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_ranges = ["0.0.0.0/0"] # Optional: restrict to your IP if possible
  target_tags   = ["postgres"]
}

resource "google_compute_firewall" "allow_prefect" {
  name    = "allow-prefect"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["4200"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["prefect"]
}


