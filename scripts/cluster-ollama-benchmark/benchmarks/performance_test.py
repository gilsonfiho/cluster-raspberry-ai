import time
import ollama
from .cpu_mem_monitor import ResourceMonitor


def run_test_on_model(model_name, prompt, monitor_interval=0.5):
    client = ollama.Client()

    monitor = ResourceMonitor(interval=monitor_interval)
    monitor.start()

    start = time.time()
    try:
        response = client.generate(
            model=model_name,
            prompt=prompt,
            stream=False
        )
        end = time.time()

        monitor.stop()

        ram_usage, cpu_usage = monitor.get_usage()
        duration = round(end - start, 2)

        # Corrigido aqui:
        result_text = str(response.text).strip() if hasattr(response, "text") else ""

        return {
            "success": True,
            "duration": duration,
            "ram_mb": ram_usage,
            "cpu_percent": cpu_usage,
            "response": result_text,  # chave correta para seu main.py
        }

    except Exception as e:
        monitor.stop()
        return {
            "success": False,
            "error": str(e)
        }
