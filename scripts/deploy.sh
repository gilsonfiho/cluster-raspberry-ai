#!/bin/bash

# Script de Deploy Geral - Orquestra todo o deploy do cluster
# Uso: ./deploy.sh [opcoes]
# Opcoes:
#   --infra-only           Deploy apenas da infraestrutura
#   --skip-validation      Pular validação
#   --stack-name <nome>    Nome customizado da stack
#   --dry-run              Simular sem fazer deploy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$SCRIPT_DIR/../infra"
SKIP_VALIDATION=0
INFRA_ONLY=0
DRY_RUN=0
STACK_NAME="llm-cluster"

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --infra-only)
            INFRA_ONLY=1
            shift
            ;;
        --skip-validation)
            SKIP_VALIDATION=1
            shift
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        *)
            echo "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Deploy Geral - LLM Cluster Raspberry Pi"
echo "=========================================="
echo "Stack: $STACK_NAME"
echo "Infra Only: $([ $INFRA_ONLY -eq 1 ] && echo 'SIM' || echo 'NÃO')"
echo "Dry Run: $([ $DRY_RUN -eq 1 ] && echo 'SIM' || echo 'NÃO')"
echo ""

# Verificar pré-requisitos
echo "Verificando pré-requisitos..."

if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado"
    exit 1
fi

if ! docker info | grep -q "Swarm: active"; then
    echo "Erro: Docker Swarm não está ativo"
    echo "Execute: docker swarm init --advertise-addr <IP>"
    exit 1
fi

if ! docker info | grep -q "Is Manager: true"; then
    echo "Erro: Este nó não é um manager do Swarm"
    exit 1
fi

echo "✓ Pré-requisitos OK"
echo ""

# Validação
if [ $SKIP_VALIDATION -eq 0 ]; then
    echo "Validando configurações..."
    cd "$INFRA_DIR"
    docker-compose -f docker-compose.yml config > /dev/null
    echo "✓ Configurações validadas"
    echo ""
fi

# Deploy
if [ $DRY_RUN -eq 0 ]; then
    echo "Fazendo deploy..."
    cd "$INFRA_DIR"
    docker stack deploy -c docker-compose.yml "$STACK_NAME"
    
    echo ""
    echo "Aguardando convergência..."
    sleep 5
    
    echo ""
    echo "=========================================="
    echo "Status do Deploy:"
    echo "=========================================="
    docker stack ps "$STACK_NAME" --no-trunc
else
    echo "[DRY RUN] Skipando deploy real"
fi

echo ""
echo "=========================================="
echo "Deploy concluído!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Monitorar: $SCRIPT_DIR/monitor.sh $STACK_NAME"
echo "2. Verificar logs: docker service logs ${STACK_NAME}_ollama"
echo "3. Acessar N8N: http://<IP>:5678 (admin/admin123)"
echo "4. Testar Ollama: curl http://localhost:11434/api/tags"
