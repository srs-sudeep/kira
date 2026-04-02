# ---------------------------------------------------------------------------
# DB Subnet Group (private subnets only)
# ---------------------------------------------------------------------------

resource "aws_db_subnet_group" "kira" {
  name        = "${local.name_prefix}-db-subnet-group"
  subnet_ids  = aws_subnet.private[*].id
  description = "Private subnet group for KIRA RDS"

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

# ---------------------------------------------------------------------------
# RDS Parameter Group
# Tuned for KIRA's async connection-per-pod pattern.
# ---------------------------------------------------------------------------

resource "aws_db_parameter_group" "kira" {
  name        = "${local.name_prefix}-pg16"
  family      = "postgres${var.rds_engine_version}"
  description = "KIRA PostgreSQL ${var.rds_engine_version} parameter group"

  # Allow more concurrent connections (default 100 for db.t3.medium)
  parameter {
    name  = "max_connections"
    value = "500"
  }

  # Log slow queries (anything over 1 second)
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  # Log all connections and disconnections in production
  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  # Enable query ID tracking (required for pg_stat_statements)
  parameter {
    name         = "compute_query_id"
    value        = "on"
    apply_method = "pending-reboot"
  }

  # pg_stat_statements for query performance analysis
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  # Timezone
  parameter {
    name  = "timezone"
    value = "UTC"
  }

  tags = {
    Name = "${local.name_prefix}-pg16-params"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ---------------------------------------------------------------------------
# KMS key for RDS encryption at rest
# ---------------------------------------------------------------------------

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption — ${local.name_prefix}"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# ---------------------------------------------------------------------------
# RDS Instance
# ---------------------------------------------------------------------------

resource "aws_db_instance" "kira" {
  identifier = local.name_prefix

  # Engine
  engine               = "postgres"
  engine_version       = "${var.rds_engine_version}.3"
  instance_class       = var.rds_instance_class
  parameter_group_name = aws_db_parameter_group.kira.name

  # Storage
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  # Database
  db_name  = var.rds_db_name
  username = var.rds_username
  password = random_password.db_password.result
  port     = 5432

  # High Availability
  multi_az = var.environment == "production"

  # Networking
  db_subnet_group_name   = aws_db_subnet_group.kira.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Backups
  backup_retention_period   = var.rds_backup_retention_days
  backup_window             = var.rds_backup_window
  maintenance_window        = var.rds_maintenance_window
  copy_tags_to_snapshot     = true
  delete_automated_backups  = false

  # Protection
  deletion_protection = var.environment == "production"
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${local.name_prefix}-final-snapshot" : null

  # Performance Insights (helps identify slow queries)
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Enhanced monitoring (1-second granularity)
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn

  # Auto minor version upgrades (patch releases only, never major)
  auto_minor_version_upgrade = true
  apply_immediately          = false

  tags = {
    Name = "${local.name_prefix}-postgres"
  }

  lifecycle {
    # Prevent Terraform from rotating the password on every plan
    ignore_changes = [password]
  }
}

# ---------------------------------------------------------------------------
# RDS Enhanced Monitoring IAM Role
# ---------------------------------------------------------------------------

resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${local.name_prefix}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ---------------------------------------------------------------------------
# RDS CloudWatch Alarms
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.name_prefix}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilisation > 80% for 10 minutes"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.kira.identifier
  }

  tags = {
    Name = "${local.name_prefix}-rds-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${local.name_prefix}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120 # 5 GiB in bytes
  alarm_description   = "RDS free storage < 5 GiB"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.kira.identifier
  }

  tags = {
    Name = "${local.name_prefix}-rds-storage-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${local.name_prefix}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 400
  alarm_description   = "RDS connection count > 400 (approaching max_connections=500)"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.kira.identifier
  }

  tags = {
    Name = "${local.name_prefix}-rds-connections-alarm"
  }
}
