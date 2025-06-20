import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model


# 🔧 Carregar configuração
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

MEMORY_THRESHOLD = config.get('memory_threshold_mb', 3500)
PROMPT = config.get('task_prompt', "Qual é a capital da França?")
MONITOR_INTERVAL = config.get('cpu_sample_interval', 0.5)
OUTPUT_FOLDER = config.get('output_folder', 'reports')
EXCLUDE_MODELS = config.get('exclude_models', [])

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔍 Inicializar cliente Ollama
client = ollama.Client()

# 📜 Nome do relatório com timestamp
timestamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(OUTPUT_FOLDER, f"benchmark_report_{timestamp}.txt")

# 🚀 Obter lista de modelos
models = client.list()['models']
print(f"Modelos disponíveis: {[m['name'] for m in models]}")

# 🔍 Filtrar modelos por limite de memória
filtered_models = [
    m for m in models
    if m['size'] / (1024 * 1024) <= MEMORY_THRESHOLD and m['name'] not in EXCLUDE_MODELS
]

print(f"Modelos selecionados: {[m['name'] for m in filtered_models]}")

# 📝 Gerar relatório
with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write("---------------------------------------------------------------\n")
    report.write("| Modelo            | Tempo(s) | RAM(MB) | CPU(%) | Status    |\n")
    report.write("---------------------------------------------------------------\n")

    for model in filtered_models:
        name = model['name']
        print(f"\n🚀 Testando modelo: {name}")

        result = run_test_on_model(
            name,
            prompt=PROMPT,
            monitor_interval=MONITOR_INTERVAL
        )

        if result.get("success"):
            report.write(
                f"| {name:<18} | {result['duration']:<8} | {result['ram_mb']:<7} | {result['cpu_percent']:<6} | Sucesso   |\n"
            )
        else:
            report.write(
                f"| {name:<18} |   -     |   -    |   -   | Falha ({result.get('error')[:10]}) |\n"
            )

    report.write("---------------------------------------------------------------\n")

print(f"\n✅ Relatório salvo em {report_path}")
