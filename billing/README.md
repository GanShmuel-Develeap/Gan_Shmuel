# Billing Service

## Setup

Some files are not included in the repository and must be created manually.

### 1. Database initialization

Create the file: (in the db/ directory)

```
db/billingdb.sql
```

### 2. Environment variables

Create a `.env` file in the project root.

## Run with Docker

Create a network:

```
docker network create gan_shmuel_shared
```

Start the services:

```
cd billing
docker compose up -d --build
```

Stop the services:

```
docker compose down
```
