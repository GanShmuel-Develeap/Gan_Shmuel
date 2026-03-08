#!/bin/bash
PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd $PROJECT_DIR

# 1. Update the code
git fetch origin
git checkout billing
git pull origin billing

# 2. Rebuild only what changed
echo ${PROJECT_DIR}
docker compose -f ${PROJECT_DIR}/billing/compose.yaml build web

# 3. Run Unit Tests
docker compose -f ${PROJECT_DIR}/billing/compose.yaml up -d
docker compose -f ${PROJECT_DIR}/billing/compose.yaml exec web pytest > test_report.txt
echo "Waiting for web service to initialize..."
sleep 5
RESULT=$?

# 4. Logic for Slack (as we discussed)
if [ $RESULT -eq 0 ]; then
    STATUS="BILLING-CI-PASSED ✅"
else
    STATUS="BILLING-CI-FAILED ❌"
fi

# 5. Send Notification
curl -X POST -H 'Content-type: application/json' \
--data "{\"text\":\"*EC2 CI Update*: $STATUS on Billing Branch\"}" $SLACK_WEBHOOK_URL
