# Terraform variables for Senate Hearing Audio Capture

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
}

variable "notification_email" {
  description = "Email address for monitoring notifications"
  type        = string
}

# Database configuration
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Database disk size in GB"
  type        = number
  default     = 20
}

# Redis configuration
variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# Cloud Run configuration
variable "cpu_limit" {
  description = "CPU limit for Cloud Run service"
  type        = string
  default     = "2000m"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run service"
  type        = string
  default     = "4Gi"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = string
  default     = "10"
}

variable "concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 10
}

# Environment-specific configurations
variable "environments" {
  description = "Environment-specific configurations"
  type = map(object({
    db_tier           = string
    redis_tier        = string
    redis_memory_size = number
    cpu_limit         = string
    memory_limit      = string
    max_instances     = string
    concurrency       = number
  }))
  default = {
    development = {
      db_tier           = "db-f1-micro"
      redis_tier        = "BASIC"
      redis_memory_size = 1
      cpu_limit         = "1000m"
      memory_limit      = "2Gi"
      max_instances     = "2"
      concurrency       = 5
    }
    staging = {
      db_tier           = "db-g1-small"
      redis_tier        = "BASIC"
      redis_memory_size = 2
      cpu_limit         = "1000m"
      memory_limit      = "4Gi"
      max_instances     = "3"
      concurrency       = 10
    }
    production = {
      db_tier           = "db-custom-2-4096"
      redis_tier        = "STANDARD_HA"
      redis_memory_size = 4
      cpu_limit         = "2000m"
      memory_limit      = "4Gi"
      max_instances     = "20"
      concurrency       = 10
    }
  }
}