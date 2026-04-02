# ---------------------------------------------------------------------------
# EKS
# ---------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "EKS cluster name — set as EKS_CLUSTER_NAME in GitHub Actions secrets."
  value       = aws_eks_cluster.kira.name
}

output "eks_cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = aws_eks_cluster.kira.endpoint
}

output "eks_cluster_ca" {
  description = "Base64-encoded cluster CA certificate."
  value       = aws_eks_cluster.kira.certificate_authority[0].data
  sensitive   = true
}

output "eks_oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider (used to attach IAM roles to service accounts)."
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "eks_oidc_issuer_url" {
  description = "OIDC issuer URL for the EKS cluster."
  value       = aws_eks_cluster.kira.identity[0].oidc[0].issuer
}

output "eks_node_group_role_arn" {
  description = "IAM role ARN for EKS worker nodes."
  value       = aws_iam_role.eks_node_group.arn
}

# ---------------------------------------------------------------------------
# VPC / Networking
# ---------------------------------------------------------------------------

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.kira.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value       = aws_subnet.private[*].id
}

# ---------------------------------------------------------------------------
# RDS
# ---------------------------------------------------------------------------

output "rds_hostname" {
  description = "RDS instance hostname — used in DATABASE_URL."
  value       = aws_db_instance.kira.address
}

output "rds_port" {
  description = "RDS instance port."
  value       = aws_db_instance.kira.port
}

output "rds_db_name" {
  description = "Database name."
  value       = aws_db_instance.kira.db_name
}

output "rds_username" {
  description = "RDS master username."
  value       = aws_db_instance.kira.username
}

output "rds_database_url_template" {
  description = "DATABASE_URL template — replace <password> with the value from Secrets Manager."
  value       = "postgresql+asyncpg://${aws_db_instance.kira.username}:<password>@${aws_db_instance.kira.address}:${aws_db_instance.kira.port}/${aws_db_instance.kira.db_name}"
}

# ---------------------------------------------------------------------------
# ElastiCache Redis
# ---------------------------------------------------------------------------

output "redis_primary_endpoint" {
  description = "Redis primary endpoint address."
  value       = aws_elasticache_replication_group.kira.primary_endpoint_address
}

output "redis_port" {
  description = "Redis port."
  value       = aws_elasticache_replication_group.kira.port
}

output "redis_url" {
  description = "REDIS_URL for application services (DB 0)."
  value       = "rediss://${aws_elasticache_replication_group.kira.primary_endpoint_address}:6379/0"
}

# ---------------------------------------------------------------------------
# ECR
# ---------------------------------------------------------------------------

output "ecr_registry" {
  description = "ECR registry URL — set as ECR_REGISTRY in GitHub Actions secrets."
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

output "ecr_repository_urls" {
  description = "Map of service name → ECR repository URL."
  value = {
    for name, repo in aws_ecr_repository.services :
    name => repo.repository_url
  }
}

# ---------------------------------------------------------------------------
# S3
# ---------------------------------------------------------------------------

output "s3_assets_bucket" {
  description = "S3 bucket name for static assets."
  value       = aws_s3_bucket.assets.bucket
}

output "s3_backups_bucket" {
  description = "S3 bucket name for database backups."
  value       = aws_s3_bucket.backups.bucket
}

# ---------------------------------------------------------------------------
# Secrets Manager
# ---------------------------------------------------------------------------

output "secrets_manager_db_password_arn" {
  description = "ARN of the Secrets Manager secret holding the RDS password."
  value       = aws_secretsmanager_secret.db_password.arn
}

output "secrets_manager_arns" {
  description = "Map of secret name → ARN for all Kira application secrets."
  value = merge(
    { db_password = aws_secretsmanager_secret.db_password.arn },
    { jwt_secret  = aws_secretsmanager_secret.jwt_secret.arn },
    { for name, s in aws_secretsmanager_secret.services : name => s.arn }
  )
}

# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

output "cicd_user_arn" {
  description = "ARN of the IAM user used by GitHub Actions."
  value       = aws_iam_user.cicd.arn
}

output "cluster_autoscaler_role_arn" {
  description = "IAM role ARN for the Cluster Autoscaler pod (attach via IRSA)."
  value       = aws_iam_role.cluster_autoscaler.arn
}

# ---------------------------------------------------------------------------
# Data sources used across modules
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
