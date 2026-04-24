#!/bin/bash

# Script de Inicialização do Docker Swarm
# Uso: ./swarm-init.sh <IP_DO_MASTER>

set -e

MASTER_IP=${1:-$(hostname -I | awk '{print $1}')}

if [ -z "$MASTER_IP" ]; then
    echo "Erro: IP do master não fornecido"
    echo "Uso: $0 <IP_DO_MASTER>"
    exit 1
fi

echo "=========================================="
echo "Inicializando Docker Swarm"
echo "IP Master: $MASTER_IP"
echo "=========================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker não encontrado. Instalando..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
fi

# Verificar se Swarm já foi inicializado
if docker info | grep -q "Swarm: active"; then
    echo "✓ Docker Swarm já está ativo"
else
    echo "Inicializando Swarm no nó master..."
    docker swarm init --advertise-addr "$MASTER_IP"
    echo "✓ Swarm inicializado com sucesso"
fi

# Obter token de join para workers
WORKER_TOKEN=$(docker swarm join-token -q worker)
MANAGER_TOKEN=$(docker swarm join-token -q manager)

echo ""
echo "=========================================="
echo "Token para Workers (use em outros nós):"
echo "=========================================="
echo "docker swarm join --token $WORKER_TOKEN $MASTER_IP:2377"
echo ""
echo "=========================================="
echo "Token para Managers (use em outros nós):"
echo "=========================================="
echo "docker swarm join --token $MANAGER_TOKEN $MASTER_IP:2377"
echo ""

# Listar nós atuais
echo "=========================================="
echo "Nós atuais no Swarm:"
echo "=========================================="
docker node ls

echo ""
echo "✓ Inicialização concluída!"
