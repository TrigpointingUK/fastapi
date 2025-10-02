# Target Group for webserver instance (for testing ALB + nginx)
resource "aws_lb_target_group" "webserver" {
  name        = "${var.project_name}-webserver-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.project_name}-webserver-tg"
  }
}

# Attach webserver instance to target group
resource "aws_lb_target_group_attachment" "webserver" {
  target_group_arn = aws_lb_target_group.webserver.arn
  target_id        = aws_instance.webserver.id
  port             = 80
}

# Listener rules for test domains
resource "aws_lb_listener_rule" "test1" {
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 110

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webserver.arn
  }

  condition {
    host_header {
      values = ["test1.trigpointing.me"]
    }
  }

  tags = {
    Name = "${var.project_name}-test1-listener-rule"
  }
}

resource "aws_lb_listener_rule" "test2" {
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 111

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webserver.arn
  }

  condition {
    host_header {
      values = ["test2.trigpointing.me"]
    }
  }

  tags = {
    Name = "${var.project_name}-test2-listener-rule"
  }
}

# Production listener rules for trigpointing.uk domains
resource "aws_lb_listener_rule" "forum" {
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 120

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webserver.arn
  }

  condition {
    host_header {
      values = ["forum.trigpointing.uk"]
    }
  }

  tags = {
    Name = "${var.project_name}-forum-listener-rule"
  }
}

# phpMyAdmin listener rule moved to phpmyadmin.tf when phpMyAdmin ECS service is enabled

resource "aws_lb_listener_rule" "static" {
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 122

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.webserver.arn
  }

  condition {
    host_header {
      values = ["static.trigpointing.uk"]
    }
  }

  tags = {
    Name = "${var.project_name}-static-listener-rule"
  }
}

# Wiki listener rule moved to mediawiki.tf when MediaWiki ECS service is enabled
