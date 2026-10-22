terraform {
  required_version = ">= 1.6"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 6.0" } }
}

provider "aws" { region = "us-east-1" }
data "aws_caller_identity" "current" {}
variable "anthropic_model" {
  description = "The one place the model is chosen; the worker reads it as ANTHROPIC_MODEL."
  type        = string
  default     = "claude-sonnet-4-6"
}
variable "worker_image_digest" {
  description = "sha256 digest of the worker image in ECR; deploys are pinned to it, never to a tag."
  type        = string
  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.worker_image_digest))
    error_message = "worker_image_digest must look like sha256:<64 hex>."
  }
}

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

locals {
  lambda_assume = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }] })
  github_assume = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Federated = aws_iam_openid_connect_provider.github.arn }, Action = "sts:AssumeRoleWithWebIdentity", Condition = { StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" }, StringLike = { "token.actions.githubusercontent.com:sub" = "repo:dmrvcodes/demotrace:ref:refs/heads/main" } } }] })
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]
}
resource "aws_iam_role" "github_deploy" {
  name               = "demotrace-github-deploy"
  assume_role_policy = local.github_assume
}
resource "aws_iam_role_policy" "github_deploy" {
  name   = "demotrace-deploy-only"
  role   = aws_iam_role.github_deploy.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = ["s3:*", "dynamodb:*", "ecr:*", "lambda:*", "logs:*", "iam:GetRole", "iam:CreateRole", "iam:DeleteRole", "iam:PassRole", "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:AttachRolePolicy", "iam:DetachRolePolicy", "secretsmanager:DescribeSecret"], Resource = "*" }] })
}

resource "aws_iam_role" "worker" {
  name               = "demotrace-worker"
  assume_role_policy = local.lambda_assume
}
resource "aws_iam_role_policy_attachment" "worker_logs" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy" "worker" {
  name = "data-and-secret"
  role = aws_iam_role.worker.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["s3:GetObjectVersion", "s3:DeleteObjectVersion"], Resource = "${aws_s3_bucket.videos.arn}/incoming/*" },
    { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.jobs.arn },
    { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_secretsmanager_secret.anthropic.arn }
  ] })
}
resource "aws_lambda_function" "worker" {
  function_name = "demotrace-worker"
  role          = aws_iam_role.worker.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.worker.repository_url}@${var.worker_image_digest}"
  architectures = ["arm64"]
  timeout       = 900
  memory_size   = 3008
  ephemeral_storage { size = 2048 } # video up to 150 MB plus frames and audio in /tmp
  environment { variables = { JOBS_TABLE_NAME = aws_dynamodb_table.jobs.name, VIDEOS_BUCKET_NAME = aws_s3_bucket.videos.id, ANTHROPIC_SECRET_ARN = aws_secretsmanager_secret.anthropic.arn, ANTHROPIC_MODEL = var.anthropic_model } }
}

output "github_deploy_role_arn" { value = aws_iam_role.github_deploy.arn }

output "videos_bucket" { value = aws_s3_bucket.videos.id }
output "jobs_table" { value = aws_dynamodb_table.jobs.name }
output "anthropic_secret_arn" { value = aws_secretsmanager_secret.anthropic.arn }
output "ecr_repository_url" { value = aws_ecr_repository.worker.repository_url }
