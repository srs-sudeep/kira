# ---------------------------------------------------------------------------
# Global
# ---------------------------------------------------------------------------

variable "project" {
  description = "Project name used as a prefix for all resource names and tags."
  type        = string
  default     = "kira"
}

variable "environment" {
  description = "Deployment environment (production | staging). Controls Multi-AZ, deletion protection, and resource sizing."
  type        = string
  default     = "production"

  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "environment must be 'production' or 'staging'."
  }
}

variable "region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

# ---------------------------------------------------------------------------
# Terraform state backend (used externally by -backend-config; kept here as
# documentation and for the tfvars.example)
# ---------------------------------------------------------------------------

variable "state_bucket" {
  description = "S3 bucket name for Terraform remote state. Must already exist before running terraform init."
  type        = string
  default     = "kira-terraform-state"
}

variable "state_dynamodb_table" {
  description = "DynamoDB table name used for Terraform state locking."
  type        = string
  default     = "kira-terraform-locks"
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (one per AZ)."
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "AZs to spread subnets across. Must be in the chosen region."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

# ---------------------------------------------------------------------------
# EKS
# ---------------------------------------------------------------------------

variable "eks_cluster_version" {
  description = "Kubernetes version for the EKS cluster."
  type        = string
  default     = "1.29"
}

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS worker nodes."
  type        = string
  default     = "t3.xlarge"
}

variable "eks_node_desired" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 1
}

variable "eks_node_min" {
  description = "Minimum number of worker nodes (Cluster Autoscaler lower bound)."
  type        = number
  default     = 1
}

variable "eks_node_max" {
  description = "Maximum number of worker nodes (Cluster Autoscaler upper bound)."
  type        = number
  default     = 3
}

variable "eks_node_disk_size" {
  description = "Root EBS volume size (GiB) for worker nodes."
  type        = number
  default     = 50
}

variable "eks_public_access_cidrs" {
  description = "CIDR blocks allowed to reach the EKS API server endpoint. Restrict to your office/VPN CIDRs in production."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ---------------------------------------------------------------------------
# RDS
# ---------------------------------------------------------------------------

variable "rds_engine_version" {
  description = "PostgreSQL major version."
  type        = string
  default     = "16"
}

variable "rds_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Initial allocated storage in GiB."
  type        = number
  default     = 50
}

variable "rds_max_allocated_storage" {
  description = "Maximum storage autoscaling threshold in GiB."
  type        = number
  default     = 200
}

variable "rds_backup_retention_days" {
  description = "Number of days to retain automated RDS backups."
  type        = number
  default     = 7
}

variable "rds_backup_window" {
  description = "Daily time range (UTC) for automated backups."
  type        = string
  default     = "02:00-03:00"
}

variable "rds_maintenance_window" {
  description = "Weekly time range for maintenance (day:HH:MM-day:HH:MM UTC)."
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "rds_db_name" {
  description = "Name of the initial database."
  type        = string
  default     = "kira"
}

variable "rds_username" {
  description = "Master username for RDS."
  type        = string
  default     = "kira_admin"
}

# ---------------------------------------------------------------------------
# ElastiCache Redis
# ---------------------------------------------------------------------------

variable "redis_engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "redis_node_type" {
  description = "ElastiCache node instance type."
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes. Set to 2+ for replication."
  type        = number
  default     = 1
}

variable "redis_snapshot_retention" {
  description = "Number of days to retain Redis snapshots."
  type        = number
  default     = 3
}

# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------

variable "s3_assets_bucket_name" {
  description = "Name for the static assets S3 bucket. Must be globally unique."
  type        = string
  default     = "kira-assets"
}

variable "s3_backups_bucket_name" {
  description = "Name for the backups S3 bucket. Must be globally unique."
  type        = string
  default     = "kira-backups"
}

# ---------------------------------------------------------------------------
# Secrets (initial values — rotate after first apply)
# ---------------------------------------------------------------------------

variable "sendgrid_api_key" {
  description = "SendGrid API key for transactional email (notification-service)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "booking_com_api_key" {
  description = "Booking.com Connectivity API key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "expedia_api_key" {
  description = "Expedia EQC API key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "mmt_api_key" {
  description = "MakeMyTrip API key."
  type        = string
  sensitive   = true
  default     = ""
}

# ---------------------------------------------------------------------------
# DNS / ACM
# ---------------------------------------------------------------------------

variable "domain_name" {
  description = "Root domain for the KIRA platform (e.g. kira.abodeab.com)."
  type        = string
  default     = "kira.abodeab.com"
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for var.domain_name. Leave empty to skip DNS record creation."
  type        = string
  default     = ""
}
