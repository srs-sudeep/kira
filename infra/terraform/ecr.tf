# ---------------------------------------------------------------------------
# ECR Repositories — one per service
# ---------------------------------------------------------------------------

resource "aws_ecr_repository" "services" {
  for_each = toset(local.services)

  name                 = "kira/${each.key}"
  image_tag_mutability = "MUTABLE" # allow re-tagging the :latest pointer

  image_scanning_configuration {
    # Scan every image on push — results visible in ECR console and Security Hub
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }

  tags = {
    Name    = "kira/${each.key}"
    Service = each.key
  }
}

# ---------------------------------------------------------------------------
# ECR Lifecycle Policies
# Keep the last 20 tagged images per service.
# Untagged images (intermediate build layers) are expired after 1 day.
# ---------------------------------------------------------------------------

resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 2
        description  = "Keep last 20 SHA-tagged images"
        selection = {
          tagStatus      = "tagged"
          tagPrefixList  = ["sha-", "v"]
          countType      = "imageCountMoreThan"
          countNumber    = 20
        }
        action = { type = "expire" }
      },
      {
        rulePriority = 3
        description  = "Keep last 5 latest-tagged images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = { type = "expire" }
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# ECR Repository Policies
# Grants the CI/CD IAM user push access and EKS node role pull access.
# ---------------------------------------------------------------------------

resource "aws_ecr_repository_policy" "services" {
  for_each   = aws_ecr_repository.services
  repository = each.value.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCICDPush"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_user.cicd.arn
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeRepositories",
          "ecr:GetRepositoryPolicy",
          "ecr:ListImages",
          "ecr:DeleteRepository",
          "ecr:BatchDeleteImage",
          "ecr:DescribeImages",
        ]
      },
      {
        Sid    = "AllowEKSNodePull"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.eks_node_group.arn
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
        ]
      },
    ]
  })
}

# ---------------------------------------------------------------------------
# KMS Key for ECR encryption
# ---------------------------------------------------------------------------

resource "aws_kms_key" "ecr" {
  description             = "KMS key for ECR image encryption — ${local.name_prefix}"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "ecr" {
  name          = "alias/${local.name_prefix}-ecr"
  target_key_id = aws_kms_key.ecr.key_id
}
