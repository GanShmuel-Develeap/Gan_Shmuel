#!/bin/bash

echo "🚀 Starting Integration Tests..."

# 1. Check if Billing Service is up
echo "🔍 Checking Billing Service..."
curl --retry 10 --retry-delay 5 --retry-connrefused http://billing-service:5000/health || exit 1

# 2. Check if Weight Service is up
echo "🔍 Checking Weight Service..."
curl --retry 10 --retry-delay 5 --retry-connrefused http://weight-service:5001/health || exit 1

echo "✅ All services are responsive. Integration successful!"
exit 0
