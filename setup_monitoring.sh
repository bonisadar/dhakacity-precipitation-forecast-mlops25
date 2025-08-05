#!/bin/bash
set -e
# Safe startup script for Prometheus + Pushgateway + Grafana
# It will start docker compose, without removing volumes or images.

# How to Use
# Save the file as setup_monitoring.sh in the directory with your docker-compose.yml.
# Make it executable:
# $ chmod +x setup_monitoring.sh
# Run it:
# $ ./setup_monitoring.sh
echo "=== Starting Monitoring Stack (Prometheus + Pushgateway + Grafana) ==="

# Check if docker-compose.yml exists
if [ ! -f docker-compose.yml ]; then
  echo "ERROR: docker-compose.yml not found in this directory."
  exit 1
fi

# Pull latest images (optional, comment if not needed every time)
echo "Pulling latest images..."
docker compose pull

# Start the services in detached mode
echo "Starting containers..."
docker compose up -d

echo "=== Monitoring stack started successfully ==="
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
