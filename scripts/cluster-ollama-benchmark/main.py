import ollama
import time
import yaml


def list_viable_models(memory_threshold_mb):
    response = ollama.list()

    if isinstance(response, dict) and 'models' in response:
        models = response['models']
    else:
        models = response

    if not models:
        print("❌ Nenhum modelo encontrado. Verifique se o Ollama está rodando e se há modelos instalados.")
        exit(1)

    model_names = []
    for m in models:
        name = m.get("name") or m.get("model")
        size = m.get("size", 0) / (1024 * 1024)  # Bytes → MB
        if name and size <= memory_threshold_mb:
            model_names.append(name)

    return model_names


def run_benchmark(model, prompt):
    start_time = time.time()

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        end_time = time.time()

        output = response['message']['content']
        elapsed = end_time - start_time

        return {
            "model": model,
            "output": output,
            "time_seconds": round(elapsed, 2)
        }

    except Exception as e:
        print(f"❌ Erro ao rodar {model}: {e}")
        return {
            "model": model,
            "output": "Erro",
            "time_seconds": None
        }


def main():
    # 🔧 Carregar configurações
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    memory_limit = config.get("memory_threshold_mb", 2500)
    prompt = config.get("prompt", "Qual é a capital da França?")

    print(f"🚀 Benchmark com limite de memória {memory_limit} MB")
    print(f"🧠 Prompt usado: {prompt}")

    # 🔍 Listar modelos possíveis
    models = list_viable_models(memory_limit)
    print(f"✅ Modelos viáveis: {models}")

    if not models:
        print("⚠️ Nenhum modelo disponível dentro do limite de memória.")
        return

    results = []

    for model in models:
        print(f"⏳ Testando {model} ...")
        result = run_benchmark(model, prompt)
        results.append(result)
        print(f"✔️ {model} respondeu em {result['time_seconds']}s")

    # 📜 Gerar relatório
    print("\n📊 Resultado Final:")
    print("-" * 50)
    for r in results:
        print(f"🧠 {r['model']}")
        print(f"⏱️ Tempo: {r['time_seconds']}s")
        print(f"➡️ Resposta: {r['output']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
