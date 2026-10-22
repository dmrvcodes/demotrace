#!/usr/bin/env bash
set -euo pipefail

: "${AWS_PROFILE:?Set AWS_PROFILE to the DemoTrace AWS profile}"
: "${ANTHROPIC_API_KEY:?Export ANTHROPIC_API_KEY before deployment}"
: "${ANTHROPIC_MODEL:?Export ANTHROPIC_MODEL before deployment}"

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

terraform -chdir=infra init
terraform -chdir=infra apply -auto-approve
secret_arn="$(terraform -chdir=infra output -raw anthropic_secret_arn)"
secret_payload="$(python3 -c 'import json, os; print(json.dumps({"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]}))')"
aws secretsmanager put-secret-value --secret-id "$secret_arn" --secret-string "$secret_payload" >/dev/null
echo "Provisioned the DemoTrace data plane with direct model $ANTHROPIC_MODEL"
