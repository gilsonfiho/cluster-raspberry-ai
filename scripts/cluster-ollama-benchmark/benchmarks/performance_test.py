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

        # ✅ Adaptação correta e funcional:
        if isinstance(response, dict):
            result_text = response.get("response", "").strip()
        elif hasattr(response, "response"):
            result_text = str(response.response).strip()
        else:
            result_text = str(response).strip()

        return {
            "success": True,
            "duration": duration,
            "ram_mb": ram_usage,
            "cpu_percent": cpu_usage,
            "response": result_text,
        }

    except Exception as e:
        monitor.stop()
        return {
            "success": False,
            "error": str(e)
        }
