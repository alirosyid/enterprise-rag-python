provider "aws" {
  region = "ap-southeast-1"
}

resource "aws_instance" "rag_backend" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"
  key_name      = "rag-deploy-key"

  vpc_security_group_ids = [aws_security_group.rag_sg.id]

  tags = {
    Name        = "Enterprise-RAG-Production"
    Environment = "Production"
  }
}

resource "aws_security_group" "rag_sg" {
  name        = "rag_api_gateway_sg"
  description = "Membuka jalur API Gateway, memblokir akses langsung ke Vector DB"

  ingress {
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}