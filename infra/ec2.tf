resource "aws_instance" "rt_dashboard" {
  ami                    = "ami-08618906934470b52"  # Amazon Linux 2023, arm64
  instance_type          = "t4g.small"
  vpc_security_group_ids = [aws_security_group.rt_dashboard.id]
  iam_instance_profile   = aws_iam_instance_profile.rt_dashboard_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name    = "rt-dashboard"
    Project = "rt-dashboard"
  }
}

output "instance_public_ip" {
  value = aws_instance.rt_dashboard.public_ip
}

output "instance_id" {
  value = aws_instance.rt_dashboard.id
}
