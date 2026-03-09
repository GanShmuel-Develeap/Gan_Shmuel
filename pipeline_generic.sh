#!/bin/bash
# 0. Capture the branch/service name
SERVICE_NAME=$1

# Validation: Ensure a name was provided
if [ -z "$SERVICE_NAME" ]; then
    echo "Usage: $0 <service_name> (e.g., billing or weight)"
    exit 1
fi

cd "$(dirname "$0")"

# 1. Load the specific .env for this service
# We use the variable to find the right folder
export $(grep -v '^#' ../${SERVICE_NAME}/.env | xargs)

PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd $PROJECT_DIR

# 2. Update the code dynamically
git fetch origin
git checkout $SERVICE_NAME
git pull origin $SERVICE_NAME

# 3. Rebuild and Test using the variable for paths
echo "Processing: ${SERVICE_NAME} in ${PROJECT_DIR}"
COMPOSE_FILE="${PROJECT_DIR}/${SERVICE_NAME}/docker-compose.yml"

docker compose -f $COMPOSE_FILE build web
docker compose -f $COMPOSE_FILE up -d

echo "Waiting for ${SERVICE_NAME} service to initialize..."
sleep 5

# Run tests and capture result
docker compose -f $COMPOSE_FILE exec web pytest > test_report.txt
RESULT=$?

# 4. Dynamic Logic for Slack
if [ $RESULT -eq 0 ]; then
    STATUS="${SERVICE_NAME^^}-CI-PASSED ✅" # ^^ makes it uppercase
else
    STATUS="${SERVICE_NAME^^}-CI-FAILED ❌"
fi

# 5. Send Notification
curl -X POST -H 'Content-type: application/json' \
--data "{\"text\":\"*EC2 CI Update*: $STATUS on ${SERVICE_NAME} branch\"}" $SLACK_WEBHOOK_URL
