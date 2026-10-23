terraform {
  required_version = ">= 1.6"
  backend "s3" {
    bucket       = "demotrace-623588627433-us-east-1-tfstate"
    key          = "production/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
  required_providers {
    aws     = { source = "hashicorp/aws", version = "~> 6.0" }
    archive = { source = "hashicorp/archive", version = "~> 2.7" }
  }
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
resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "delete-incoming-video-versions"
    status = "Enabled"
    filter { prefix = "incoming/" }

    expiration { days = 1 }
    noncurrent_version_expiration { noncurrent_days = 1 }
    abort_incomplete_multipart_upload { days_after_initiation = 1 }
  }
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
    allowed_methods = ["POST", "PUT"]
    allowed_origins = ["http://localhost:3000", "https://*.vercel.app"]
    allowed_headers = ["content-type", "x-amz-*"]
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
  # This repository uses GitHub's immutable subject claims (owner and repo IDs in the sub), so the
  # name-only form never matches; it is kept in case the setting is switched back. Only the
  # production environment may deploy, never a bare push to a branch.
  github_deploy_subjects = [
    "repo:dmrvcodes@85731803/demotrace@1427533148:environment:production",
    "repo:dmrvcodes/demotrace:environment:production",
  ]
  github_assume = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Principal = { Federated = aws_iam_openid_connect_provider.github.arn }, Action = "sts:AssumeRoleWithWebIdentity", Condition = { StringEquals = { "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com" }, StringLike = { "token.actions.githubusercontent.com:sub" = local.github_deploy_subjects } } }] })
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
  name = "demotrace-deploy-only"
  role = aws_iam_role.github_deploy.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    # AWS provider discovery calls are read-only; write actions are scoped below.
    { Effect = "Allow", Action = ["sts:GetCallerIdentity", "ec2:DescribeAvailabilityZones", "iam:GetRole", "iam:GetRolePolicy", "iam:ListRolePolicies", "iam:ListAttachedRolePolicies", "lambda:GetFunction", "lambda:GetFunctionUrlConfig", "lambda:GetFunctionEventInvokeConfig", "dynamodb:DescribeTable", "ecr:DescribeRepositories", "ecr:DescribeImages", "logs:DescribeLogGroups", "secretsmanager:DescribeSecret", "s3:GetBucket*", "s3:ListBucket"], Resource = "*" },
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], Resource = "arn:aws:s3:::demotrace-623588627433-us-east-1-tfstate/production/*" },
    { Effect = "Allow", Action = ["s3:ListBucket"], Resource = "arn:aws:s3:::demotrace-623588627433-us-east-1-tfstate" },
    { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
    { Effect = "Allow", Action = ["ecr:BatchCheckLayerAvailability", "ecr:CompleteLayerUpload", "ecr:InitiateLayerUpload", "ecr:PutImage", "ecr:UploadLayerPart"], Resource = aws_ecr_repository.worker.arn },
    { Effect = "Allow", Action = ["lambda:UpdateFunctionCode", "lambda:UpdateFunctionConfiguration", "lambda:PutFunctionEventInvokeConfig", "lambda:UpdateFunctionUrlConfig"], Resource = [aws_lambda_function.worker.arn, aws_lambda_function.control.arn] },
    { Effect = "Allow", Action = ["dynamodb:UpdateTable", "dynamodb:UpdateTimeToLive"], Resource = aws_dynamodb_table.jobs.arn },
    { Effect = "Allow", Action = ["logs:PutRetentionPolicy"], Resource = "arn:aws:logs:us-east-1:623588627433:log-group:/aws/lambda/demotrace-*" },
    { Effect = "Allow", Action = ["iam:PassRole"], Resource = [aws_iam_role.worker.arn, aws_iam_role.control.arn], Condition = { StringEquals = { "iam:PassedToService" = "lambda.amazonaws.com" } } },
    { Effect = "Allow", Action = ["iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:AttachRolePolicy", "iam:DetachRolePolicy"], Resource = [aws_iam_role.worker.arn, aws_iam_role.control.arn] }
  ] })
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
    { Effect = "Allow", Action = ["s3:ListBucketVersions"], Resource = aws_s3_bucket.videos.arn, Condition = { StringLike = { "s3:prefix" = ["incoming/*"] } } },
    { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.jobs.arn },
    { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = aws_secretsmanager_secret.anthropic.arn }
  ] })
}

resource "aws_iam_role" "control" {
  name               = "demotrace-control"
  assume_role_policy = local.lambda_assume
}
resource "aws_iam_role_policy_attachment" "control_logs" {
  role       = aws_iam_role.control.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy" "control" {
  name = "job-control-plane"
  role = aws_iam_role.control.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject"], Resource = "${aws_s3_bucket.videos.arn}/incoming/*" },
    { Effect = "Allow", Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"], Resource = aws_dynamodb_table.jobs.arn },
    { Effect = "Allow", Action = ["lambda:InvokeFunction"], Resource = aws_lambda_function.worker.arn }
  ] })
}

data "archive_file" "control" {
  type        = "zip"
  source_file = "${path.module}/../backend/control/lambda/handler.py"
  # A content-addressed path prevents a stale local zip from being re-used by
  # a later Terraform plan after the source handler has changed.
  output_path = "${path.module}/.terraform/control-lambda-${filesha256("${path.module}/../backend/control/lambda/handler.py")}.zip"
}

resource "aws_lambda_function" "control" {
  function_name    = "demotrace-control"
  role             = aws_iam_role.control.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  architectures    = ["arm64"]
  filename         = data.archive_file.control.output_path
  source_code_hash = data.archive_file.control.output_base64sha256
  timeout          = 15
  memory_size      = 512
  environment { variables = {
    JOBS_TABLE_NAME      = aws_dynamodb_table.jobs.name
    VIDEOS_BUCKET_NAME   = aws_s3_bucket.videos.id
    WORKER_FUNCTION_NAME = aws_lambda_function.worker.function_name
    MAX_DAILY_ANALYSES   = "30"
  } }
  depends_on = [aws_cloudwatch_log_group.control]
}

resource "aws_cloudwatch_log_group" "control" {
  name              = "/aws/lambda/demotrace-control"
  retention_in_days = 14
}

resource "aws_lambda_function_url" "control" {
  function_name      = aws_lambda_function.control.function_name
  authorization_type = "NONE"
  cors {
    allow_credentials = false
    allow_headers     = ["authorization", "content-type"]
    allow_methods     = ["GET", "POST"]
    # Lambda URLs accept protocol-level wildcards, not subdomain wildcards.
    # Job tokens protect individual reports; this permits the Vercel preview/production origins.
    allow_origins = ["http://localhost:3000", "https://*"]
    max_age       = 600
  }
}

resource "aws_lambda_permission" "control_public_url" {
  statement_id           = "FunctionUrlPublicAccess"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.control.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
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

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${aws_lambda_function.worker.function_name}"
  retention_in_days = 14
}

resource "aws_lambda_function_event_invoke_config" "worker" {
  function_name                = aws_lambda_function.worker.function_name
  maximum_event_age_in_seconds = 900
  maximum_retry_attempts       = 0
}

output "github_deploy_role_arn" { value = aws_iam_role.github_deploy.arn }

output "videos_bucket" { value = aws_s3_bucket.videos.id }
output "jobs_table" { value = aws_dynamodb_table.jobs.name }
output "anthropic_secret_arn" { value = aws_secretsmanager_secret.anthropic.arn }
output "ecr_repository_url" { value = aws_ecr_repository.worker.repository_url }
output "control_api_url" { value = aws_lambda_function_url.control.function_url }
