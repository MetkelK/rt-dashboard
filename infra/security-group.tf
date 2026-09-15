resource "aws_security_group" "rt_dashboard" {
  name        = "rt-dashboard-sg"
  description = "Security group for rt-dashboard streaming project"

  # No SSH ingress rule - access via SSM Session Manager only

  ingress {
    description = "FastAPI backend"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "rt-dashboard-sg"
    Project = "rt-dashboard"
  }
}
