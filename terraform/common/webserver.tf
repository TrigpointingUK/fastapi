# Web Server Instance in Private Subnet
resource "aws_instance" "webserver" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  key_name      = var.key_pair_name

  subnet_id                   = aws_subnet.private[0].id
  vpc_security_group_ids      = [aws_security_group.webserver.id]
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.webserver.name

  # Enable detailed monitoring
  monitoring = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    http_put_response_hop_limit = 1
  }

  user_data = base64encode(templatefile("${path.module}/webserver_user_data.sh", {
    db_endpoint = aws_db_instance.main.endpoint
    db_username = "fastapi_user"
    db_password = "temp-password-change-this"
  }))

  tags = {
    Name = "${var.project_name}-webserver"
  }
}

# Security Group for Web Server
resource "aws_security_group" "webserver" {
  name        = "${var.project_name}-webserver-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.main.id

  # SSH access from bastion host
  ingress {
    description     = "SSH from bastion host"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # HTTP access from ALB (will be added by environment-specific configs)
  ingress {
    description = "HTTP from ALB"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-webserver-sg"
  }
}

# IAM Role for Web Server
resource "aws_iam_role" "webserver" {
  name = "${var.project_name}-webserver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-webserver-role"
  }
}

# Attach SSM policy to webserver role
resource "aws_iam_role_policy_attachment" "webserver_ssm" {
  role       = aws_iam_role.webserver.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile for webserver
resource "aws_iam_instance_profile" "webserver" {
  name = "${var.project_name}-webserver-profile"
  role = aws_iam_role.webserver.name
}
