#!/bin/bash
cd infra/
docker-compose -f docker-compose.yml config > /dev/null
docker stack deploy -c docker-compose.yml llm-cluster
docker stack ps llm-cluster
