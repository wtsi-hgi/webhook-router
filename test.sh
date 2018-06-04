#!/bin/bash
set -euo pipefail

if [ -z "${POSTGRES_PASSWORD+defined}" ]; then
    export POSTGRES_PASSWORD=$(docker run -it frapsoft/openssl rand -base64 15);
fi

echo "-------------------------------"
echo "Starting up docker-compose ..."
echo "-------------------------------"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "-------------------------------"
echo "Testing the configserver ..."
echo "-------------------------------"
docker-compose exec configserver sh -c "cd /config-server && pip install -r test_requirements.txt && pytest test.py"

echo "-------------------------------"
echo "Testing the router ..."
echo "-------------------------------"
docker-compose exec router sh -c "cd /router && npm run-script test"

echo "-------------------------------"
echo "Testing the firewall-config server ..."
echo "-------------------------------"
docker-compose exec firewallconfig sh -c "cd /firewall-config/ && pip install -r test_requirements.txt && pytest test.py"

echo "All tests succeeded!"