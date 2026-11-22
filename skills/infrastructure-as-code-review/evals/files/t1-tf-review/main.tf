resource "aws_security_group" "db" {
  name = "orders-db"

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "orders" {
  identifier             = "orders"
  engine                 = "postgres"
  instance_class         = "db.t3.medium"
  allocated_storage      = 50
  username               = "app"
  password               = "orders-Prod-2024"
  vpc_security_group_ids = [aws_security_group.db.id]
  tags = {
    Name = "orders"
  }
}

resource "aws_s3_bucket" "exports" {
  bucket = "orders-exports"
  acl    = "public-read"
}

resource "aws_iam_role_policy" "worker" {
  name = "worker"
  role = "orders-worker"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "sqs:*"]
      Resource = "*"
    }]
  })
}

resource "aws_cloudwatch_log_group" "worker" {
  name = "/orders/worker"
}
