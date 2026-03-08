#!/bin/bash
PROJECT_DIR="/home/ubuntu/Gan_Shmuel"
cd $PROJECT_DIR

# 1. Update the code
git fetch origin
git checkout billing
git pull origin billing

# 2. Rebuild only what changed
docker-compose -f billing/docker-compose.yml build billing-service

# 3. Run Unit Tests
docker-compose -f billing/docker-compose.yml run --rm billing-service pytest > test_report.txt
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
