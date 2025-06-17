import threading
import time
import psutil

class ResourceMonitor(threading.Thread):
    def __init__(self, interval=0.2):
        super().__init__()
        self.interval = interval
        self.running = False
        self.cpu_usage = []
        self.ram_usage = []

    def run(self):
        self.running = True
        while self.running:
            self.cpu_usage.append(psutil.cpu_percent())
            self.ram_usage.append(psutil.virtual_memory().used / (1024 * 1024))  # MB
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.join()

    @property
    def cpu_mean(self):
        return round(sum(self.cpu_usage) / len(self.cpu_usage), 2) if self.cpu_usage else 0

    @property
    def cpu_peak(self):
        return max(self.cpu_usage) if self.cpu_usage else 0

    @property
    def ram_mean(self):
        return round(sum(self.ram_usage) / len(self.ram_usage), 2) if self.ram_usage else 0

    @property
    def ram_peak(self):
        return round(max(self.ram_usage), 2) if self.ram_usage else 0
