# ---------------------------------------------------------------------------
# ALB Security Group
# Allows inbound HTTP/HTTPS from the internet; Kong pods communicate with it.
# ---------------------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Allow HTTP/HTTPS inbound from internet to the Application Load Balancer"
  vpc_id      = aws_vpc.kira.id

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-alb-sg"
  }
}

# ---------------------------------------------------------------------------
# EKS Cluster (control plane) Security Group
# Manages communication between the EKS control plane and worker nodes.
# ---------------------------------------------------------------------------

resource "aws_security_group" "eks_cluster" {
  name        = "${local.name_prefix}-eks-cluster-sg"
  description = "EKS cluster control plane security group"
  vpc_id      = aws_vpc.kira.id

  egress {
    description = "All outbound (control plane to nodes)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-eks-cluster-sg"
  }
}

# Allow worker nodes to communicate with the control plane API
resource "aws_security_group_rule" "eks_cluster_from_nodes" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_cluster.id
  source_security_group_id = aws_security_group.eks_nodes.id
  description              = "Allow nodes to reach the cluster API server"
}

# ---------------------------------------------------------------------------
# EKS Worker Nodes Security Group
# ---------------------------------------------------------------------------

resource "aws_security_group" "eks_nodes" {
  name        = "${local.name_prefix}-eks-nodes-sg"
  description = "EKS worker node security group"
  vpc_id      = aws_vpc.kira.id

  # Node-to-node communication (required for pod networking)
  ingress {
    description = "Node-to-node all traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Control plane to node communication (kubelet, webhooks)
  ingress {
    description             = "Control plane to node kubelets and webhooks"
    from_port               = 1025
    to_port                 = 65535
    protocol                = "tcp"
    security_group_id       = aws_security_group.eks_nodes.id
    source_security_group_id = aws_security_group.eks_cluster.id
  }

  # ALB health checks and traffic to NodePort/pod ports
  ingress {
    description             = "ALB to node ports"
    from_port               = 1024
    to_port                 = 65535
    protocol                = "tcp"
    security_group_id       = aws_security_group.eks_nodes.id
    source_security_group_id = aws_security_group.alb.id
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-eks-nodes-sg"
    # Required for EKS to discover which SG belongs to the cluster
    "kubernetes.io/cluster/${local.name_prefix}" = "owned"
  }
}

# Allow control plane to reach nodes on all ports (required for managed addons)
resource "aws_security_group_rule" "nodes_from_cluster" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  security_group_id        = aws_security_group.eks_nodes.id
  source_security_group_id = aws_security_group.eks_cluster.id
  description              = "Allow all traffic from control plane to nodes"
}

# ---------------------------------------------------------------------------
# RDS Security Group
# Only EKS worker nodes may connect.
# ---------------------------------------------------------------------------

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Allow PostgreSQL from EKS worker nodes only"
  vpc_id      = aws_vpc.kira.id

  ingress {
    description             = "PostgreSQL from EKS nodes"
    from_port               = 5432
    to_port                 = 5432
    protocol                = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-rds-sg"
  }
}

# ---------------------------------------------------------------------------
# ElastiCache Redis Security Group
# Only EKS worker nodes may connect.
# ---------------------------------------------------------------------------

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Allow Redis from EKS worker nodes only"
  vpc_id      = aws_vpc.kira.id

  ingress {
    description             = "Redis from EKS nodes"
    from_port               = 6379
    to_port                 = 6379
    protocol                = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-redis-sg"
  }
}

# ---------------------------------------------------------------------------
# MSK (Kafka) Security Group
# ---------------------------------------------------------------------------

resource "aws_security_group" "msk" {
  name        = "${local.name_prefix}-msk-sg"
  description = "Allow Kafka (TLS) from EKS worker nodes only"
  vpc_id      = aws_vpc.kira.id

  ingress {
    description             = "Kafka TLS from EKS nodes"
    from_port               = 9094
    to_port                 = 9094
    protocol                = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
  }

  ingress {
    description             = "Kafka plaintext from EKS nodes (internal only)"
    from_port               = 9092
    to_port                 = 9092
    protocol                = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
  }

  ingress {
    description             = "ZooKeeper (if needed) from EKS nodes"
    from_port               = 2181
    to_port                 = 2181
    protocol                = "tcp"
    source_security_group_id = aws_security_group.eks_nodes.id
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-msk-sg"
  }
}
