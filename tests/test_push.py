from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Step 1: Create a new metrics registry (isolated)
registry = CollectorRegistry()

# Step 2: Define a dummy gauge metric
test_metric = Gauge(
    "test_push_metric", "This is a test metric from Python", registry=registry
)

# Step 3: Set it to a random float value just for fun
import random

test_metric.set(random.uniform(0.5, 1.5))

# Step 4: Push to Pushgateway (update IP/port if needed)
gateway = "127.0.0.1:9091"  # Replace with your IP if needed (e.g. '172.17.0.1:9091')

try:
    push_to_gateway(gateway, job="test_push_job", registry=registry)
    print(f"Successfully pushed metric to {gateway} under job='test_push_job'")
except Exception as e:
    print(f"Failed to push: {e}")
