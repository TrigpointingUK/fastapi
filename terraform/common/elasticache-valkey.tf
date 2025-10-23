# ElastiCache Serverless for Valkey (MediaWiki caching) - COMMENTED OUT
# Replaced with self-managed ECS Valkey service to reduce costs
# Smallest possible configuration with 100MB storage

# Security group for ElastiCache
# resource "aws_security_group" "elasticache" {
#   name        = "${var.project_name}-elasticache-sg"
#   description = "Security group for ElastiCache Valkey serverless"
#   vpc_id      = aws_vpc.main.id
#
#   # Valkey/Redis port from ECS tasks
#   ingress {
#     description     = "Valkey from ECS tasks"
#     from_port       = 6379
#     to_port         = 6379
#     protocol        = "tcp"
#     security_groups = [aws_security_group.mediawiki_ecs.id]
#   }
#
#   ingress {
#     description     = "Valkey from bastion (for maintenance)"
#     from_port       = 6379
#     to_port         = 6379
#     protocol        = "tcp"
#     security_groups = [aws_security_group.bastion.id]
#   }
#
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-elasticache-sg"
#   }
# }

# ElastiCache subnet group
# resource "aws_elasticache_subnet_group" "main" {
#   name       = "${var.project_name}-cache-subnet-group"
#   subnet_ids = aws_subnet.private[*].id
#
#   tags = {
#     Name = "${var.project_name}-cache-subnet-group"
#   }
# }

# ElastiCache Serverless Cache (Valkey)
# resource "aws_elasticache_serverless_cache" "valkey" {
#   engine = "valkey"
#   name   = "${var.project_name}-valkey"
#
#   cache_usage_limits {
#     data_storage {
#       maximum = 1 # 1 GB is the minimum for serverless
#       unit    = "GB"
#     }
#     ecpu_per_second {
#       maximum = 1000 # Minimum ECPUs for serverless
#     }
#   }
#
#   daily_snapshot_time      = "03:00"
#   description              = "Valkey serverless cache for MediaWiki"
#   major_engine_version     = "7"
#   snapshot_retention_limit = 1
#   security_group_ids       = [aws_security_group.elasticache.id]
#   subnet_ids               = aws_subnet.private[*].id
#
#   tags = {
#     Name = "${var.project_name}-valkey-cache"
#   }
# }
