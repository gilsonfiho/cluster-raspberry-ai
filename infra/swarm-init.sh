#!/bin/bash
IP=${1:-$(hostname -I | awk '{print $1}')}
docker swarm init --advertise-addr "$IP" 2>/dev/null || echo "Swarm já ativo"
docker swarm join-token -q worker | sed "s/^/docker swarm join --token /" | sed "s/ / $IP:2377/"
