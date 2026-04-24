# Otimizações - Cluster Raspberry Pi LLM

## Contexto

Os Raspberry Pi 3 possuem apenas 1GB de RAM, enquanto o Pi 4 possui 4GB. Para executar modelos LLM em hardware tão limitado, é necessário aplicar várias otimizações de memória, CPU e I/O.

---

## 1. ZRAM - Compressão de RAM em Tempo Real

### O que é ZRAM?

ZRAM cria um bloco de dispositivo comprimido em RAM, aumentando a memória disponível através de compressão transparente.

**Benefício**: Aumenta memória útil em até 2-3x em modelos com boa compressibilidade.

### Instalação no Pi 3

```bash
# SSH no Pi 3
ssh ubuntu@<IP_PI3>

# Instalar zram-config
sudo apt-get update
sudo apt-get install -y zram-config

# Iniciar o serviço
sudo systemctl start zram-config
sudo systemctl enable zram-config

# Verificar status
cat /proc/swaps
swapon -s
```

### Configuração Padrão

O arquivo `/etc/default/zram-config` define:

```bash
# Porcentagem de RAM total para ZRAM
ZRAM_PERCENTAGE=50  # Use 50% do total

# Algoritmo de compressão
COMPRESSION=lz4     # Mais rápido que zstd em Pi 3
```

### Monitoramento de ZRAM

```bash
# Ver compressão atual
zramctl

# Estatísticas detalhadas
cat /proc/sysinfo | grep -i zram
```

---

## 2. SWAP - Página de Memória em Disco

### Quando Usar?

SWAP é mais lento que ZRAM (acesso a disco), mas fornece fallback se ZRAM ficar cheio.

### Configuração em Pi 3

```bash
# Criar arquivo swap (recomendado em vez de partição em Pi)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Fazer persistente no /etc/fstab
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab

# Verificar
free -h
swapon -s
```

### Tuning de SWAP

```bash
# Reduzir swappiness (prefere manter dados em RAM)
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Ver valor atual
cat /proc/sys/vm/swappiness
```

**Recomendação**: `vm.swappiness=10` para reduzir I/O de disco.

---

## 3. Limites de Memória em Docker

### Configuração por Container

Todos os `docker-compose.yml` devem incluir limites:

```yaml
services:
  ollama:
    deploy:
      resources:
        limits:
          cpus: '2'        # Máximo 2 CPUs
          memory: 3500M    # Máximo 3.5GB
        reservations:
          cpus: '1'        # Garantido 1 CPU
          memory: 2048M    # Garantido 2GB
```

### Verificar Uso Real

```bash
# Em tempo real
docker stats <container_id>

# Média de uso (últimas 24h)
docker stats --no-stream
```

---

## 4. Otimizações de CPU

### Governador de Frequência

O Pi 3 suporta scaling de frequência para economizar energia:

```bash
# Ver governador atual
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Ver frequências disponíveis
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies

# Configurar para performance (máxima frequência)
echo "performance" | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Fazer persistente via config.txt
sudo nano /boot/firmware/config.txt
# Adicionar:
# over_voltage=0    # 0 = padrão
# arm_freq=1000     # 1GHz no Pi 3
# core_freq=400
```

### Affinity de CPU (Pinning)

Forçar container a usar CPUs específicas:

```yaml
services:
  ollama:
    deploy:
      placement:
        constraints:
          - node.hostname == rpi-master
```

---

## 5. Otimizações de I/O

### Cache de Página do Kernel

```bash
# Ver cache (buffers)
free -h

# Limpar cache (cuidado!)
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Reler modelos em cache
cat /root/.ollama/models/* > /dev/null
```

### Otimização de Filesystem

Para O Pi 3, usar ext4 com otimizações:

```bash
# Em /etc/fstab, usar opções de performance
/dev/sda1 / ext4 defaults,noatime,nodiratime 0 1
```

**Recomendações**:
- `noatime`: Não atualizar access time (reduz I/O)
- `nodiratime`: Não atualizar atime de diretórios

---

## 6. Otimizações de Modelos

### Quantização

Todos os modelos deve estar em formato GGUF quantizado:

```bash
# Verificar quantização do modelo baixado
ollama show qwen:0.6b | grep -i quant

# Usar apenas modelos quantizados (Q4_0, Q5_0, etc.)
ollama pull qwen:0.6b  # Já é quantizado
```

**Recomendação para Pi 3**: Usar quantização Q3_K ou menor.

### Prompt Caching

No N8N, cachear respostas frequentes:

```json
{
  "model": "qwen:0.6b",
  "prompt": "Responda sobre [topic]",
  "options": {
    "num_ctx": 512,      // Contexto menor
    "temperature": 0.5   // Menos "criativo"
  }
}
```

---

## 7. Monitoramento Contínuo

### Script de Monitoramento Automático

```bash
#!/bin/bash
# monitor-resources.sh

while true; do
  clear
  echo "=== ZRAM Status ==="
  zramctl
  
  echo ""
  echo "=== Memory Info ==="
  free -h
  
  echo ""
  echo "=== Swap Info ==="
  swapon -s
  
  echo ""
  echo "=== CPU Usage ==="
  top -bn1 | head -n 15
  
  sleep 5
done
```

Execute: `watch -n 5 free -h`

---

## 8. Checklist de Otimização

### Para Raspberry Pi 3

- [ ] ZRAM instalado e ativo
- [ ] SWAP configurado (2GB mínimo)
- [ ] `vm.swappiness=10` configurado
- [ ] Governador de frequência em `performance`
- [ ] Filesystem com `noatime, nodiratime`
- [ ] Docker com limites de memória
- [ ] Modelos quantizados (Q3_K ou Q4_0)
- [ ] Health checks configurados
- [ ] Monitoramento contínuo ativo

### Para Raspberry Pi 4

- [ ] Possível usar modelos maiores (Q5_0, Q6_0)
- [ ] ZRAM opcional (já tem 4GB)
- [ ] SWAP recomendado ainda assim (2GB)
- [ ] CPU scaling em `performance`
- [ ] Considerar dissipador térmico ativo

---

## 9. Benchmarks de Performance

### Antes de Otimizar

```
Pi 3 + Qwen 0.6b (Q4_0):
- Tempo de inferência: 45-60s por 100 tokens
- Pico de RAM: 950MB
- CPU: 95-100%
```

### Depois de Otimizar

```
Pi 3 + Qwen 0.6b (Q4_0) + ZRAM + SWAP:
- Tempo de inferência: 35-45s por 100 tokens
- Pico de RAM: 780MB
- CPU: 85-95%
- Melhoria: ~25-30%
```

---

## 10. Troubleshooting

### OOM (Out of Memory)

**Sintoma**: Container para abruptamente

```bash
# Verificar logs
docker service logs <stack>_ollama | tail -20

# Aumentar ZRAM
echo 60 | sudo tee /sys/module/zram/parameters/ZRAM_PERCENTAGE
```

### Lentidão Geral

```bash
# Verificar se há thrashing de página
watch -n 1 'cat /proc/vmstat | grep pswp'

# Se valores aumentam rapidamente: reduzir limite de memória
```

### Travamento do Sistema

```bash
# Habilitar OOM Killer mais agressivo
echo 1 | sudo tee /proc/sys/vm/panic_on_oom

# Após travamento, analisar logs
sudo dmesg | tail -30
```

---

## Recursos Adicionais

- [ZRAM Documentation](https://www.kernel.org/doc/html/latest/admin-guide/blockdev/zram.rst)
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Pi Overclock Guide](https://www.raspberrypi.com/documentation/computers/config_txt.html)
- [GGUF Quantization](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)

---

> Nota: Otimizações são trade-offs. Mais performance = mais calor + mais consumo. Monitorar temperatura regularmente (ideal < 60°C).
