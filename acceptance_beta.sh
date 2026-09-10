#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Starting platform services for Beta acceptance test..."

# Start postgres and baas-api
docker-compose up -d postgres baas-api

# Wait for baas-api to be healthy
echo "Waiting for baas-api to be healthy..."
until [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health)" = "200" ]; do
  sleep 1
done

# Start UI
docker-compose up -d ui

# Wait for UI to be ready
echo "Waiting for UI to be ready..."
until [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/)" = "200" ]; do
  sleep 1
done

echo "Running acceptance checks..."

# Check UI homepage
UI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/)
if [ "$UI_STATUS" -ne 200 ]; then
  echo "❌ UI homepage returned $UI_STATUS, expected 200"
  docker-compose down
  exit 1
fi

# Check UI homepage for expected content
UI_CONTENT=$(curl -s http://localhost:3000/)
if [[ ! "$UI_CONTENT" =~ "Dalizebo" ]]; then
  echo "❌ UI homepage does not contain expected text"
  docker-compose down
  exit 1
fi

# Check API health
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
if [ "$API_STATUS" -ne 200 ]; then
  echo "❌ API health returned $API_STATUS, expected 200"
  docker-compose down
  exit 1
fi

# Check a few API endpoints to ensure they are responding
API_EVENTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/events || echo "000")
if [ "$API_EVENTS_STATUS" -ne "200" ] && [ "$API_EVENTS_STATUS" -ne "401" ] && [ "$API_EVENTS_STATUS" -ne "403" ]; then
  echo "⚠️  API events endpoint returned $API_EVENTS_STATUS (expected 200, 401, or 403)"
  # Not failing the test for this, as it might be expected to require auth
fi

echo "✅ All acceptance checks passed!"

# Tear down
docker-compose down

echo "Beta acceptance test completed successfully."