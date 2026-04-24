# Arquitetura - Cluster Raspberry Pi LLM

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Swarm Manager                     │
│                  (Raspberry Pi 4 - Master)                  │
│                    192.168.1.x:2377                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Overlay Network: llm-cluster                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Serviço Ollama                              │   │  │
│  │  │  - Porta: 11434 (HTTP)                       │   │  │
│  │  │  - Volume: /root/.ollama                     │   │  │
│  │  │  - Limite: 3.5GB RAM, 2 CPUs                 │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  Serviço N8N                                  │   │  │
│  │  │  - Porta: 5678 (HTTP)                        │   │  │
│  │  │  - Volume: /home/node/.n8n                   │   │  │
│  │  │  - Limite: 1GB RAM, 2 CPUs                   │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Token Join + Rede Overlay
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
    │   Pi 3    │      │   Pi 3    │      │   Pi 3    │
    │  Worker   │      │  Worker   │      │  Worker   │
    │   1GB     │      │   1GB     │      │   1GB     │
    │  RAM      │      │  RAM      │      │  RAM      │
    └───────────┘      └───────────┘      └───────────┘
```

## Componentes de Infra

### Docker Swarm
- **Master**: Raspberry Pi 4 (4GB RAM)
- **Workers**: 3x Raspberry Pi 3 (1GB RAM cada)
- **Rede**: Overlay network `llm-cluster` com VXLAN ID 4096
- **Portabilidade**: Serviços podem ser replicados entre nós

### Serviço Ollama
- **Imagem**: `ollama/ollama:latest`
- **Porta**: 11434 (HTTP API)
- **Volume**: `ollama:/root/.ollama` (persistência de modelos)
- **Placement**: Fixo no `rpi-master` (por ser o mais poderoso)
- **Healthcheck**: Verifica `/api/tags` a cada 30s
- **Recursos**:
  - Limite: 3.5GB RAM, 2 CPUs
  - Reserva: 2GB RAM, 1 CPU

### Serviço N8N
- **Imagem**: `n8nio/n8n:latest`
- **Porta**: 5678 (Web UI)
- **Volume**: `n8n_data:/home/node/.n8n` (persistência de workflows)
- **Placement**: Fixo no `rpi-master`
- **Autenticação**: Basic Auth (admin/admin123)
- **Recursos**:
  - Limite: 1GB RAM, 2 CPUs
  - Reserva: 512MB RAM, 1 CPU

## Fluxo de Dados

### 1. Comunicação Interna (Docker Overlay)
```
N8N (5678) ──HTTP──> Ollama (11434)
         <──HTTP response──
```
- Ambos os serviços rodam na rede overlay `llm-cluster`
- N8N acessa Ollama via `http://ollama:11434` (DNS interno Docker)
- Não requer port mapping externo para comunicação

### 2. Acesso Externo
```
Cliente HTTP
    │
    ├──> N8N Web UI: http://<IP_MASTER>:5678
    │
    └──> Ollama API: http://<IP_MASTER>:11434/api/*
```

### 3. Fluxo de Benchmark
```
Script Python (benchmarks/main.py)
    │
    ├──> Detecta modelos (GET /api/tags)
    │
    ├──> Executa prompt (POST /api/generate)
    │
    ├──> Coleta métricas (CPU, RAM, tempo)
    │
    └──> Gera relatório (reports/*.txt)
```

## Persistência e Volumes

| Volume | Localização | Conteúdo | Retenção |
|--------|-------------|----------|----------|
| `ollama` | `/var/lib/docker/volumes/ollama/_data` | Modelos GGUF baixados | Persistente |
| `n8n_data` | `/var/lib/docker/volumes/n8n_data/_data` | Workflows, credenciais | Persistente |

## Restrições e Limites

### Hardware Constraints
- **Pi 4 Master**: 4GB RAM total
  - Reservado para SO: ~500MB
  - Disponível para containers: ~3.5GB
  - Suporta modelo Qwen 0.6b-1.7b
  
- **Pi 3 Workers**: 1GB RAM cada
  - ZRAM + SWAP necessários
  - Ideal apenas para coleta de dados, não execução de modelos

### Rede
- Latência entre nós: ~1-5ms (local network)
- Banda: Gigabit Ethernet (até 1Gbps teórico)
- DNS interno: Usando resolver do Docker (127.0.0.11:53)

## Topologia de Rede

```
Rede Docker Overlay (llm-cluster)
├── VXLAN Tunnel ID: 4096
├── Driver: overlay
├── Encrypted: Não (performance)
└── Conecta todos os nós Swarm
    ├── Pi 4 Master
    └── Pi 3 Workers (x3)
```

## Estados de Saúde

### Healthcheck - Ollama
```bash
Test: curl -f http://localhost:11434/api/tags
Intervalo: 30 segundos
Timeout: 10 segundos
Retries: 3 falhas antes de marcar como unhealthy
```

### Healthcheck - N8N
```bash
Test: wget --quiet --tries=1 --spider http://localhost:5678
Intervalo: 30 segundos
Timeout: 10 segundos
Retries: 3 falhas antes de marcar como unhealthy
```

## Escalabilidade Futura

### Adição de novos nós
1. Instalar Docker em novo Pi
2. Executar `docker swarm join --token <TOKEN> <IP>:2377`
3. Atualizar constraints em `docker-compose.yml` se necessário

### Novos serviços
1. Criar arquivo `apps/<serviço>/docker-compose.yml`
2. Adicionar definição de serviço em `infra/docker-compose.yml`
3. Executar `docker stack deploy -c infra/docker-compose.yml llm-cluster`

---

> Nota: A arquitetura atual é otimizada para desenvolvimento e estudo. Para produção, considere adicionar:
> - Reverse proxy (Traefik, Nginx)
> - Monitoramento (Prometheus, Grafana)
> - Logging centralizado (ELK, Loki)
> - Backup automático de volumes
