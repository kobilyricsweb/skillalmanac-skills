terraform {
  required_version = ">= 1.5"
}

module "network" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "core"
}

module "ci" {
  source = "git::https://example.com/org/ci.git"
}

resource "aws_security_group" "web" {
  name = "web"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
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
  acl    = "public-read"
  tags = {
    env = "prod"
  }
}

resource "aws_db_instance" "main" {
  identifier          = "main"
  engine              = "postgres"
  publicly_accessible = true
  password            = "Sup3rS3cretPw"
  skip_final_snapshot = true
}

resource "aws_iam_policy" "admin" {
  name   = "admin"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]
}
EOF
}

resource "aws_cloudwatch_log_group" "app" {
  name = "/app"
}

# access_key = "AKIAABCDEFGHIJKLMNOP"
# iac-scan: ignore TAG-MISSING
resource "aws_ebs_volume" "data" {
  availability_zone = "us-east-1a"
  size              = 100
}
