variable "discord_token" {
  description = "The Discord bot token"
  type        = string
  sensitive   = true
}

variable "pr_api_token" {
  description = "PR API token"
  type        = string
  sensitive   = true
}

variable "channel_id" {
  description = "PR API token"
  type        = string
  sensitive   = true
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "allow_tls" {
  name        = "terraform-firewall"
  description = "allow tls"
}

resource "aws_vpc_security_group_ingress_rule" "allow_tls_ipv4" {
  security_group_id = aws_security_group.allow_tls.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {
  security_group_id = aws_security_group.allow_tls.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1" # semantically equivalent to all ports
}

resource "aws_instance" "license_scanner_bot" {
  ami           = "ami-0fa3fe0fa7920f68e"
  instance_type = "t3.micro"

  iam_instance_profile   = aws_iam_instance_profile.ec2_ecr_instance_profile.name
  vpc_security_group_ids = [aws_security_group.allow_tls.id]

  tags = {
    Name = "license_scanner_bot"
  }

  user_data = <<-EOF
      #!/bin/bash
      # Update OS
      yum update -y

      # Install Docker
      amazon-linux-extras install docker -y || yum install docker -y
      sudo usermod -aG docker ec2-user
      systemctl start docker
      systemctl enable docker

      # Login to ECR (uses IAM role)
      aws ecr get-login-password --region us-east-1 \
        | docker login --username AWS --password-stdin 390403880719.dkr.ecr.us-east-1.amazonaws.com

      # Pull your bot image
      docker pull 390403880719.dkr.ecr.us-east-1.amazonaws.com/license_scanner_bot:v1.0.0

      # Run the container
      docker run -d --name license_scanner_bot \
        -e DISCORD_TOKEN="${var.discord_token}" \
        -e CHANNEL_ID="${var.channel_id}" \
        -e PR_API_TOKEN="${var.pr_api_token}" \
        390403880719.dkr.ecr.us-east-1.amazonaws.com/license_scanner_bot:v1.0.0 
    EOF
}

resource "aws_ecr_repository" "license_scanner_bot" {
  name                 = "license_scanner_bot"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "license_scanner_bot_policy" {
  repository = aws_ecr_repository.license_scanner_bot.name

  policy = <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Expire images older than 2 days",
      "selection": {
        "tagStatus": "any",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 2
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF
}


resource "aws_iam_role" "ec2_ecr_role" {
  name = "ec2-ecr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "ec2_ecr_readonly" {
  role       = aws_iam_role.ec2_ecr_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}


resource "aws_iam_instance_profile" "ec2_ecr_instance_profile" {
  name = "ec2-ecr-instance-profile"
  role = aws_iam_role.ec2_ecr_role.name
}
