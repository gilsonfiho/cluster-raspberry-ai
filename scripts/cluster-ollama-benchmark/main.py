import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model


# 🔧 Carregar configuração
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# 🎯 Ler parâmetros do YAML
MEMORY_THRESHOLD = config['memory_threshold_mb']
PROMPT = config['task_prompt']
MONITOR_INTERVAL = config['cpu_sample_interval']
OUTPUT_FOLDER = config['output_folder']

# 📂 Criar pasta de saída
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🚀 Inicializar cliente Ollama
client = ollama.Client()

# 🕑 Gerar timestamp
timestamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(OUTPUT_FOLDER, f"benchmark_report_{timestamp}.txt")

# 🔍 Obter lista de modelos
response = client.list()

# ✅ GARANTIR que é um dicionário com chave 'models'
if 'models' not in response:
    print("❌ ERRO: Resposta inesperada de client.list()")
    print(f"Resposta: {response}")
    exit(1)

all_models = response['models']

# ✅ Verificar se cada modelo é uma lista
if not all(isinstance(m, list) and len(m) >= 2 for m in all_models):
    print("❌ ERRO: Formato inesperado dos modelos")
    print(f"Modelos: {all_models}")
    exit(1)

# ✔️ Mostrar modelos disponíveis
print(f"Modelos disponíveis: {[m[0] for m in all_models]}")

# 🔬 Filtrar modelos pelo limite de memória
filtered_models = [
    m for m in all_models
    if isinstance(m[1], (int, float)) and (m[1] / (1024 * 1024)) <= MEMORY_THRESHOLD
]

print(f"Modelos selecionados: {[m[0] for m in filtered_models]}")

# 📝 Criar relatório
with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write("---------------------------------------------------------------\n")
    report.write("| Modelo            | Tempo(s) | RAM(MB) | CPU(%) | Status    |\n")
    report.write("---------------------------------------------------------------\n")

    for model in filtered_models:
        model_id = model[0]  # Nome do modelo
        print(f"\n🚀 Testando modelo: {model_id}")

        result = run_test_on_model(
            model_id,
            prompt=PROMPT,
            monitor_interval=MONITOR_INTERVAL
        )

        if result.get("success"):
            report.write(
                f"| {model_id:<18} | {result['duration']:<8} | {result['ram_mb']:<7} | {result['cpu_percent']:<6} | Sucesso   |\n"
            )
        else:
            report.write(
                f"| {model_id:<18} |   -     |   -    |   -   | Falha ({result.get('error')[:10]}) |\n"
            )

    report.write("---------------------------------------------------------------\n")

print(f"\n✅ Relatório salvo em {report_path}")
