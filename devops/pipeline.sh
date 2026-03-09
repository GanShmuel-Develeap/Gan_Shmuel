#!/bin/bash

# --- 0. Network & Infrastructure Setup ---
NETWORK_NAME="gan_shmuel_shared"

# Check if the network exists to prevent errors
if [ ! "$(docker network ls | grep $NETWORK_NAME)" ]; then
    echo "Creating network: $NETWORK_NAME" 
    docker network create $NETWORK_NAME
else
    echo "Network $NETWORK_NAME already exists. Skipping creation."
fi

# --- 1. Environment & Git Sync ---
BRANCH_NAME=$1  # e.g., "weight" or "billing"
OTHER_SERVICE=$([ "$BRANCH_NAME" == "weight" ] && echo "billing" || echo "weight")

# Move to the project root
cd "$(dirname "$0")"
PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd "$PROJECT_DIR"

echo "📍 Current Branch: $BRANCH_NAME | Other Service: $OTHER_SERVICE"

# Pull the latest code for the entire repo
git fetch origin
git checkout "$BRANCH_NAME"
git pull origin "$BRANCH_NAME"

# --- 2. Unit Testing (Isolated Branch) ---
echo "🧪 PHASE 1: Running Unit Tests for $BRANCH_NAME..."

# Build and start ONLY the service that was pushed
# Using --build ensures the new code from git pull is included
docker compose -f "${PROJECT_DIR}/${BRANCH_NAME}/compose.yaml" up -d --build

# Run the pytest suite inside the container
docker compose -f "${PROJECT_DIR}/${BRANCH_NAME}/compose.yaml" exec -T web pytest > "${BRANCH_NAME}_report.txt"
TEST_A_RESULT=$?

if [ $TEST_A_RESULT -eq 0 ]; then
    TEST_A_STATUS="SUCCESS ✅"
    echo "✅ Unit Tests passed."

    # --- 3. Integration & Environment Sync (Full Setup) ---
    echo "🔗 PHASE 2: Synchronizing both services for Integration..."
    
    # Ensure the OTHER service is up (no --build needed here unless it's missing)
    docker compose -f "${PROJECT_DIR}/${OTHER_SERVICE}/compose.yaml" up -d

    # If you have a root compose.yaml that links them, run it now to ensure parity
    # This ensures the pushed service is updated and integrated
    docker compose -f "${PROJECT_DIR}/compose.yaml" up -d --build

    # Connectivity Check: Can the pushed service ping the other one?
    # We use the service name as the hostname
    echo "🛰 Testing internal connectivity to $OTHER_SERVICE..."
    docker compose -f "${PROJECT_DIR}/${BRANCH_NAME}/compose.yaml" exec -T web curl -s http://${OTHER_SERVICE}:5000/health > /dev/null
    TEST_B_RESULT=$?
    
    TEST_B_STATUS=$([ $TEST_B_RESULT -eq 0 ] && echo "SUCCESS ✅" || echo "FAILED ❌")
else
    TEST_A_STATUS="FAILED ❌"
    TEST_B_STATUS="SKIPPED ⏭ (Unit Test Failed)"
    echo "❌ Unit Tests failed. Integration skipped."
fi

# --- 4. Final Slack Report ---
PUBLIC_IP=$(curl -s ifconfig.me)
MESSAGE="*EC2 CI Deployment Report* \n\n"
MESSAGE+="*Branch*: \`${BRANCH_NAME}\`\n"
MESSAGE+="*1. Unit Test ($BRANCH_NAME)*: $TEST_A_STATUS\n"
MESSAGE+="*2. Integration Check*: $TEST_B_STATUS\n"
MESSAGE+="*3. Browser Access*:\n"
MESSAGE+="   • *Billing*: http://${PUBLIC_IP}:5000\n"
MESSAGE+="   • *Weight*: http://${PUBLIC_IP}:5001"

echo "📤 Sending report to Slack..."
curl -X POST -H 'Content-type: application/json' \
--data "{\"text\":\"$MESSAGE\"}" "$SLACK_WEBHOOK_URL"

echo "🏁 Pipeline Complete."
