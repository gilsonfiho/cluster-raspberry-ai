import yaml
import ollama
import os
import time
from benchmarks.performance_test import run_test_on_model
import textwrap

# --- Configurações
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
models_list = all_models_response.models

filtered_models = [
    m for m in models_list if (m.size / (1024 * 1024)) <= MEMORY_THRESHOLD
]

# --- Cabeçalho da tabela
header = f"{'Modelo':<20} | {'Tempo(s)':<8} | {'RAM(MB)':<7} | {'CPU(%)':<6} | {'Status':<10} | Resposta resumida"
separator = "-" * 110

with open(report_path, 'w') as report:
    report.write(f"=== Benchmark Report ===\n")
    report.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.write(f"Prompt utilizado: \"{PROMPT}\"\n\n")
    report.write(separator + "\n")
    report.write(header + "\n")
    report.write(separator + "\n")

    for model in filtered_models:
        model_id = model.model
        print(f"\n🚀 Testando modelo: {model_id}")

        result = run_test_on_model(
            model_id,
            prompt=PROMPT,
            monitor_interval=MONITOR_INTERVAL
        )

        status = "Sucesso" if result.get("success") else f"Falha ({result.get('error')[:10]})"
        duration = f"{result.get('duration', '-'):.2f}" if result.get("duration") else "-"
        ram = f"{result.get('ram_mb', '-'):.1f}" if result.get("ram_mb") else "-"
        cpu = f"{result.get('cpu_percent', '-'):.1f}" if result.get("cpu_percent") else "-"
        response = result.get("response", "").replace('\n', ' ')  # resposta sem quebras de linha
        response_summary = (response[:60] + "...") if len(response) > 60 else response

        # Linha da tabela
        report.write(f"{model_id:<20} | {duration:<8} | {ram:<7} | {cpu:<6} | {status:<10} | {response_summary}\n")

    report.write(separator + "\n\n")

    # --- Detalhes completos das respostas
    for model in filtered_models:
        model_id = model.model
        print(f"Adicionando resposta detalhada para: {model_id}")
        result = run_test_on_model(
            model_id,
            prompt=PROMPT,
            monitor_interval=MONITOR_INTERVAL
        )
        response = result.get("response", "")
        status = "Sucesso" if result.get("success") else f"Falha ({result.get('error')[:10]})"

        report.write(f"=== Modelo: {model_id} ===\n")
        report.write(f"Status: {status}\n")
        report.write(f"Tempo(s): {result.get('duration', '-')}\n")
        report.write(f"RAM(MB): {result.get('ram_mb', '-')}\n")
        report.write(f"CPU(%): {result.get('cpu_percent', '-')}\n\n")
        report.write("Resposta completa:\n")
        report.write(textwrap.fill(response, width=100) + "\n")
        report.write("\n" + "="*80 + "\n\n")

print(f"\n✅ Relatório detalhado salvo em {report_path}")
