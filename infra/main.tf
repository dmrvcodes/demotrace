terraform {
  required_version = ">= 1.6"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 6.0" } }
}

provider "aws" { region = "us-east-1" }
data "aws_caller_identity" "current" {}

locals {
  bucket = "demotrace-${data.aws_caller_identity.current.account_id}-us-east-1"
}

resource "aws_s3_bucket" "videos" { bucket = local.bucket }
resource "aws_s3_bucket_public_access_block" "videos" {
  bucket                  = aws_s3_bucket.videos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_cors_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id
  cors_rule {
    allowed_methods = ["PUT"]
    allowed_origins = ["http://localhost:3000", "https://*.vercel.app"]
    allowed_headers = ["content-type"]
  }
}
resource "aws_dynamodb_table" "jobs" {
  name         = "demotrace-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  attribute {
    name = "pk"
    type = "S"
  }
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}
resource "aws_ecr_repository" "worker" { name = "demotrace-worker" }
resource "aws_secretsmanager_secret" "anthropic" {
  name                    = "demotrace/anthropic-api-key"
  recovery_window_in_days = 0
}

output "videos_bucket" { value = aws_s3_bucket.videos.id }
output "jobs_table" { value = aws_dynamodb_table.jobs.name }
output "anthropic_secret_arn" { value = aws_secretsmanager_secret.anthropic.arn }
output "ecr_repository_url" { value = aws_ecr_repository.worker.repository_url }
