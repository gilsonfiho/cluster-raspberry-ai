import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model

# Carregar configuração
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Validar chaves obrigatórias no config
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
MODELS_TO_SIMULATE = set(config.get('models_to_simulate', []))  # Opcional

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

client = ollama.Client()

timestamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(OUTPUT_FOLDER, f"benchmark_report_{timestamp}.txt")

# Obter lista de modelos (lista de tuplas: (id, size, ...))
all_models = client.list()

print(f"Modelos disponíveis: {[m[0] for m in all_models]}")

# Filtra modelos conforme config e tamanho
if MODELS_TO_SIMULATE:
    filtered_models = [
        m for m in all_models
        if m[0] in MODELS_TO_SIMULATE and m[1] / (1024 * 1024) <= MEMORY_THRESHOLD
    ]
else:
    filtered_models = [
        m for m in all_models
        if m[1] / (1024 * 1024) <= MEMORY_THRESHOLD and m[0] not in EXCLUDE_MODELS
    ]

print(f"Modelos selecionados para simulação: {[m[0] for m in filtered_models]}")

with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write("---------------------------------------------------------------\n")
    report.write("| Modelo            | Tempo(s) | RAM(MB) | CPU(%) | Status    |\n")
    report.write("---------------------------------------------------------------\n")

    for model in filtered_models:
        model_id = model[0]
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
