# Main Terraform configuration for Senate Hearing Audio Capture
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }
  
  backend "gcs" {
    bucket = "senate-hearing-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Random password for database
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "storage.googleapis.com",
    "container.googleapis.com",
    "cloudscheduler.googleapis.com",
    "redis.googleapis.com"
  ])
  
  service = each.value
  project = var.project_id
  
  disable_on_destroy = false
}

# Service account for the application
resource "google_service_account" "app_service_account" {
  account_id   = "senate-hearing-processor"
  display_name = "Senate Hearing Processor Service Account"
  description  = "Service account for Senate Hearing Audio Capture application"
}

# Cloud SQL instance
resource "google_sql_database_instance" "main" {
  name             = "senate-hearing-db-${var.environment}"
  database_version = "POSTGRES_13"
  region           = var.region
  
  settings {
    tier                        = var.db_tier
    availability_type           = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_type                   = "PD_SSD"
    disk_size                   = var.db_disk_size
    disk_autoresize            = true
    disk_autoresize_limit      = 100
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 30
      }
    }
    
    maintenance_window {
      hour = 4
      day  = 7
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Cloud SQL database
resource "google_sql_database" "main" {
  name     = "senate_hearing_db"
  instance = google_sql_database_instance.main.name
}

# Cloud SQL user
resource "google_sql_user" "main" {
  name     = "app_user"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

# Cloud Storage bucket for audio files
resource "google_storage_bucket" "audio_files" {
  name          = "${var.project_id}-audio-files-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "production"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
}

# Cloud Storage bucket for backups
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "production"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

# Redis instance for caching
resource "google_redis_instance" "cache" {
  name           = "senate-hearing-cache-${var.environment}"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.region
  
  redis_version = "REDIS_7_0"
  
  depends_on = [google_project_service.required_apis]
}

# Secret Manager secrets
resource "google_secret_manager_secret" "db_password" {
  secret_id = "database-password"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "congress_api_key" {
  secret_id = "congress-api-key"
  
  replication {
    auto {}
  }
}

# IAM bindings for service account
resource "google_project_iam_member" "app_service_account_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/redis.editor"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Cloud Run service
resource "google_cloud_run_service" "main" {
  name     = "senate-hearing-processor"
  location = var.region
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"        = var.max_instances
        "run.googleapis.com/cloudsql-instances"   = google_sql_database_instance.main.connection_name
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }
    
    spec {
      service_account_name = google_service_account.app_service_account.email
      
      containers {
        image = "gcr.io/${var.project_id}/senate-hearing-capture:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "ENV"
          value = var.environment
        }
        
        env {
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.main.name}:${random_password.db_password.result}@/${google_sql_database.main.name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
        }
        
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}"
        }
        
        env {
          name  = "AUDIO_BUCKET"
          value = google_storage_bucket.audio_files.name
        }
        
        env {
          name  = "BACKUP_BUCKET"
          value = google_storage_bucket.backups.name
        }
        
        env {
          name = "CONGRESS_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.congress_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = var.cpu_limit
            memory = var.memory_limit
          }
        }
      }
      
      timeout_seconds = 3600
      container_concurrency = var.concurrency
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.main,
    google_redis_instance.cache
  ]
}

# Cloud Run IAM
resource "google_cloud_run_service_iam_binding" "public_access" {
  count = var.environment == "production" ? 0 : 1
  
  location = google_cloud_run_service.main.location
  service  = google_cloud_run_service.main.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

# Cloud Scheduler job for automated processing
resource "google_cloud_scheduler_job" "automated_processing" {
  name        = "senate-hearing-automated-processing"
  description = "Automated processing of Senate hearings"
  schedule    = "0 */6 * * *"  # Every 6 hours
  time_zone   = "America/New_York"
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.main.status[0].url}/api/process/automated"
    
    headers = {
      "Content-Type" = "application/json"
    }
    
    body = base64encode(jsonencode({
      "type" = "scheduled"
    }))
    
    oidc_token {
      service_account_email = google_service_account.app_service_account.email
      audience              = google_cloud_run_service.main.status[0].url
    }
  }
  
  depends_on = [google_project_service.required_apis]
}

# Monitoring alert policy
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate - Senate Hearing Processor"
  combiner     = "OR"
  
  conditions {
    display_name = "High error rate"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"senate-hearing-processor\" AND metric.type=\"run.googleapis.com/request_count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
}

# Monitoring notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notifications"
  type         = "email"
  
  labels = {
    email_address = var.notification_email
  }
}

# Outputs
output "cloud_run_url" {
  value = google_cloud_run_service.main.status[0].url
}

output "database_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "audio_bucket_name" {
  value = google_storage_bucket.audio_files.name
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "service_account_email" {
  value = google_service_account.app_service_account.email
}