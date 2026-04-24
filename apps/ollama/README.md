# Serviço Ollama

Configuração isolada do serviço Ollama para execução de modelos LLM.

## Estrutura

```
ollama/
├── docker-compose.yml           # Compose específico para Ollama
├── README.md                    # Este arquivo
└── .env.example                 # Template de variáveis de ambiente (futuro)
```

## O que é Ollama?

Ollama é um framework minimalista para rodar LLMs localmente, oferecendo:
- Suporte a múltiplos formatos de modelo (GGUF, etc)
- API REST simples
- Gerenciamento automático de modelos
- Otimizações de memória

[Ollama.ai](https://ollama.ai)

## Modelos Compatíveis

### Recomendado para Pi 3 (1GB)
- `qwen:0.6b` - Excelente para Pi 3
- `tinyllama:1.1b` - Leve

### Recomendado para Pi 4 (4GB)
- `qwen:1.7b` - Performance balanceada
- `mistral:7b-q4` - Mais capacidade

## Deploy Individual

```bash
# Deploy apenas do Ollama
cd apps/ollama
docker stack deploy -c docker-compose.yml ollama-test

# Verificar
docker service ls
docker service logs ollama-test_ollama
```

## Operação

### Baixar um Modelo

```bash
# Conectar ao container
docker exec -it <container_id> bash

# Dentro do container
ollama pull qwen:0.6b
ollama list
```

### API Endpoints

#### Listar Modelos
```bash
curl http://localhost:11434/api/tags
```

Response:
```json
{
  "models": [
    {
      "name": "qwen:0.6b",
      "modified_at": "2025-06-20T15:30:00.000000000Z",
      "size": 534887296
    }
  ]
}
```

#### Executar Inferência
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen:0.6b",
    "prompt": "Olá, como está?",
    "stream": false
  }'
```

Response:
```json
{
  "model": "qwen:0.6b",
  "created_at": "2025-06-20T15:30:00Z",
  "response": "Olá! Estou bem, obrigado por perguntar. Como posso ajudá-lo?",
  "done": true,
  "context": [...],
  "total_duration": 3500000000,
  "load_duration": 1000000000,
  "prompt_eval_count": 12,
  "eval_count": 25,
  "eval_duration": 2500000000
}
```

### Health Check

```bash
# Verificar saúde do serviço
curl -f http://localhost:11434/api/tags

# Status dentro do Swarm
docker service inspect ollama-test_ollama
```

## Configuração

### Recursos (no docker-compose.yml)

```yaml
resources:
  limits:
    cpus: '2'        # Max 2 CPUs
    memory: 3500M    # Max 3.5GB RAM
  reservations:
    cpus: '1'        # Reserved 1 CPU
    memory: 2048M    # Reserved 2GB RAM
```

Ajustar conforme necessidade.

### Volume de Modelos

```yaml
volumes:
  - ollama:/root/.ollama
```

Os modelos são armazenados em:
```
/var/lib/docker/volumes/ollama/_data/
```

### Logging

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"      # Máximo 10MB por log
    max-file: "3"        # Manter 3 arquivos
```

## Troubleshooting

### Container não inicia

```bash
# Ver erro
docker service logs <service_name> --no-trunc | tail -50

# Verificar se porta 11434 está disponível
netstat -tlnp | grep 11434
```

### Modelo carrega muito lentamente

```bash
# Verificar espaço em disco
df -h /var/lib/docker/

# Limpar dados antigos
docker volume prune
```

### Falta de memória

```bash
# Verificar uso
docker stats <container_id>

# Se necessário, aumentar ZRAM/SWAP no nó
cat /proc/swaps
```

## Integração com N8N

No N8N, adicionar um nó HTTP:

```json
{
  "method": "POST",
  "url": "http://ollama:11434/api/generate",
  "body": {
    "model": "qwen:0.6b",
    "prompt": "{{ $node.previous.json.user_input }}",
    "stream": false
  }
}
```

A URL `http://ollama:11434` funciona porque ambos os containers estão na rede overlay `llm-cluster`.

---

## Performance Tipicas

### Qwen 0.6b em Pi 3 (1GB)
- Tempo de load: 3-5s
- Tempo de inferência (100 tokens): 40-50s
- Uso de RAM: ~900MB (pico)

### Qwen 1.7b em Pi 4 (4GB)
- Tempo de load: 5-8s
- Tempo de inferência (100 tokens): 15-20s
- Uso de RAM: ~3200MB (pico)

---

## Referências

- [Ollama Official Docs](https://github.com/ollama/ollama)
- [GGUF Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [Model Library](https://ollama.ai/library)

---

> Nota: Para desenvolvimento, use `docker-compose up` em vez de `docker stack deploy`
