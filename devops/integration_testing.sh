#!/bin/bash

# 1. Create/Switch to a dedicated production branch
git checkout -B production-live

# 2. Pull the latest infrastructure and app code
git fetch origin
git merge origin/devops --no-edit
git merge origin/billing --no-edit
git merge origin/weight --no-edit

docker network create gan_shmuel_shared_test

# 3. Launch the environment in the background
# The -p flag ensures it's isolated from your testing branch
docker compose --env-file .env.test -p gan-shmuel-test -f compose.integration.yaml up -d --build

echo "Integration environment is live!"

