# =============================================================================
# AWS C7g HYBRID CLOUD INFRASTRUCTURE
# High-Performance Trading Pipeline on AWS Graviton3
# =============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# -----------------------------------------------------------------------------
# PROVIDER CONFIGURATION
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AtikulBank-Trading"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Stack       = "MasterPipeline"
    }
  }
}

# -----------------------------------------------------------------------------
# VARIABLES
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type_primary" {
  description = "Primary instance type (C7g for Graviton3)"
  type        = string
  default     = "c7g.large"
}

variable "instance_type_ml" {
  description = "ML inference instance type"
  type        = string
  default     = "c7g.xlarge"
}

variable "instance_type_training" {
  description = "Training instance type"
  type        = string
  default     = "c7g.2xlarge"
}

# -----------------------------------------------------------------------------
# VPC & NETWORKING
# -----------------------------------------------------------------------------

resource "aws_vpc" "trading" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.environment}-trading-vpc"
  }
}

resource "aws_internet_gateway" "trading" {
  vpc_id = aws_vpc.trading.id
  
  tags = {
    Name = "${var.environment}-trading-igw"
  }
}

resource "aws_subnet" "private_az1" {
  vpc_id            = aws_vpc.trading.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone = "${var.aws_region}a"
  
  tags = {
    Name = "${var.environment}-private-az1"
    Tier = "private"
  }
}

resource "aws_subnet" "private_az2" {
  vpc_id            = aws_vpc.trading.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 2)
  availability_zone = "${var.aws_region}b"
  
  tags = {
    Name = "${var.environment}-private-az2"
    Tier = "private"
  }
}

resource "aws_subnet" "public_az1" {
  vpc_id            = aws_vpc.trading.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 101)
  availability_zone = "${var.aws_region}a"
  
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.environment}-public-az1"
    Tier = "public"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.trading.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.trading.id
  }
  
  tags = {
    Name = "${var.environment}-private-rt"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.trading.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.trading.id
  }
  
  tags = {
    Name = "${var.environment}-public-rt"
  }
}

resource "aws_route_table_association" "private_az1" {
  subnet_id      = aws_subnet.private_az1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_az2" {
  subnet_id      = aws_subnet.private_az2.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "public_az1" {
  subnet_id      = aws_subnet.public_az1.id
  route_table_id = aws_route_table.public.id
}

# -----------------------------------------------------------------------------
# SECURITY GROUPS
# -----------------------------------------------------------------------------

resource "aws_security_group" "trading" {
  name_prefix = "${var.environment}-trading-"
  vpc_id      = aws_vpc.trading.id
  
  # FIX Protocol
  ingress {
    from_port   = 9876
    to_port     = 9876
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "FIX Protocol"
  }
  
  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
    description = "SSH Access"
  }
  
  # Internal communication
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
    description = "Internal"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound"
  }
  
  tags = {
    Name = "${var.environment}-trading-sg"
  }
}

variable "admin_cidr" {
  description = "Admin CIDR for SSH access"
  type        = string
  default     = "0.0.0.0/0"
}

# -----------------------------------------------------------------------------
# C7g INSTANCES - PRIMARY TRADING PIPELINE
# -----------------------------------------------------------------------------

resource "aws_instance" "trading_primary" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type_primary
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.private_az1.id
  
  # C7g Optimization
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
  
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 100
    iops                  = 6000
    throughput            = 250
    encrypted             = true
    delete_on_termination = true
  }
  
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp3"
    volume_size           = 500
    iops                  = 16000
    throughput            = 1000
    encrypted             = true
    delete_on_termination = true
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    role = "primary"
  }))
  
  tags = {
    Name = "${var.environment}-trading-primary"
    Role = "primary-pipeline"
  }
}

# -----------------------------------------------------------------------------
# C7g INSTANCES - ML INFERENCE
# -----------------------------------------------------------------------------

resource "aws_instance" "ml_inference" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type_ml
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.private_az2.id
  
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 100
    iops                  = 6000
    throughput            = 250
    encrypted             = true
    delete_on_termination = true
  }
  
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp3"
    volume_size           = 1000
    iops                  = 16000
    throughput            = 1000
    encrypted             = true
    delete_on_termination = true
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    role = "ml-inference"
  }))
  
  tags = {
    Name = "${var.environment}-ml-inference"
    Role = "ml-inference"
  }
}

# -----------------------------------------------------------------------------
# C7g SPOT INSTANCES - TRAINING (Cost Optimized)
# -----------------------------------------------------------------------------

resource "aws_spot_instance_request" "training" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type_training
  key_name               = aws_key_pair.trading.key_name
  vpc_security_group_ids = [aws_security_group.trading.id]
  subnet_id              = aws_subnet.private_az1.id
  
  spot_type            = "one-time"
  wait_for_fulfillment = true
  
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 100
    iops                  = 6000
    throughput            = 250
    encrypted             = true
    delete_on_termination = true
  }
  
  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_type           = "gp3"
    volume_size           = 2000
    iops                  = 16000
    throughput            = 1000
    encrypted             = true
    delete_on_termination = true
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    role = "training"
  }))
  
  tags = {
    Name = "${var.environment}-training-spot"
    Role = "batch-training"
  }
}

# -----------------------------------------------------------------------------
# KEY PAIR
# -----------------------------------------------------------------------------

resource "aws_key_pair" "trading" {
  key_name   = "${var.environment}-trading-key"
  public_key = var.ssh_public_key
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

# -----------------------------------------------------------------------------
# AMI DATA SOURCE
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# S3 BUCKET FOR CHECKPOINTS & MODELS
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "models" {
  bucket = "${var.environment}-atikulbank-models"
  
  tags = {
    Name = "${var.environment}-models-bucket"
  }
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  
  rule {
    id     = "cleanup-old-models"
    status = "Enabled"
    
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# -----------------------------------------------------------------------------
# CLOUDWATCH MONITORING
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.environment}-trading-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  
  dimensions = {
    InstanceId = aws_instance.trading_primary.id
  }
  
  alarm_description = "Trading pipeline CPU utilization > 80%"
}

resource "aws_cloudwatch_metric_alarm" "memory_high" {
  alarm_name          = "${var.environment}-trading-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "mem_used_percent"
  namespace           = "CWAgent"
  period              = 300
  statistic           = "Average"
  threshold           = 85
  
  dimensions = {
    InstanceId = aws_instance.trading_primary.id
  }
  
  alarm_description = "Trading pipeline memory utilization > 85%"
}

resource "aws_cloudwatch_log_group" "trading" {
  name              = "/aws/ec2/${var.environment}-trading"
  retention_in_days = 30
  
  tags = {
    Name = "${var.environment}-trading-logs"
  }
}

# -----------------------------------------------------------------------------
# ELASTIC IP FOR FIX CONNECTION
# -----------------------------------------------------------------------------

resource "aws_eip" "trading_primary" {
  instance = aws_instance.trading_primary.id
  domain   = "vpc"
  
  tags = {
    Name = "${var.environment}-trading-eip"
  }
}

# -----------------------------------------------------------------------------
# OUTPUTS
# -----------------------------------------------------------------------------

output "trading_primary_id" {
  description = "Primary trading instance ID"
  value       = aws_instance.trading_primary.id
}

output "trading_primary_private_ip" {
  description = "Primary trading instance private IP"
  value       = aws_instance.trading_primary.private_ip
}

output "trading_primary_public_ip" {
  description = "Primary trading instance public IP (Elastic IP)"
  value       = aws_eip.trading_primary.public_ip
}

output "ml_inference_id" {
  description = "ML inference instance ID"
  value       = aws_instance.ml_inference.id
}

output "ml_inference_private_ip" {
  description = "ML inference instance private IP"
  value       = aws_instance.ml_inference.private_ip
}

output "training_spot_id" {
  description = "Training spot instance ID"
  value       = aws_spot_instance_request.training.spot_instance_id
}

output "models_bucket" {
  description = "S3 bucket for models"
  value       = aws_s3_bucket.models.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.trading.id
}
