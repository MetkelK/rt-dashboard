data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_elasticache_subnet_group" "rt_dashboard" {
  name       = "rt-dashboard-redis-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_security_group" "redis" {
  name        = "rt-dashboard-redis-sg"
  description = "Allow Redis access from the rt-dashboard EC2 instance only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Redis from EC2"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.rt_dashboard.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "rt-dashboard-redis-sg"
    Project = "rt-dashboard"
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "rt-dashboard-redis"
  engine                = "redis"
  node_type             = "cache.t3.micro"
  num_cache_nodes       = 1
  parameter_group_name  = "default.redis7"
  engine_version        = "7.1"
  port                   = 6379
  subnet_group_name     = aws_elasticache_subnet_group.rt_dashboard.name
  security_group_ids    = [aws_security_group.redis.id]

  tags = {
    Name    = "rt-dashboard-redis"
    Project = "rt-dashboard"
  }
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
