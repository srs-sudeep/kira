# ---------------------------------------------------------------------------
# AWS WAF v2 WebACL
# Attached to the ALB (created by Kong Ingress or AWS LBC).
# Provides OWASP Top 10 protection via AWS Managed Rule Groups.
#
# NOTE: WAF WebACLs for ALBs must be created in the same region as the ALB.
# WAF WebACLs for CloudFront must be created in us-east-1.
# ---------------------------------------------------------------------------

resource "aws_wafv2_web_acl" "kira" {
  name        = "${local.name_prefix}-web-acl"
  description = "KIRA WAF — OWASP Top 10 protection for the API gateway ALB"
  scope       = "REGIONAL" # use CLOUDFRONT for CloudFront distributions

  default_action {
    allow {}
  }

  # ── Rule 1: AWS Managed Rules — Common Rule Set (OWASP Top 10) ────────────
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 10

    override_action {
      none {} # count {} to test without blocking
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Exclude rules that may cause false positives on API payloads
        rule_action_override {
          name = "SizeRestrictions_BODY"
          action_to_use {
            count {} # log only; API bodies can be large (bulk ARI updates)
          }
        }

        rule_action_override {
          name = "GenericRFI_BODY"
          action_to_use {
            count {} # RFI checks can fire on JSON with URL-like values
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 2: AWS Known Bad Inputs ──────────────────────────────────────────
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 20

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 3: SQL Injection Protection ─────────────────────────────────────
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 30

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-sqli"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 4: Linux OS exploits ─────────────────────────────────────────────
  rule {
    name     = "AWSManagedRulesLinuxRuleSet"
    priority = 40

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesLinuxRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-linux-rules"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 5: IP Reputation (bots, scanners, known bad actors) ──────────────
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 50

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-ip-reputation"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 6: Bot Control ───────────────────────────────────────────────────
  rule {
    name     = "AWSManagedRulesBotControlRuleSet"
    priority = 60

    override_action {
      count {} # count only — do not block bots until you've reviewed the traffic
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_bot_control_rule_set {
            inspection_level = "COMMON"
          }
        }

        # Allow legitimate API clients (channel OTA callbacks, health checkers)
        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                field_to_match { uri_path {} }
                positional_constraint = "STARTS_WITH"
                search_string         = "/api/v1/channels"
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-bot-control"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 7: Rate limiting — global API throttle ───────────────────────────
  # Complements Kong's per-route rate limiting with a WAF-level hard cap.
  rule {
    name     = "RateLimitGlobal"
    priority = 70

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000 # requests per 5-minute window per IP
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit-global"
      sampled_requests_enabled   = true
    }
  }

  # ── Rule 8: Rate limiting — auth endpoints (brute-force protection) ───────
  rule {
    name     = "RateLimitAuthEndpoints"
    priority = 80

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 100 # 100 login attempts per 5 minutes per IP
        aggregate_key_type = "IP"

        scope_down_statement {
          byte_match_statement {
            field_to_match { uri_path {} }
            positional_constraint = "STARTS_WITH"
            search_string         = "/api/v1/auth"
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit-auth"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-web-acl"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${local.name_prefix}-web-acl"
  }
}

# ---------------------------------------------------------------------------
# WAF Logging — ship sampled requests to CloudWatch Logs
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "waf" {
  # WAF log group names must start with "aws-waf-logs-"
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = 30
}

resource "aws_wafv2_web_acl_logging_configuration" "kira" {
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.kira.arn

  # Redact Authorization headers from WAF logs (never log JWT tokens)
  redacted_fields {
    single_header {
      name = "authorization"
    }
  }
}

# ---------------------------------------------------------------------------
# WAF Association with ALB
# The ALB ARN is created by Kong Ingress / AWS LBC after EKS is deployed.
# Pass it via the variable below or associate it manually after the ALB exists:
#   aws wafv2 associate-web-acl --web-acl-arn <waf-arn> --resource-arn <alb-arn>
# ---------------------------------------------------------------------------

variable "alb_arn" {
  description = "ARN of the Application Load Balancer to associate with the WAF WebACL. Set after Kong/ALB is deployed. Leave empty to skip association."
  type        = string
  default     = ""
}

resource "aws_wafv2_web_acl_association" "alb" {
  count        = var.alb_arn != "" ? 1 : 0
  resource_arn = var.alb_arn
  web_acl_arn  = aws_wafv2_web_acl.kira.arn
}

# ---------------------------------------------------------------------------
# Output the WAF ARN so it can be associated with the ALB in a second apply
# ---------------------------------------------------------------------------

output "waf_web_acl_arn" {
  description = "WAF WebACL ARN — associate with the ALB via alb_arn variable or aws wafv2 associate-web-acl."
  value       = aws_wafv2_web_acl.kira.arn
}
