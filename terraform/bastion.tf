# Bastion Host for secure database access
resource "aws_instance" "bastion" {
  count = var.environment == "staging" && var.admin_ip_address != null ? 1 : 0

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  key_name      = var.key_pair_name

  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.bastion[0].id]
  associate_public_ip_address = true

  user_data = base64encode(templatefile("${path.module}/bastion_user_data.sh", {
    db_endpoint = aws_db_instance.main.endpoint
    db_username = var.db_username
    db_password = var.db_password
  }))

  tags = {
    Name = "${var.project_name}-${var.environment}-bastion"
  }
}

# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group for Bastion Host
resource "aws_security_group" "bastion" {
  count = var.environment == "staging" && var.admin_ip_address != null ? 1 : 0

  name        = "${var.project_name}-${var.environment}-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH from admin IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.admin_ip_address}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-bastion-sg"
  }
}

# Update RDS security group to allow bastion access
resource "aws_security_group_rule" "rds_from_bastion" {
  count = var.environment == "staging" && var.admin_ip_address != null ? 1 : 0

  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion[0].id
  security_group_id        = aws_security_group.rds.id
  description              = "MySQL from bastion host"
}
