#!/bin/bash

# 1. Create/Switch to a dedicated production branch
git checkout -B production-live

# 2. Pull the latest infrastructure and app code
git fetch origin

git merge origin/front-testing --no-edit
# git merge origin/devops --no-edit
# git merge origin/billing --no-edit
# git merge origin/weight --no-edit

# docker network prune -f


docker network create gan_shmuel_shared_prod


# 3. Launch the environment in the background
# The -p flag ensures it's isolated from your testing branch
docker compose -p gan-shmuel-production -f compose.production.yaml up -d --build --remove-orphans

echo "Production is live!"