# Terraform configuration for Senate Hearing Audio Capture
# Environment: Development deployment

project_id = "habuapi"
region     = "us-central1"
environment = "development"
notification_email = "ropak9@gmail.com"

# Development environment configuration
db_tier           = "db-f1-micro"
db_disk_size      = 20
redis_tier        = "BASIC"
redis_memory_size = 1
cpu_limit         = "1000m"
memory_limit      = "2Gi"
max_instances     = "3"
concurrency       = 5