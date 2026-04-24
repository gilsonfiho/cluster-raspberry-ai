#!/bin/bash

# Script de Deploy da Stack LLM Cluster
# Uso: ./stack-deploy.sh [opcoes]
# Opcoes:
#   --stack-name <nome>    Nome da stack (padrão: llm-cluster)
#   --compose-file <arquivo> Arquivo compose customizado
#   --prod                  Deploy em modo produção
#   --validate             Apenas validar, não fazer deploy

set -e

STACK_NAME="llm-cluster"
COMPOSE_FILE="docker-compose.yml"
VALIDATE_ONLY=0
PROD_MODE=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        --validate)
            VALIDATE_ONLY=1
            shift
            ;;
        --prod)
            PROD_MODE=1
            shift
            ;;
        *)
            echo "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Deploy da Stack LLM Cluster"
echo "=========================================="
echo "Stack: $STACK_NAME"
echo "Arquivo: $COMPOSE_FILE"
echo "Modo Produção: $([ $PROD_MODE -eq 1 ] && echo 'SIM' || echo 'NÃO')"
echo ""

# Verificar se está em um nó Swarm
if ! docker info | grep -q "Swarm: active"; then
    echo "Erro: Docker Swarm não está ativo neste nó"
    exit 1
fi

# Verificar se está no nó master
if ! docker info | grep -q "Is Manager: true"; then
    echo "Erro: Este nó não é um manager do Swarm"
    exit 1
fi

# Validar arquivo docker-compose
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Erro: Arquivo $COMPOSE_FILE não encontrado"
    exit 1
fi

echo "Validando arquivo compose..."
docker-compose -f "$COMPOSE_FILE" config > /dev/null
echo "✓ Arquivo é válido"
echo ""

if [ $VALIDATE_ONLY -eq 1 ]; then
    echo "Validação concluída com sucesso"
    exit 0
fi

# Fazer deploy
echo "Fazendo deploy da stack..."
docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"

echo ""
echo "=========================================="
echo "Aguardando convergência dos serviços..."
echo "=========================================="

# Aguardar por alguns segundos
sleep 5

# Listar serviços
echo ""
echo "Serviços ativos:"
docker service ls --filter "label=com.docker.stack.namespace=$STACK_NAME"

echo ""
echo "Status das tarefas:"
docker stack ps "$STACK_NAME" --no-trunc

echo ""
echo "✓ Deploy concluído!"
echo ""
echo "Próximos passos:"
echo "1. Verificar logs: docker service logs ${STACK_NAME}_ollama"
echo "2. Acessar N8N: http://<IP_DO_MASTER>:5678"
echo "3. Testar Ollama: curl http://localhost:11434/api/tags"
