# Fluxo de Dados - Cluster Raspberry Pi LLM

## Fluxo 1: Execução de Modelo via Ollama (Direct API Call)

```
┌─────────────────┐
│   Cliente HTTP  │ (laptop, smartphone, etc)
│  http://<IP>    │
└────────┬────────┘
         │
         │ POST http://<IP>:11434/api/generate
         │ {
         │   "model": "qwen:0.6b",
         │   "prompt": "Olá"
         │ }
         │
    ┌────▼──────────────────────────────┐
    │   Docker Swarm Manager            │
    │   (Load Balancer Virtual IP)      │
    └────┬──────────────────────────────┘
         │
         │ Roteamento interno
         │
    ┌────▼──────────────────────────────┐
    │   Container Ollama                │
    │   (Porta 11434)                   │
    │                                   │
    │  1. Carrega modelo de volume      │
    │  2. Processa prompt               │
    │  3. Executa inferência            │
    │  4. Retorna tokens                │
    └────┬──────────────────────────────┘
         │
         │ Response HTTP 200 OK
         │ {
         │   "response": "Olá! Tudo bem?",
         │   "model": "qwen:0.6b",
         │   "created_at": "...",
         │   "done": true
         │ }
         │
    ┌────▼─────────┐
    │   Cliente    │
    │   Recebe     │
    │   Resposta   │
    └──────────────┘
```

### Latência Esperada
- Primeira chamada (load model): 5-15s
- Chamadas subsequentes: 2-8s (por inferência de 100 tokens)

---

## Fluxo 2: Automação via N8N + Ollama

```
┌──────────────────┐
│   Usuário N8N    │
│  http://<IP>:5678│
└────────┬─────────┘
         │
         │ Acesso Web UI
         │
    ┌────▼──────────────────────┐
    │   N8N Container          │
    │   (Porta 5678)           │
    │                          │
    │   - Node.js Runtime      │
    │   - Workflow Engine      │
    │   - WebSocket Support    │
    └────┬─────────────────────┘
         │
         │ Workflow criado:
         │ Trigger → HTTP Request → Ollama → Processamento → Save
         │
    ┌────▼──────────────────────┐
    │   HTTP Request Node       │
    │                          │
    │   Method: POST           │
    │   URL: http://ollama:11434
    │   /api/generate          │
    │                          │
    │   Body: {                │
    │     model: "qwen:0.6b",  │
    │     prompt: "..."        │
    │   }                      │
    └────┬──────────────────────┘
         │ (Via rede overlay Docker)
         │
    ┌────▼──────────────────────┐
    │   Container Ollama       │
    │   (Porta 11434)          │
    │   (Rede interna)         │
    │                          │
    │   Processa → Retorna     │
    └────┬──────────────────────┘
         │
         │ Response JSON
         │
    ┌────▼──────────────────────┐
    │   N8N Processing Node    │
    │                          │
    │   - Extrai campos        │
    │   - Transforma dados     │
    │   - Salva resultado      │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │   Saída                  │
    │   - Database             │
    │   - Email                │
    │   - Webhook              │
    │   - Arquivo              │
    └──────────────────────────┘
```

### Endpoints de N8N para Ollama
```
# Listar modelos disponíveis
GET http://ollama:11434/api/tags

# Executar inferência
POST http://ollama:11434/api/generate
Body: {
  "model": "qwen:0.6b",
  "prompt": "seu prompt aqui",
  "stream": false
}

# Embeddings (se necessário)
POST http://ollama:11434/api/embeddings
Body: {
  "model": "nomic-embed-text",
  "prompt": "seu texto aqui"
}
```

---

## Fluxo 3: Benchmark e Coleta de Métricas

```
┌──────────────────────────┐
│   User (CLI)             │
│   ./benchmark-run.sh     │
└────────┬─────────────────┘
         │
    ┌────▼──────────────────────────────┐
    │   Ambiente Python (venv)          │
    │   benchmarks/main.py              │
    │                                   │
    │   1. Carrega config.yaml          │
    │   2. Inicializa monitores         │
    └────┬──────────────────────────────┘
         │
         │ loop para cada modelo
         │
    ┌────▼──────────────────────────────┐
    │   Detecção de Modelos            │
    │   GET http://localhost:11434/api/tags
    │                                   │
    │   Response:                       │
    │   {                               │
    │     "models": [                   │
    │       {"name": "qwen:0.6b", ...}, │
    │       {"name": "qwen:1.7b", ...}  │
    │     ]                             │
    │   }                               │
    └────┬──────────────────────────────┘
         │
    ┌────▼──────────────────────────────┐
    │   Threads de Monitoramento       │
    │                                   │
    │   - CPU Monitor (benchmarks/     │
    │     cpu_mem_monitor.py)          │
    │                                   │
    │   - RAM Monitor (Coleta a cada   │
    │     intervalo configurado)       │
    │                                   │
    │   - Execução do Prompt           │
    │     (performance_test.py)        │
    └────┬──────────────────────────────┘
         │ Coleta paralela:
         │ - ps aux (CPU)
         │ - /proc/meminfo (RAM)
         │ - time (Latência)
         │
    ┌────▼──────────────────────────────┐
    │   POST Ollama                    │
    │   /api/generate                  │
    │                                   │
    │   Parametros:                     │
    │   - model: nome do modelo        │
    │   - prompt: from config.yaml     │
    │   - stream: false                │
    │                                   │
    │   Métricas coletadas:            │
    │   - Tempo total (ms)             │
    │   - Pico de CPU (%)              │
    │   - Pico de RAM (MB)             │
    │   - Consumo médio de RAM         │
    └────┬──────────────────────────────┘
         │
    ┌────▼──────────────────────────────┐
    │   Agregação de Resultados       │
    │                                   │
    │   Dados estruturados:            │
    │   - Timestamp                    │
    │   - Modelo                       │
    │   - Prompt usado                 │
    │   - Resposta (tokens)            │
    │   - Métricas de performance      │
    └────┬──────────────────────────────┘
         │
    ┌────▼──────────────────────────────┐
    │   Relatório de Saída             │
    │   benchmarks/reports/            │
    │   benchmark_report_YYYYMMDD_     │
    │   HHMMSS.txt                     │
    │                                   │
    │   Formato:                        │
    │   ========================        │
    │   Modelo: qwen:0.6b             │
    │   Data: 2025-06-20 15:27:15    │
    │   ========================        │
    │   Tempo Total: 3500ms           │
    │   CPU Peak: 87%                 │
    │   RAM Peak: 850MB               │
    │   ...                           │
    └──────────────────────────────────┘
```

### Componentes de Benchmark

#### 1. `main.py`
- Orquestra execução
- Carrega `config.yaml`
- Itera sobre modelos
- Gera relatório final

#### 2. `cpu_mem_monitor.py`
- Thread de monitoramento
- Coleta métricas do sistema (`/proc`, `ps`)
- Intervalo configurável
- Armazena em estrutura de dados

#### 3. `performance_test.py`
- Executa inferência
- Mede tempo de resposta
- Captura output do modelo
- Sincroniza com monitor de recursos

---

## Fluxo 4: Persistência de Dados

```
┌─────────────────────────────┐
│   Container Ollama          │
│   /root/.ollama/            │
│   ├── models/               │
│   │   ├── qwen:0.6b/       │
│   │   │   └── model.gguf   │
│   │   └── qwen:1.7b/       │
│   │       └── model.gguf   │
│   └── manifests/            │
│       └── [metadados]       │
└────────────┬────────────────┘
             │
        ┌────▼─────────────────┐
        │   Volume Docker      │
        │   "ollama"           │
        │                      │
        │   /var/lib/docker/   │
        │   volumes/           │
        │   ollama/_data/      │
        └────┬─────────────────┘
             │
        ┌────▼──────────────────────┐
        │   Filesystem do nó        │
        │   Master (Pi 4)           │
        │                           │
        │   Persistência: SIM       │
        │   Retenção: Permanente    │
        │   Backup: Manual          │
        └────────────────────────────┘
```

---

## Fluxo 5: Logging e Monitoramento

```
Container Ollama                Container N8N
     │                               │
     └─────────────┬─────────────────┘
                   │
            ┌──────▼──────────┐
            │  Docker Logs    │
            │  (json-file)    │
            │                 │
            │  Rotação:       │
            │  - max-size:10m │
            │  - max-file:3   │
            └──────┬──────────┘
                   │
        ┌──────────▼──────────────┐
        │  /var/lib/docker/       │
        │  containers/            │
        │  <container_id>/        │
        │  <container_id>-        │
        │  json.log               │
        └──────────────────────────┘
```

### Verificar Logs
```bash
# Logs do Ollama
docker service logs <stack>_ollama

# Logs do N8N
docker service logs <stack>_n8n

# Logs em tempo real
docker service logs -f <stack>_ollama
```

---

## Resumo de Endpoints

| Serviço | Port | Endpoint | Método | Descrição |
|---------|------|----------|--------|-----------|
| Ollama | 11434 | `/api/tags` | GET | Listar modelos |
| Ollama | 11434 | `/api/generate` | POST | Executar inferência |
| Ollama | 11434 | `/api/embeddings` | POST | Gerar embeddings |
| N8N | 5678 | `/` | GET | Web UI |
| N8N | 5678 | `/api/workflows` | GET | Lista workflows |
| N8N | 5678 | `/webhook/*` | POST | Webhooks custom |

---

> Nota: Todos os fluxos assumem que os containers estão rodando e saudáveis. Use `docker service ls` e `docker stack ps` para verificar o status.
