# ---------------------------------------------------------------------------
# ElastiCache Subnet Group (private subnets only)
# ---------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "kira" {
  name        = "${local.name_prefix}-redis-subnet-group"
  subnet_ids  = aws_subnet.private[*].id
  description = "Private subnet group for KIRA ElastiCache Redis"

  tags = {
    Name = "${local.name_prefix}-redis-subnet-group"
  }
}

# ---------------------------------------------------------------------------
# ElastiCache Parameter Group
# ---------------------------------------------------------------------------

resource "aws_elasticache_parameter_group" "kira" {
  name        = "${local.name_prefix}-redis7"
  family      = "redis7"
  description = "KIRA Redis 7 parameter group"

  # Require clients to authenticate (AUTH token set on the replication group)
  parameter {
    name  = "activerehashing"
    value = "yes"
  }

  # Notify keyspace events for expired keys (used by session management)
  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  tags = {
    Name = "${local.name_prefix}-redis7-params"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ---------------------------------------------------------------------------
# KMS Key for Redis at-rest encryption
# ---------------------------------------------------------------------------

resource "aws_kms_key" "redis" {
  description             = "KMS key for ElastiCache Redis encryption — ${local.name_prefix}"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "redis" {
  name          = "alias/${local.name_prefix}-redis"
  target_key_id = aws_kms_key.redis.key_id
}

# ---------------------------------------------------------------------------
# ElastiCache Replication Group (Redis)
# Phase 1: single node, cluster mode disabled.
# Phase 2: set num_cache_clusters = 2 (adds read replica) or enable cluster mode.
# ---------------------------------------------------------------------------

resource "aws_elasticache_replication_group" "kira" {
  replication_group_id = local.name_prefix
  description          = "KIRA Redis ${var.redis_engine_version} — ${var.environment}"

  # Engine
  engine               = "redis"
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.kira.name

  # Single-node for Phase 1; set to 2 to add a read replica
  num_cache_clusters = var.redis_num_cache_nodes

  # Cluster mode disabled (required for Celery compatibility)
  automatic_failover_enabled = var.redis_num_cache_nodes > 1
  multi_az_enabled           = var.redis_num_cache_nodes > 1

  # Networking
  subnet_group_name  = aws_elasticache_subnet_group.kira.name
  security_group_ids = [aws_security_group.redis.id]

  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = aws_kms_key.redis.arn
  auth_token                 = random_password.redis_auth_token.result

  # Maintenance and snapshots
  maintenance_window       = "sun:05:00-sun:06:00"
  snapshot_retention_limit = var.redis_snapshot_retention
  snapshot_window          = "03:00-04:00"

  # Auto minor version upgrades
  auto_minor_version_upgrade = true

  # Apply changes during the maintenance window (not immediately)
  apply_immediately = false

  tags = {
    Name = "${local.name_prefix}-redis"
  }

  lifecycle {
    ignore_changes = [auth_token]
  }
}

# Random auth token for Redis in-transit encryption
resource "random_password" "redis_auth_token" {
  length  = 32
  special = false # Redis AUTH token cannot contain special characters
}

# Store Redis auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name                    = "${local.name_prefix}/redis-auth-token"
  description             = "ElastiCache Redis AUTH token"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
    redis_url  = "rediss://:${random_password.redis_auth_token.result}@${aws_elasticache_replication_group.kira.primary_endpoint_address}:6379"
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Alarms for Redis
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${local.name_prefix}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis CPU > 80% for 10 minutes"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.kira.id
  }

  tags = {
    Name = "${local.name_prefix}-redis-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${local.name_prefix}-redis-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis memory usage > 80%"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.kira.id
  }

  tags = {
    Name = "${local.name_prefix}-redis-memory-alarm"
  }
}
