import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

MEMORY_THRESHOLD = config['memory_threshold_mb']
PROMPT = config['task_prompt']
MONITOR_INTERVAL = config['cpu_sample_interval']
OUTPUT_FOLDER = config['output_folder']

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
client = ollama.Client()

timestamp = time.strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(OUTPUT_FOLDER, f"benchmark_report_{timestamp}.txt")

all_models_response = client.list()

print(f"Retorno completo de client.list():\n{all_models_response}")
print(f"Chaves disponíveis: {list(all_models_response.keys())}")

models_list = all_models_response.get('models', [])

print(f"Tipo de models_list: {type(models_list)}")
print(f"Quantidade de modelos: {len(models_list)}")
print(f"Primeiro modelo: {models_list[0]}")

print(f"Modelos disponíveis: {[m.model if hasattr(m, 'model') else m[0] for m in models_list]}")

filtered_models = [
    m for m in models_list if (m.size / (1024 * 1024)) <= MEMORY_THRESHOLD
]

print(f"Modelos selecionados: {[m.model for m in filtered_models]}")

with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write("---------------------------------------------------------------\n")
    report.write("| Modelo            | Tempo(s) | RAM(MB) | CPU(%) | Status    |\n")
    report.write("---------------------------------------------------------------\n")

    for model in filtered_models:
        model_id = model.model
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
