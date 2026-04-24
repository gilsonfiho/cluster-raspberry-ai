# Scripts - Automação do Cluster

Conjunto de scripts shell para automação de deploy, monitoramento e operações do cluster.

## Estrutura

```
scripts/
├── deploy.sh                # Script principal de deploy
├── monitor.sh              # Monitoramento contínuo
├── benchmark-run.sh        # Execução de benchmarks
└── README.md              # Este arquivo
```

## Scripts Disponíveis

### `deploy.sh` - Deploy Geral

Orquestra o deploy completo do cluster.

**Uso:**
```bash
chmod +x deploy.sh
./deploy.sh [opcoes]
```

**Opções:**
```
--infra-only          Deploy apenas infraestrutura (sem serviços)
--skip-validation     Pular validação de arquivos
--stack-name <nome>   Nome customizado da stack (padrão: llm-cluster)
--dry-run            Simular sem fazer deploy real
```

**Exemplos:**
```bash
# Deploy normal
./deploy.sh

# Deploy em modo dry-run (apenas validação)
./deploy.sh --dry-run

# Deploy com nome customizado
./deploy.sh --stack-name meu-cluster
```

**O que faz:**
1. Valida pré-requisitos (Docker, Swarm)
2. Valida arquivos docker-compose
3. Faz deploy da stack
4. Aguarda convergência (5s)
5. Mostra status dos serviços

---

### `monitor.sh` - Monitoramento

Monitora status do cluster em tempo real.

**Uso:**
```bash
chmod +x monitor.sh
./monitor.sh [stack_name] [intervalo]
```

**Argumentos:**
- `stack_name`: Nome da stack (padrão: llm-cluster)
- `intervalo`: Segundos entre atualizações (padrão: 5)

**Exemplos:**
```bash
# Monitorar com intervalo padrão
./monitor.sh

# Monitorar stack específica
./monitor.sh meu-cluster

# Monitorar com intervalo de 2s
./monitor.sh llm-cluster 2
```

**Mostra:**
- Nós do cluster
- Serviços ativos
- Status de tarefas
- Volumes
- Redes

Pressione `Ctrl+C` para sair.

---

### `benchmark-run.sh` - Execução de Benchmarks

Executa testes de performance dos modelos LLM.

**Uso:**
```bash
chmod +x benchmark-run.sh
./benchmark-run.sh [opcoes]
```

**Opções:**
```
--models <modelo1,modelo2>    Modelos a testar (separados por vírgula)
--interval <segundos>         Intervalo de coleta de métricas
--prompt <arquivo>            Arquivo contendo prompt customizado
--output <diretório>          Diretório de saída dos relatórios
```

**Exemplos:**
```bash
# Benchmark com configuração padrão (config.yaml)
./benchmark-run.sh

# Testar múltiplos modelos
./benchmark-run.sh --models "qwen:0.6b,qwen:1.7b"

# Usar prompt customizado de arquivo
./benchmark-run.sh --prompt ./custom_prompt.txt

# Output em diretório específico
./benchmark-run.sh --output "./my_results"

# Combinar opções
./benchmark-run.sh --models "qwen:0.6b" --interval 3 --output "/tmp/bench"
```

**O que faz:**
1. Valida pré-requisitos (Python3, main.py)
2. Cria ambiente virtual se necessário
3. Instala dependências de requirements.txt
4. Executa main.py
5. Lista relatórios gerados

---

## Scripts em `infra/` (Infraestrutura)

### `infra/swarm-init.sh` - Inicializar Swarm

Inicializa Docker Swarm e fornece tokens.

```bash
chmod +x infra/swarm-init.sh
./infra/swarm-init.sh <IP_DO_MASTER>
```

Retorna tokens de join para workers.

---

### `infra/stack-deploy.sh` - Deploy da Stack

Deploy com validação avançada.

```bash
chmod +x infra/stack-deploy.sh
./infra/stack-deploy.sh [opcoes]

# Opções:
--stack-name <nome>          Nome da stack
--compose-file <arquivo>     Arquivo compose customizado
--validate                   Apenas validar
--prod                       Modo produção
```

---

## Fluxo Recomendado

### Primeira Vez (Setup Completo)

```bash
# 1. Inicializar Swarm no master
./infra/swarm-init.sh 192.168.1.10

# 2. Adicionar workers (em cada Pi 3)
docker swarm join --token <TOKEN> 192.168.1.10:2377

# 3. Deploy
./deploy.sh

# 4. Verificar status
./monitor.sh
```

### Operação Diária

```bash
# Monitorar em tempo real
./monitor.sh llm-cluster

# Executar benchmarks (ex: diariamente)
./benchmark-run.sh

# Se precisar redeployar
./deploy.sh --dry-run  # Validar primeiro
./deploy.sh            # Deploy real
```

---

## Checklist de Deployment

```bash
# Antes de executar deploy.sh
[ ] Docker instalado e rodando
[ ] Docker Swarm inicializado (docker info | grep Swarm)
[ ] Este nó é manager (docker info | grep "Is Manager: true")
[ ] Arquivo docker-compose.yml presente em infra/
[ ] Permissões de execução dos scripts

# Após deploy
[ ] Todos os serviços estão rodando (docker service ls)
[ ] Health checks passando (docker service ps)
[ ] Logs sem erros (docker service logs)
[ ] Portas acessíveis (curl http://localhost:11434/api/tags)
```

---

## Debugging

### Verificar Logs do Script

```bash
# Executar com debug
bash -x deploy.sh

# Ou redirecionar para arquivo
./deploy.sh 2>&1 | tee deploy.log
```

### Verificar Docker Swarm

```bash
# Status geral
docker info | grep -A 5 Swarm

# Nós
docker node ls

# Serviços
docker service ls

# Status detalhado de uma stack
docker stack ps llm-cluster
```

### Verificar Rede

```bash
# Redes
docker network ls

# Inspecionar rede overlay
docker network inspect llm-cluster

# Testar conectividade entre containers
docker exec <container> ping <outro_container>
```

---

## Tratamento de Erros Comuns

### Erro: "Swarm not active"

```bash
# Solução: Inicializar Swarm
docker swarm init --advertise-addr <IP>
```

### Erro: "Stack failed to deploy"

```bash
# Solução: Validar compose
docker-compose -f infra/docker-compose.yml config

# Ver erro detalhado
docker service logs <stack_name> --tail 50 --no-trunc
```

### Erro: "No such file or directory"

```bash
# Solução: Verificar permissões
ls -la scripts/
chmod +x scripts/*.sh

# Verificar path
pwd
```

---

## Agendamento Automático

### Crontab (Linux)

```bash
# Editar crontab
crontab -e

# Exemplos:
# Deploy diariamente às 2 AM
0 2 * * * cd /home/ubuntu/cluster-raspberry-ai && ./deploy.sh >> deploy.log 2>&1

# Benchmark todo domingo às 3 AM
0 3 * * 0 cd /home/ubuntu/cluster-raspberry-ai && ./scripts/benchmark-run.sh >> benchmark.log 2>&1

# Monitoramento (redirecionado para arquivo)
* * * * * cd /home/ubuntu/cluster-raspberry-ai && ./scripts/monitor.sh >> monitor.log 2>&1
```

### Systemd Timer (Alternative)

```ini
# /etc/systemd/system/cluster-deploy.timer
[Unit]
Description=Deploy Cluster Raspberry AI
After=network-online.target

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Performance Tips

### Otimizar Deploy

```bash
# Validar antes (mais rápido que deploy real)
./infra/stack-deploy.sh --validate

# Usar --dry-run para testar
./deploy.sh --dry-run
```

### Otimizar Monitoramento

```bash
# Aumentar intervalo em períodos de inatividade
./monitor.sh llm-cluster 30  # Check a cada 30s
```

### Executar em Background

```bash
# Monitoramento em background
nohup ./monitor.sh > monitor.log 2>&1 &

# Verificar PID
ps aux | grep monitor.sh

# Matar processo
kill %1
```

---

> Nota: Sempre executar scripts a partir do diretório raiz do projeto ou usar caminhos absolutos.
