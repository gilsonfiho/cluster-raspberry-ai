import time
import psutil
import ollama
from benchmarks.cpu_mem_monitor import ResourceMonitor

def check_model_viability(model, mem_threshold=600):
    """Verifica se o modelo é carregável no cluster."""
    try:
        mem = psutil.virtual_memory()
        if mem.available < mem_threshold * 1024 * 1024:
            print(f"🚫 Memória insuficiente para testar {model}")
            return False

        print(f"🚀 Testando carregamento do modelo {model}...")
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": "Diga apenas: OK"}],
            stream=False,
        )
        if "OK" in response['message']['content']:
            print(f"✅ Modelo {model} respondeu corretamente.")
            return True
        else:
            return False
    except Exception as e:
        print(f"⚠️ Erro ao testar {model}: {e}")
        return False


def run_benchmark_for_model(model, prompt, interval=0.2):
    """Executa benchmark de um modelo."""
    print(f"▶️ Rodando benchmark para {model}")

    monitor = ResourceMonitor(interval)
    monitor.start()

    start_time = time.time()

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )

    end_time = time.time()

    monitor.stop()

    metrics = {
        "model": model,
        "latency_s": round(end_time - start_time, 2),
        "cpu_mean": monitor.cpu_mean,
        "cpu_peak": monitor.cpu_peak,
        "ram_mean_mb": monitor.ram_mean,
        "ram_peak_mb": monitor.ram_peak,
        "output": response["message"]["content"]
    }

    return metrics
