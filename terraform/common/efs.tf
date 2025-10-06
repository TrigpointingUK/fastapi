# EFS for phpBB persistent storage

resource "aws_security_group" "efs" {
  name        = "${var.project_name}-efs-sg"
  description = "Security group for EFS allowing NFS from ECS tasks and webserver"
  vpc_id      = aws_vpc.main.id

  # Allow NFS from within VPC (tighten later to ECS SGs when forum ECS exists)
  ingress {
    description = "NFS from VPC"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  # Explicitly allow NFS from bastion host
  ingress {
    description     = "NFS from bastion"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-efs-sg"
  }
}

resource "aws_efs_file_system" "phpbb" {
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  encrypted = true

  tags = {
    Name        = "phpbb-efs"
    Application = "phpbb"
  }
}

resource "aws_efs_mount_target" "phpbb" {
  count           = length(aws_subnet.private)
  file_system_id  = aws_efs_file_system.phpbb.id
  subnet_id       = aws_subnet.private[count.index].id
  security_groups = [aws_security_group.efs.id]
}

# Access point with www-data uid/gid=33 so Fargate writes as phpBB
resource "aws_efs_access_point" "phpbb" {
  file_system_id = aws_efs_file_system.phpbb.id

  posix_user {
    gid = 33
    uid = 33
  }

  root_directory {
    path = "/phpbb"
    creation_info {
      owner_gid   = 33
      owner_uid   = 33
      permissions = "0775"
    }
  }

  tags = {
    Name        = "phpbb-access-point"
    Application = "phpbb"
  }
}
