#!/bin/bash

# Script para executar Benchmarks de LLMs no Cluster
# Uso: ./benchmark-run.sh [opcoes]
# Opcoes:
#   --models <modelo1,modelo2>  Modelos a testar (separados por vírgula)
#   --interval <segundos>       Intervalo de coleta de métricas
#   --prompt <arquivo>          Arquivo com o prompt personalizado
#   --output <diretório>        Diretório de saída dos relatórios

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_DIR="$SCRIPT_DIR/benchmarks"
MODELS=""
INTERVAL="2"
PROMPT=""
OUTPUT="$BENCHMARK_DIR/reports"

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --models)
            MODELS="$2"
            shift 2
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Benchmark de LLMs - Cluster Raspberry Pi"
echo "=========================================="
echo "Diretório de saída: $OUTPUT"
echo ""

# Criar diretório de saída se não existir
mkdir -p "$OUTPUT"

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "Erro: Python3 não encontrado"
    exit 1
fi

# Verificar se o arquivo main.py existe
if [ ! -f "$BENCHMARK_DIR/main.py" ]; then
    echo "Erro: $BENCHMARK_DIR/main.py não encontrado"
    exit 1
fi

# Instalar dependências se necessário
if [ ! -d "$BENCHMARK_DIR/venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv "$BENCHMARK_DIR/venv"
    source "$BENCHMARK_DIR/venv/bin/activate"
    pip install -q -r "$BENCHMARK_DIR/requirements.txt"
else
    source "$BENCHMARK_DIR/venv/bin/activate"
fi

echo "Iniciando benchmarks..."
echo ""

# Executar o benchmark
python3 "$BENCHMARK_DIR/main.py" \
    --interval "$INTERVAL" \
    --output "$OUTPUT" \
    ${MODELS:+--models "$MODELS"} \
    ${PROMPT:+--prompt "$PROMPT"}

echo ""
echo "=========================================="
echo "Benchmarks concluídos!"
echo "=========================================="
echo "Relatórios salvos em: $OUTPUT"
ls -lah "$OUTPUT" | tail -5
