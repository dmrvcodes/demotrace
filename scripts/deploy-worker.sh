#!/usr/bin/env bash
# Build the Worker image for arm64, push it under a dated tag, and apply Terraform pinned to its digest.
# The plan is shown and must be confirmed; nothing is applied blindly.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

: "${AWS_PROFILE:?Set AWS_PROFILE to the DemoTrace profile (direnv loads it from .env)}"
expected="${DEMOTRACE_AWS_ACCOUNT_ID:?Set DEMOTRACE_AWS_ACCOUNT_ID in .env}"
actual="$(aws sts get-caller-identity --query Account --output text)"
if [ "$actual" != "${expected//-/}" ]; then
  echo "Refusing: profile $AWS_PROFILE is not the DemoTrace account" >&2
  exit 3
fi

repo="$(terraform -chdir=infra output -raw ecr_repository_url)"
tag="worker-$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M)"
aws ecr get-login-password | docker login --username AWS --password-stdin "${repo%%/*}"
# Lambda rejects OCI image indexes with attestations, so build a single-platform manifest.
docker buildx build --platform linux/arm64 --provenance=false --sbom=false \
  -f backend/worker/Dockerfile -t "$repo:$tag" --push .
digest="$(aws ecr describe-images --repository-name demotrace-worker --image-ids imageTag="$tag" \
  --query 'imageDetails[0].imageDigest' --output text)"
echo "Pushed $repo:$tag ($digest)"

terraform -chdir=infra plan -input=false -var "worker_image_digest=$digest" -out=worker.tfplan
read -r -p "Read the plan above. Apply it? Type yes: " answer
[ "$answer" = "yes" ] || { echo "Not applied."; exit 1; }
terraform -chdir=infra apply -input=false worker.tfplan
aws lambda wait function-updated-v2 --function-name demotrace-worker
echo "Worker now runs $digest"
