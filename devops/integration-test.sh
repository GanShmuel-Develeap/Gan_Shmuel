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

# ./in CREATION
echo "🌐 Ensuring gan_shmuel_shared network exists..."
docker network create gan_shmuel_shared 2>/dev/null || true

# RUN ORCHESTRATOR
cd "$REPO_ROOT/devops"
echo "🏗️ Starting Docker Compose..."
docker compose -f compose.integration.yaml up --build -d

echo "✅ Script reached Docker Up!"

echo "⏳ Waiting for services to reach healthy state..."
# This waits for the healthcheck service (which depends on the apps) to finish
docker compose -f compose.integration.yaml up healthcheck --exit-code-from healthcheck

if [ $? -ne 0 ]; then
    echo "❌ Services failed to stabilize in time."
    cleanup
    exit 1
fi

# 2. Run the Unit/Integration tests for Billing
echo "🧪 Running Billing Tests..."
docker exec gan-shmuel-integration-billing-app-1 pytest || echo "❌ Billing tests failed"

# 3. Run the Unit/Integration tests for Weight
echo "🧪 Running Weight Tests..."
docker exec -e PYTHONPATH=/app weight-app pytest

echo "🏁 All integration steps completed!"
