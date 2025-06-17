import os
import yaml
import pandas as pd
import ollama
from benchmarks.performance_test import check_model_viability, run_benchmark_for_model


def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def list_viable_models(mem_threshold):
    """Lista os modelos que estão instalados e podem ser testados."""
    models = ollama.list()["models"]
    models = [m["name"] for m in models]
    viable = []

    print(f"🔍 Verificando modelos instalados: {models}")

    for model in models:
        if check_model_viability(model, mem_threshold):
            viable.append(model)
        else:
            print(f"⚠️ Modelo {model} removido do benchmark por falta de recursos.")

    return viable


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
