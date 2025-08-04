
# =========================
# outputs.tf
# =========================

output "vm_ip" {
  value       = google_compute_instance.mlops_vm.network_interface[0].access_config[0].nat_ip
  description = "Public IP of the VM instance"
}

output "db_public_ip" {
  value       = google_sql_database_instance.mlflow_db_instance.public_ip_address
  description = "Public IP of the PostgreSQL DB"
}

output "mlops_vm_sta_ip" {
  value = google_compute_address.mlops_vm_sta_ip.address
}

output "prefect_database_name" {
  value = google_sql_database.prefect_database.name
}


