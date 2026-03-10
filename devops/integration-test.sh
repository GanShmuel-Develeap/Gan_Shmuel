#!/bin/bash
set -e

# Get the absolute path of the project root
REPO_ROOT=$(git rev-parse --show-toplevel)

cleanup() {
    echo "🧹 Running automated cleanup..."
    # The -v flag removes the associated volumes!
    docker compose -f compose.integration.yaml down -v --remove-orphans || true
    git checkout devops
    git branch -D ci-integration-run || true
}
trap cleanup EXIT

echo "🚀 Starting Integration Test..."
git checkout devops
git pull origin devops
git fetch origin

# Create branch and merge
git checkout -B ci-integration-run
git merge origin/billing --no-edit
git merge origin/weight --no-edit

# VERIFICATION (Using absolute paths to be safe)
echo "🧐 Verifying the billing compose file is the NEW version..."
if grep -q "billing-app" "$REPO_ROOT/billing/compose.yaml"; then
    echo "✅ Success: Found billing-app names."
else
    echo "⚠️ WARNING: Still seeing the old version in $REPO_ROOT/billing/compose.yaml"
fi

# NETWORK CREATION
echo "🌐 Ensuring gan_shmuel_shared network exists..."
docker network create gan_shmuel_shared 2>/dev/null || true

# RUN ORCHESTRATOR
cd "$REPO_ROOT/devops"
echo "🏗️ Starting Docker Compose..."
docker compose -f compose.integration.yaml up --build -d

echo "✅ Script reached Docker Up!"

# 1. Give the Flask apps a few seconds to finish their internal DB migrations/startup
echo "⏳ Waiting 10 seconds for Flask apps to stabilize..."
sleep 10

# 2. Run the Unit/Integration tests for Billing
echo "🧪 Running Billing Tests..."
docker exec gan-shmuel-integration-billing-app-1 pytest || echo "❌ Billing tests failed"

# 3. Run the Unit/Integration tests for Weight
echo "🧪 Running Weight Tests..."
docker exec -e PYTHONPATH=/app weight-app pytest

echo "🏁 All integration steps completed!"
