import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model

# 🔧 Carregar configuração
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Validar configurações obrigatórias
required_keys = [
    'memory_threshold_mb',
    'task_prompt',
    'cpu_sample_interval',
    'output_folder',
    'exclude_models'
]

for key in required_keys:
    if key not in config:
        raise ValueError(f"Chave obrigatória '{key}' faltando no config.yaml")

MEMORY_THRESHOLD = config['memory_threshold_mb']
PROMPT = config['task_prompt']
MONITOR_INTERVAL = config['cpu_sample_interval']
OUTPUT_FOLDER = config['output_folder']
EXCLUDE_MODELS = set(config['exclude_models'])
MODELS_TO_SIMULATE = set(config.get('models_to_simulate', []))  # opcional

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

client = ollama.Client()

timestamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(OUTPUT_FOLDER, f"benchmark_report_{timestamp}.txt")

all_models = client.list()

print(f"Modelos disponíveis: {[m.id for m in all_models]}")

filtered_models = []

if MODELS_TO_SIMULATE:
    for m in all_models:
        if m.id in MODELS_TO_SIMULATE and m.size / (1024 * 1024) <= MEMORY_THRESHOLD:
            filtered_models.append(m)
else:
    filtered_models = [
        m for m in all_models
        if m.size / (1024 * 1024) <= MEMORY_THRESHOLD and m.id not in EXCLUDE_MODELS
    ]

print(f"Modelos selecionados para simulação: {[m.id for m in filtered_models]}")

with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write("---------------------------------------------------------------\n")
    report.write("| Modelo            | Tempo(s) | RAM(MB) | CPU(%) | Status    |\n")
    report.write("---------------------------------------------------------------\n")

    for model in filtered_models:
        name = model.id
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
