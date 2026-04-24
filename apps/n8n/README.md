# Serviço N8N

Configuração isolada do serviço N8N para orquestração de workflows com integração LLM.

## Estrutura

```
n8n/
├── docker-compose.yml           # Compose específico para N8N
├── README.md                    # Este arquivo
└── .env.example                 # Template de variáveis (futuro)
```

## O que é N8N?

N8N é uma plataforma visual de automação de fluxos que permite:
- Integração com múltiplos serviços
- Criação de workflows sem código (low-code)
- Execução de tarefas automatizadas
- Integração com APIs (como Ollama)

[N8N Official](https://n8n.io)

## Deploy Individual

```bash
# Deploy apenas do N8N
cd apps/n8n
docker stack deploy -c docker-compose.yml n8n-test

# Verificar
docker service ls
docker service logs n8n-test_n8n
```

## Acesso

### Web UI

Abra no navegador:
```
http://<IP_DO_MASTER>:5678
```

Credenciais padrão:
- **Usuário**: `admin`
- **Senha**: `admin123`

**Alterar após primeiro acesso!**

## Workflows com Ollama

### Exemplo 1: Simples Q&A

1. Adicionar **HTTP Request** node
2. Configurar:
   ```
   Method: POST
   URL: http://ollama:11434/api/generate
   Body (JSON):
   {
     "model": "qwen:0.6b",
     "prompt": "{{ $node.trigger.json.question }}",
     "stream": false
   }
   ```
3. Conectar a um nó de resposta (Email, Webhook, etc)

### Exemplo 2: Pipeline de Processamento

```
Webhook Input
    ↓
Extract Text
    ↓
Call Ollama (Summarize)
    ↓
Save to Database
    ↓
Send Email
    ↓
Return Response
```

Cada seta é uma conexão no N8N UI.

## Variáveis de Ambiente

Configuradas em `docker-compose.yml`:

```yaml
environment:
  - N8N_BASIC_AUTH_ACTIVE=true       # Autenticação habilitada
  - N8N_BASIC_AUTH_USER=admin        # Usuário padrão
  - N8N_BASIC_AUTH_PASSWORD=admin123 # Senha padrão (MUDAR!)
  - N8N_HOST=localhost               # Host (ajustar para IP real em produção)
  - N8N_PORT=5678                    # Porta
  - OLLAMA_URL=http://ollama:11434   # URL interna do Ollama
```

## Volume de Dados

```yaml
volumes:
  - n8n_data:/home/node/.n8n
```

Contém:
- Workflows salvos
- Credenciais
- Histórico de execução

Localização:
```
/var/lib/docker/volumes/n8n_data/_data/
```

## Segurança

### Mudar Senha Padrão

1. Acessar Web UI
2. Settings → Users → Edit User
3. Alterar senha

### Usar HTTPS em Produção

```yaml
environment:
  - N8N_PROTOCOL=https
  - N8N_SSL_KEY=/certs/key.pem
  - N8N_SSL_CERT=/certs/cert.pem
```

### Desabilitar Login (não recomendado)

```yaml
environment:
  - N8N_BASIC_AUTH_ACTIVE=false
```

## Operações

### Executar Workflow

1. Abrir workflow
2. Clicar em "Execute Workflow"
3. Monitorar execução em tempo real

### Debug

Clicar no nó e ver:
- Input: Dados recebidos
- Output: Dados enviados
- Execução: Logs e erros

### Export/Import

- **Export**: Workflow → Export
- **Import**: New → Import from File

## Integração com Ollama

### Conectar Ollama

N8N consegue chamar Ollama via:

1. **URL Direta**: `http://ollama:11434` (dentro da rede Docker)
2. **HTTP Generic**: Via nó HTTP Request
3. **Credentials**: Salvar URL como credencial reutilizável

### Exemplo de Node HTTP

```javascript
{
  "method": "POST",
  "url": "{{ $env.OLLAMA_URL }}/api/generate",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "model": "{{ $node.selectModel.json.model }}",
    "prompt": "{{ $node.inputText.json.text }}",
    "stream": false
  }
}
```

## Monitoramento

### Verificar Status

```bash
# Logs
docker service logs n8n-test_n8n

# Estatísticas
docker stats n8n-test_n8n

# Configuração
docker service inspect n8n-test_n8n
```

### Recursos

```yaml
resources:
  limits:
    cpus: '2'
    memory: 1024M
  reservations:
    cpus: '1'
    memory: 512M
```

Ajustar conforme tráfego e workflows.

## Troubleshooting

### Não consegue conectar ao Ollama

```bash
# Verificar se Ollama está rodando
docker service ls | grep ollama

# Testar conectividade (dentro do container N8N)
docker exec <n8n_container_id> curl -f http://ollama:11434/api/tags
```

### Workflow trava ou executa lentamente

1. Verificar uso de memória:
   ```bash
   docker stats n8n_container
   ```

2. Se uso alto, aumentar limite:
   ```yaml
   resources:
     limits:
       memory: 2048M  # Dobrar de 1GB para 2GB
   ```

3. Simplificar workflow (remover nós desnecessários)

### Credenciais não salvam

```bash
# Verificar volume
docker volume inspect n8n_data

# Logs de erro
docker service logs n8n_container --tail=50
```

## Performance Tipica

- **Startup**: 5-10s
- **Workflow simples**: < 1s (sem Ollama)
- **Workflow com Ollama**: 35-50s (tempo de inferência)
- **Memória em repouso**: 200-300MB
- **Memória durante execução**: 500-800MB

## Backup

### Backup de Workflows

```bash
# Dentro de N8N UI
Workflow → Export as JSON
```

### Backup de Volume

```bash
# Fazer backup do volume
docker run --rm -v n8n_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/n8n_backup.tar.gz -C /data .
```

---

## Referências

- [N8N Documentation](https://docs.n8n.io)
- [Nodes Reference](https://docs.n8n.io/integrations/)
- [Workflows Best Practices](https://docs.n8n.io/workflow/)
- [REST API](https://docs.n8n.io/api/)

---

> Nota: Para desenvolvimento local, use `docker-compose up` em vez de `docker stack deploy`
