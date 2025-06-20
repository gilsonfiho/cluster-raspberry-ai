import psutil
import threading
import time


class ResourceMonitor:
    def __init__(self, interval=0.5):
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = None
        self.max_mem = 0
        self.max_cpu = 0

    def _monitor(self):
        while not self._stop_event.is_set():
            mem = psutil.virtual_memory().used / (1024 * 1024)  # MB
            cpu = psutil.cpu_percent(interval=None)

            self.max_mem = max(self.max_mem, mem)
            self.max_cpu = max(self.max_cpu, cpu)

            time.sleep(self.interval)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def get_usage(self):
        return round(self.max_mem, 2), round(self.max_cpu, 2)
