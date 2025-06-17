import os
import yaml
import pandas as pd
import ollama
from benchmarks.performance_test import check_model_viability, run_benchmark_for_model


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def list_viable_models(memory_threshold_mb):
    models = ollama.list()

    if not models:
        print("❌ Nenhum modelo encontrado. Verifique se o Ollama está rodando e se há modelos instalados.")
        exit(1)

    try:
        models = [m["name"] for m in models]
    except KeyError as e:
        print(f"❌ Erro na estrutura dos dados retornados: {e}")
        print(f"Conteúdo retornado: {models}")
        exit(1)

    viable_models = []
    for model in models:
        info = ollama.show(model)
        size_mb = info.get("size", 0) / (1024 * 1024)
        if size_mb <= memory_threshold_mb:
            viable_models.append(model)
    return viable_models



def main():
    config = load_config()

    output_folder = config["output_folder"]
    os.makedirs(output_folder, exist_ok=True)

    models = list_viable_models(config["memory_threshold_mb"])

    if not models:
        print("🚫 Nenhum modelo viável encontrado no cluster.")
        return

    print(f"🧠 Modelos viáveis encontrados: {models}")

    results = []

    for model in models:
        metrics = run_benchmark_for_model(
            model,
            prompt=config["task_prompt"],
            interval=config["cpu_sample_interval"]
        )
        results.append(metrics)

    df = pd.DataFrame(results)
    print(df)

    df.to_csv(f"{output_folder}/benchmark_results.csv", index=False)
    df.to_markdown(f"{output_folder}/benchmark_report.md")

    print(f"✅ Relatórios salvos em '{output_folder}'")


if __name__ == "__main__":
    main()
