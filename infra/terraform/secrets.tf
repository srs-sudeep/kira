# ---------------------------------------------------------------------------
# Random password generation
# All passwords are generated here and stored in Secrets Manager.
# Services read them from Secrets Manager at deploy time via:
#   aws secretsmanager get-secret-value --secret-id <name>
# ---------------------------------------------------------------------------

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 2
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false # JWT secrets are base64-encoded; keep alphanumeric
}

resource "random_password" "app_secret_key" {
  length  = 64
  special = false
}

resource "random_password" "encryption_key" {
  # 32 bytes hex = 64 chars; used for Fernet/AES encryption in reservation-service
  length  = 64
  special = false
  upper   = false # hex digits only
  numeric = true
}

# ---------------------------------------------------------------------------
# Shared secrets — used by multiple services
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name_prefix}/db-password"
  description             = "RDS PostgreSQL master password"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${local.name_prefix}/jwt-secret"
  description             = "JWT signing secret shared across all services"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = random_password.jwt_secret.result
}

# ---------------------------------------------------------------------------
# Per-service secrets
# Each service gets a secret bundle containing all its sensitive config.
# The Kubernetes deploy scripts pull these and create K8s Secrets from them.
# ---------------------------------------------------------------------------

locals {
  service_secrets = {
    "identity-service" = {
      description = "identity-service: DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY, SENDGRID_API_KEY"
      value = jsonencode({
        DATABASE_URL     = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY       = random_password.app_secret_key.result
        JWT_SECRET_KEY   = random_password.jwt_secret.result
        SENDGRID_API_KEY = var.sendgrid_api_key
      })
    }

    "rate-inventory-service" = {
      description = "rate-inventory-service: DATABASE_URL, SECRET_KEY"
      value = jsonencode({
        DATABASE_URL = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY   = random_password.app_secret_key.result
      })
    }

    "reservation-service" = {
      description = "reservation-service: DATABASE_URL, SECRET_KEY, ENCRYPTION_KEY"
      value = jsonencode({
        DATABASE_URL    = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY      = random_password.app_secret_key.result
        ENCRYPTION_KEY  = random_password.encryption_key.result
      })
    }

    "channel-engine" = {
      description = "channel-engine: DATABASE_URL, SECRET_KEY, OTA API keys"
      value = jsonencode({
        DATABASE_URL       = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY         = random_password.app_secret_key.result
        BOOKING_COM_API_KEY = var.booking_com_api_key
        EXPEDIA_API_KEY    = var.expedia_api_key
        MMT_API_KEY        = var.mmt_api_key
      })
    }

    "notification-service" = {
      description = "notification-service: DATABASE_URL, SECRET_KEY, SENDGRID_API_KEY"
      value = jsonencode({
        DATABASE_URL     = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY       = random_password.app_secret_key.result
        SENDGRID_API_KEY = var.sendgrid_api_key
      })
    }

    "admin-service" = {
      description = "admin-service: DATABASE_URL, SECRET_KEY"
      value = jsonencode({
        DATABASE_URL = "postgresql+asyncpg://${var.rds_username}:${random_password.db_password.result}@${aws_db_instance.kira.address}:5432/${var.rds_db_name}"
        SECRET_KEY   = random_password.app_secret_key.result
      })
    }
  }
}

resource "aws_secretsmanager_secret" "services" {
  for_each = local.service_secrets

  name                    = "${local.name_prefix}/${each.key}"
  description             = each.value.description
  recovery_window_in_days = 7

  tags = {
    Service = each.key
  }
}

resource "aws_secretsmanager_secret_version" "services" {
  for_each = local.service_secrets

  secret_id     = aws_secretsmanager_secret.services[each.key].id
  secret_string = each.value.value

  lifecycle {
    # Prevent Terraform from overwriting secrets that were rotated manually
    ignore_changes = [secret_string]
  }
}

# ---------------------------------------------------------------------------
# Secrets Manager Resource Policy
# Only EKS node role and CI/CD user can read application secrets.
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret_policy" "services" {
  for_each   = aws_secretsmanager_secret.services
  secret_arn = each.value.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEKSNodes"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.eks_node_group.arn
        }
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = "*"
      },
      {
        Sid    = "AllowCICD"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_user.cicd.arn
        }
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = "*"
      },
    ]
  })
}
