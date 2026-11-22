provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      owner = "platform"
    }
  }
}

module "network" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_security_group" "web" {
  name = "web"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket" "assets" {
  bucket = "acme-assets"
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_db_instance" "main" {
  identifier              = "main"
  engine                  = "postgres"
  storage_encrypted       = true
  deletion_protection     = true
  backup_retention_period = 7
  password                = var.db_password
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/app"
  retention_in_days = 30
}
