# Benchmarks - LLM Performance Testing

Módulo de benchmark automatizado para medir desempenho de modelos LLM no cluster.

## Estrutura

```
benchmarks/
├── docker-compose.yml               # Compose para ambiente de benchmark
├── README.md                        # Este arquivo
├── main.py                          # Script principal de orquestração
├── requirements.txt                 # Dependências Python
├── config.yaml                      # Arquivo de configuração
├── benchmarks/
│   ├── cpu_mem_monitor.py          # Monitora CPU/RAM
│   └── performance_test.py          # Executa testes de inferência
└── reports/
    └── benchmark_report_YYYYMMDD_HHMMSS.txt  # Relatórios gerados
```

## O que é Testado?

- **Tempo de Carregamento**: Quanto tempo demora carregar o modelo
- **Latência de Inferência**: Tempo para gerar resposta
- **Pico de CPU**: Máximo uso de CPU durante teste
- **Pico de RAM**: Máximo uso de memória durante teste
- **Consumo Médio de RAM**: Memória média durante execução

## Configuração

### `config.yaml`

```yaml
# Modelo a testar
model: "qwen:0.6b"

# Prompt para teste
prompt: "Olá, qual é a capital do Brasil?"

# Intervalo de coleta de métricas (segundos)
metric_interval: 2

# Repetições do teste
repetitions: 3

# Timeout por inferência (segundos)
timeout: 120

# Output
output_dir: "./reports"
```

## Uso

### Quick Start

```bash
# Executar benchmark com configuração padrão
./benchmark-run.sh
```

### Com Opções Customizadas

```bash
# Testar modelos específicos
./benchmark-run.sh --models "qwen:0.6b,qwen:1.7b"

# Intervalo de coleta customizado
./benchmark-run.sh --interval 3

# Usar prompt customizado
./benchmark-run.sh --prompt "Explique o significado da vida"

# Output em diretório específico
./benchmark-run.sh --output "/tmp/benchmark_results"
```

### Manual (Python)

```bash
cd benchmarks

# Criar venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar
python3 main.py --config config.yaml
```

## Saída de Relatório

Exemplo de `benchmark_report_20250620_151711.txt`:

```
====================================
LLM Benchmark Report
====================================
Timestamp: 2025-06-20 15:17:11
Host: rpi-master
====================================

Model: qwen:0.6b
Prompt: "Olá, como está?"
Repetitions: 3

--- Execution 1 ---
Load Time: 4.23s
Inference Time: 38.15s
Tokens Generated: 25
Tokens per Second: 0.65

CPU Metrics:
  Peak: 92%
  Average: 87%

Memory Metrics:
  Peak: 847MB
  Average: 812MB

--- Execution 2 ---
Load Time: 0.34s (cached)
Inference Time: 37.89s
Tokens Generated: 25
Tokens per Second: 0.66

CPU Metrics:
  Peak: 91%
  Average: 86%

Memory Metrics:
  Peak: 843MB
  Average: 809MB

====================================
SUMMARY
====================================
Average Inference Time: 38.02s
Average Load Time: 2.29s (first run: 4.23s)
Average Tokens/sec: 0.655
Peak RAM: 847MB
Average RAM: 810MB
Total CPU Time: 258.7s
Efficiency Score: 0.78/10

====================================
Recommendations:
- Model fits well in Pi 3
- Consider enabling ZRAM for better swap
- Temperature stable, cooling adequate
====================================
```

## Componentes Python

### `main.py`

Orquestra o benchmark:
1. Carrega configuração
2. Detecta modelos disponíveis no Ollama
3. Itera sobre cada modelo
4. Chama performance_test.py
5. Coleta resultados
6. Gera relatório

```python
python main.py \
  --models "qwen:0.6b,mistral:7b" \
  --interval 2 \
  --output "./reports"
```

### `benchmarks/cpu_mem_monitor.py`

Thread de monitoramento paralelo:

```python
from benchmarks.cpu_mem_monitor import SystemMonitor

monitor = SystemMonitor(interval=2)  # Coleta a cada 2s
monitor.start()

# ... executar inferência ...

monitor.stop()
metrics = monitor.get_metrics()
print(f"Peak RAM: {metrics['peak_memory_mb']}MB")
```

Coleta:
- `/proc/meminfo` para RAM
- `/proc/stat` para CPU
- `psutil` para dados adicionais

### `benchmarks/performance_test.py`

Executa a inferência:

```python
from benchmarks.performance_test import run_inference

result = run_inference(
    model="qwen:0.6b",
    prompt="Qual é a capital?",
    timeout=120
)

print(f"Time: {result['inference_time_ms']}ms")
print(f"Tokens: {result['tokens_generated']}")
```

Retorna:
- Tempo de inferência
- Tokens gerados
- Output do modelo
- Status de sucesso/erro

## Requisitos

### Hardware Mínimo

- Ollama rodando e acessível em `localhost:11434`
- Python 3.8+
- ~500MB de RAM livre

### Software

```bash
# Instalar dependências
pip install -r requirements.txt
```

Dependências:
- `requests` - HTTP requests para Ollama
- `psutil` - Coleta de métricas de sistema
- `pyyaml` - Parse de config.yaml

## Interpretando Resultados

### Tokens per Second (TPS)

Métrica de throughput:
- **> 1.0 TPS**: Excelente para Pi 3
- **0.5-1.0 TPS**: Bom para Pi 3
- **< 0.5 TPS**: Modelo muito pesado

### Memory Peak vs Average

- **Pico >> Média**: Picos de uso durante carregamento
- **Pico ≈ Média**: Uso constante (modelo grande)

### CPU Efficiency

```
Efficiency = TPS / Avg_CPU_Percent
```

Indica uso eficiente de processamento.

## Automação Diária

### Cron Job

```bash
# Adicionar ao crontab (crontab -e)

# Executar benchmark diariamente às 2 AM
0 2 * * * cd /path/to/benchmarks && ./benchmark-run.sh >> benchmark.log 2>&1

# Arquivo log vai para: /path/to/benchmarks/benchmark.log
```

### Script de Coleta

```bash
#!/bin/bash
# scripts/collect-benchmarks.sh

BENCH_DIR="benchmarks"
REPORT_DIR="$BENCH_DIR/reports"
DATE=$(date +%Y%m%d)

cd "$BENCH_DIR"

# Executar benchmark
python3 main.py

# Fazer backup dos relatórios
tar czf "backup_${DATE}.tar.gz" "$REPORT_DIR"
```

## Comparação Entre Nós

```bash
# No Pi 3
./benchmark-run.sh --output "./pi3_results"

# No Pi 4
./benchmark-run.sh --output "./pi4_results"

# Comparar resultados
diff pi3_results/ pi4_results/
```

## Troubleshooting

### Ollama não está acessível

```bash
# Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# Se erro, iniciar Ollama
docker service ls | grep ollama
```

### Python venv não funciona

```bash
# Recriar venv
python3 -m venv --clear venv
source venv/bin/activate
pip install -r requirements.txt
```

### Testes muito lentos

- Verificar CPU/RAM disponível com `top`
- Reduzir `repetitions` em config.yaml
- Usar modelo menor (qwen:0.6b em vez de 1.7b)

### Erros de Timeout

- Aumentar `timeout` em config.yaml
- Verificar se sistema está sobrecarregado

---

## Extensões Futuras

- [ ] Gráficos de performance over time
- [ ] Comparação automática entre modelos
- [ ] Alertas se performance degradar
- [ ] Integração com banco de dados
- [ ] Dashboard web de resultados

---

> Nota: Benchmarks consomem muitos recursos. Execute em horários fora de pico para não impactar produção.
