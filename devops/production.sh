#!/bin/bash

# 1. Create/Switch to a dedicated production branch
git checkout -B production-live

# 2. Pull the latest infrastructure and app code
git fetch origin
git merge origin/devops --no-edit
git merge origin/billing --no-edit
git merge origin/weight --no-edit

docker network create gan_shmuel_shared_prod || true

# 3. Launch the environment in the background
# The -p flag ensures it's isolated from your testing branch
docker compose -p gan-shmuel-production -f compose.production.yaml up -d --build

echo "Production is live!"