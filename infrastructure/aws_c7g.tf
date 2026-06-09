# ──────────────────────────────────────────────────────────────────
# AWS C7g Instances - Cloud-based Low-Latency Infrastructure
# Hybrid Cloud & Colocation for XAUUSD Trading Pipeline
# ──────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for C7g instances"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "atikulbank-pipeline"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "production"
}

# ── VPC for Low-Latency Network ────────────────────────────────────

resource "aws_vpc" "trading" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project_name}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "trading_az1" {
  vpc_id            = aws_vpc.trading.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name = "${var.project_name}-subnet-az1"
  }
}

resource "aws_subnet" "trading_az2" {
  vpc_id            = aws_vpc.trading.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name = "${var.project_name}-subnet-az2"
  }
}

# ── C7g Instance (ARM-based Graviton3) ────────────────────────────
# C7g instances use AWS Graviton3 processors for best price/performance
# and lowest latency for compute-intensive workloads.

resource "aws_instance" "trading_primary" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "c7g.large"  # 2 vCPU, 4 GB - cost efficient
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.trading_az1.id

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
    iops        = 3000
    throughput  = 125
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "${var.project_name}-primary"
    Role        = "trading-pipeline"
    Environment = var.environment
  }
}

resource "aws_instance" "trading_secondary" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "c7g.xlarge"  # 4 vCPU, 8 GB - ML inference
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.trading_az2.id

  root_block_device {
    volume_size = 100
    volume_type = "gp3"
    iops        = 6000
    throughput  = 250
  }

  tags = {
    Name        = "${var.project_name}-secondary"
    Role        = "ml-inference"
    Environment = var.environment
  }
}

# ── C7g Spot Instance for Batch Training ───────────────────────────

resource "aws_spot_instance_request" "training" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "c7g.2xlarge"  # 8 vCPU, 16 GB
  spot_price             = "0.15"
  wait_for_fulfillment   = true
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.trading_az1.id

  root_block_device {
    volume_size = 200
    volume_type = "gp3"
    iops        = 10000
    throughput  = 500
  }

  tags = {
    Name        = "${var.project_name}-training-spot"
    Role        = "batch-training"
    Environment = var.environment
  }
}

# ── Elastic Fabric Adapter (EFA) for Multi-Node ────────────────────

resource "aws_network_interface" "efa_primary" {
  subnet_id       = aws_subnet.trading_az1.id
  security_groups = [aws_security_group.trading.id]

  tags = {
    Name = "${var.project_name}-efa-primary"
  }
}

# ── Security Group ─────────────────────────────────────────────────

resource "aws_security_group" "trading" {
  name_prefix = "${var.project_name}-"
  vpc_id      = aws_vpc.trading.id

  # FIX protocol port
  ingress {
    from_port   = 9876
    to_port     = 9876
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "FIX protocol"
  }

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "SSH access"
  }

  # Prometheus metrics
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "Metrics"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

variable "admin_cidr" {
  description = "CIDR block for admin access"
  type        = string
  default     = "0.0.0.0/0"
}

# ── Key Pair ───────────────────────────────────────────────────────

resource "aws_key_pair" "trading" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

# ── AMI Data Source ────────────────────────────────────────────────

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-arm64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── CloudWatch Alarms ─────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU utilization > 80%"
  dimensions = {
    InstanceId = aws_instance.trading_primary.id
  }
}

# ── S3 Bucket for Checkpoints ─────────────────────────────────────

resource "aws_s3_bucket" "checkpoints" {
  bucket = "${var.project_name}-checkpoints-${var.environment}"

  tags = {
    Name        = "${var.project_name}-checkpoints"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "checkpoints" {
  bucket = aws_s3_bucket.checkpoints.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ── Outputs ────────────────────────────────────────────────────────

output "primary_instance_id" {
  value = aws_instance.trading_primary.id
}

output "secondary_instance_id" {
  value = aws_instance.trading_secondary.id
}

output "primary_public_ip" {
  value = aws_instance.trading_primary.public_ip
}

output "secondary_public_ip" {
  value = aws_instance.trading_secondary.public_ip
}

output "checkpoint_bucket" {
  value = aws_s3_bucket.checkpoints.bucket
}
