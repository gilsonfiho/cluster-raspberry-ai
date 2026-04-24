# Infraestrutura - Cluster Docker Swarm

Este diretório contém os arquivos de orquestração e deploy do Docker Swarm para o cluster de Raspberry Pi.

## Estrutura

```
infra/
├── docker-compose.yml              # Compose base para Swarm
├── docker-compose.override.yml      # Overrides para desenvolvimento
├── swarm-init.sh                   # Script de inicialização do Swarm
└── stack-deploy.sh                 # Script de deploy da stack
```

## Arquivos Principais

### `docker-compose.yml`

Define todos os serviços da stack em produção:
- **Ollama**: Serviço de LLM
- **N8N**: Orquestrador de workflows
- **Volumes**: Persistência de dados
- **Redes**: Overlay network para comunicação entre containers

**Uso**:
```bash
cd infra/
docker stack deploy -c docker-compose.yml llm-cluster
```

### `docker-compose.override.yml`

Configurações para desenvolvimento/testes local:
- Remove constraints de placement
- Adiciona logging mais detalhado
- Parâmetros menos restritivos

**Uso**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

### `swarm-init.sh`

Inicializa o Docker Swarm no nó master e fornece tokens para workers.

**Uso**:
```bash
chmod +x swarm-init.sh
./swarm-init.sh <IP_DO_MASTER>
```

**Resultado**:
- Swarm inicializado
- Tokens de join exibidos
- Nós listados

### `stack-deploy.sh`

Valida e faz deploy da stack com opções avançadas.

**Uso**:
```bash
chmod +x stack-deploy.sh

# Deploy normal
./stack-deploy.sh

# Apenas validar
./stack-deploy.sh --validate

# Deploy customizado
./stack-deploy.sh --stack-name custom-cluster --prod
```

## Quick Start

### 1. Inicializar Swarm no Master (Pi 4)

```bash
cd infra/
./swarm-init.sh 192.168.1.10
```

Copiar o token exibido.

### 2. Adicionar Workers (Pi 3)

Em cada Pi 3:
```bash
docker swarm join --token <TOKEN_COPIADO> 192.168.1.10:2377
```

### 3. Deploy da Stack

No master:
```bash
cd infra/
./stack-deploy.sh
```

### 4. Verificar Status

```bash
docker service ls
docker stack ps llm-cluster
```

---

## Serviços Disponíveis

| Serviço | Port | Volume | Placement |
|---------|------|--------|-----------|
| Ollama | 11434 | ollama | rpi-master |
| N8N | 5678 | n8n_data | rpi-master |

---

## Troubleshooting

### Swarm não inicializa

```bash
# Verificar se Docker está rodando
docker ps

# Verificar modo Swarm
docker info | grep Swarm

# Se necessário reiniciar
docker swarm leave --force
docker swarm init --advertise-addr <IP>
```

### Stack não faz deploy

```bash
# Validar compose
docker-compose -f docker-compose.yml config

# Ver erros de deploy
docker service logs llm-cluster_ollama

# Verificar recursos disponíveis
docker node inspect rpi-master
```

### Container keeps restarting

```bash
# Ver logs
docker service logs <service_name> --no-trunc

# Verificar health check
docker service inspect <service_name> | jq '.Endpoint.Status'
```

---

## Configurações Avançadas

### Adicionar Mais Nós

Atualizar `docker-compose.yml`:
```yaml
deploy:
  mode: global  # Replica em todos os nós
  # ou
  replicas: 3   # Spread entre 3 nós
```

### Limites de Recursos

```yaml
resources:
  limits:
    cpus: '2'
    memory: 3500M
  reservations:
    cpus: '1'
    memory: 2048M
```

### Update Policy

```yaml
deploy:
  update_config:
    parallelism: 1
    delay: 10s
```

---

## Monitoramento

Use os scripts em `../scripts/`:

```bash
../scripts/monitor.sh llm-cluster
```

---

> Para mais detalhes sobre Docker Swarm, consultar [docs/arquitetura.md](../docs/arquitetura.md)
