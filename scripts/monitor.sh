#!/bin/bash

# Script de Monitoramento do Cluster LLM
# Uso: ./monitor.sh [stack_name] [intervalo_segundos]

STACK_NAME=${1:-llm-cluster}
INTERVALO=${2:-5}

echo "=========================================="
echo "Monitorador de Stack: $STACK_NAME"
echo "Intervalo: ${INTERVALO}s (Pressione Ctrl+C para sair)"
echo "=========================================="
echo ""

# Função para mostrar status
show_status() {
    clear
    
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo "NÓS DO CLUSTER"
    echo "=========================================="
    docker node ls
    
    echo ""
    echo "=========================================="
    echo "SERVIÇOS DA STACK: $STACK_NAME"
    echo "=========================================="
    docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    
    echo ""
    echo "=========================================="
    echo "STATUS DE TAREFAS"
    echo "=========================================="
    docker stack ps "$STACK_NAME" --no-trunc
    
    echo ""
    echo "=========================================="
    echo "VOLUMES"
    echo "=========================================="
    docker volume ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    
    echo ""
    echo "=========================================="
    echo "REDES"
    echo "=========================================="
    docker network ls --filter "label=com.docker.stack.namespace=$STACK_NAME"
    
    echo ""
    echo "Atualizando em ${INTERVALO}s... (Ctrl+C para sair)"
}

# Loop de monitoramento
while true; do
    show_status
    sleep "$INTERVALO"
done
