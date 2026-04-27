#!/bin/bash
FILE=${1:-docker-compose.yml}
docker-compose -f "$FILE" config > /dev/null && docker stack deploy -c "$FILE" llm-cluster
