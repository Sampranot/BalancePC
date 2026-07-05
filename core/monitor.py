"""
System Monitor — Monitoraggio risorse in tempo reale
=====================================================
CPU, RAM, disco, GPU, temperatura, processi, rete.
"""

import os
import psutil
import platform
import subprocess
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class SystemSnapshot:
    """Fotografia istantanea dello stato del sistema."""
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    cpu_percent_per_core: List[float] = field(default_factory=list)
    cpu_freq: float = 0.0
    cpu_temp: Optional[float] = None
    ram_total_gb: float = 0.0
    ram_used_gb: float = 0.0
    ram_percent: float = 0.0
    swap_total_gb: float = 0.0
    swap_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    gpu_percent: Optional[float] = None
    gpu_temp: Optional[float] = None
    gpu_mem_percent: Optional[float] = None
    network_sent_mb: float = 0.0
    network_recv_mb: float = 0.0
    process_count: int = 0
    top_processes: List[Dict] = field(default_factory=list)
    uptime_hours: float = 0.0


class SystemMonitor:
    """
    Monitoraggio risorse in tempo reale.
    Raccoglie metriche CPU, RAM, disco, GPU, rete.
    """

    def __init__(self):
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_time = datetime.now()
        self._boot_time = datetime.fromtimestamp(psutil.boot_time())

    def get_stats(self) -> SystemSnapshot:
        """Raccoglie tutte le metriche correnti."""
        now = datetime.now()
        delta = (now - self._last_time).total_seconds() or 0.001

        s = SystemSnapshot()
        s.timestamp = now.timestamp()

        # CPU
        s.cpu_percent = psutil.cpu_percent(interval=0.3)
        s.cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            s.cpu_freq = cpu_freq.current
        s.cpu_temp = self._get_cpu_temp()

        # RAM
        ram = psutil.virtual_memory()
        s.ram_total_gb = round(ram.total / (1024**3), 1)
        s.ram_used_gb = round(ram.used / (1024**3), 1)
        s.ram_percent = ram.percent

        swap = psutil.swap_memory()
        s.swap_total_gb = round(swap.total / (1024**3), 1)
        s.swap_used_gb = round(swap.used / (1024**3), 1)

        # Disco
        try:
            disk = psutil.disk_usage('/')
            s.disk_total_gb = round(disk.total / (1024**3), 1)
            s.disk_used_gb = round(disk.used / (1024**3), 1)
            s.disk_percent = disk.percent
        except:
            pass

        # Disk IO
        try:
            dio = psutil.disk_io_counters()
            if dio:
                s.disk_io_read_mb = round(
                    (dio.read_bytes - self._last_disk_io.read_bytes) / (1024**2) / delta, 2
                )
                s.disk_io_write_mb = round(
                    (dio.write_bytes - self._last_disk_io.write_bytes) / (1024**2) / delta, 2
                )
                self._last_disk_io = dio
        except:
            pass

        # GPU (tentativo con nvidia-smi o wmi)
        gpu_stats = self._get_gpu_stats()
        if gpu_stats:
            s.gpu_percent = gpu_stats.get('gpu_percent')
            s.gpu_temp = gpu_stats.get('gpu_temp')
            s.gpu_mem_percent = gpu_stats.get('mem_percent')

        # Rete
        try:
            net = psutil.net_io_counters()
            s.network_sent_mb = round(
                (net.bytes_sent - self._last_net_io.bytes_sent) / (1024**2) / delta, 3
            )
            s.network_recv_mb = round(
                (net.bytes_recv - self._last_net_io.bytes_recv) / (1024**2) / delta, 3
            )
            self._last_net_io = net
        except:
            pass

        # Processi
        s.process_count = len(psutil.pids())
        s.top_processes = self._get_top_processes(5)

        # Uptime
        s.uptime_hours = round((now - self._boot_time).total_seconds() / 3600, 1)

        self._last_time = now
        return s

    def get_summary(self) -> Dict[str, Any]:
        """Restituisce un sommario rapido dello stato."""
        s = self.get_stats()
        return {
            'health': 'good' if s.cpu_percent < 80 and s.ram_percent < 80 and s.disk_percent < 90 else 'warning',
            'cpu': round(s.cpu_percent, 1),
            'ram': round(s.ram_percent, 1),
            'disk': round(s.disk_percent, 1),
            'gpu': round(s.gpu_percent, 1) if s.gpu_percent else None,
            'temp': s.cpu_temp,
            'processes': s.process_count,
            'uptime': s.uptime_hours,
        }

    def get_bottlenecks(self) -> List[str]:
        """Identifica i colli di bottiglia attuali."""
        s = self.get_stats()
        bottlenecks = []

        if s.cpu_percent > 85:
            bottlenecks.append(f"CPU al {s.cpu_percent}%")
        if s.ram_percent > 85:
            bottlenecks.append(f"RAM al {s.ram_percent}%")
        if s.disk_percent > 95:
            bottlenecks.append(f"Disco quasi pieno ({s.disk_percent}%)")
        if s.gpu_percent and s.gpu_percent > 90:
            bottlenecks.append(f"GPU al {s.gpu_percent}%")
        if s.cpu_temp and s.cpu_temp > 85:
            bottlenecks.append(f"Temperatura CPU alta ({s.cpu_temp}°C)")

        return bottlenecks

    # ---- Metodi privati ----

    def _get_cpu_temp(self) -> Optional[float]:
        """Legge temperatura CPU."""
        try:
            # Prova con LibreHardwareMonitor o WMI
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current:
                                return entry.current
        except:
            pass

        try:
            # WMI fallback
            import wmi
            c = wmi.WMI()
            temps = c.query("SELECT * FROM Win32_PerfFormattedData_Counters_ThermalZoneInformation")
            for t in temps:
                temp = getattr(t, 'Temperature', None)
                if temp:
                    temp_k = int(temp) / 10.0
                    if temp_k > 200:  # Kelvin valido (> -73°C)
                        temp_c = round(temp_k - 273.15, 1)
                        if -50 < temp_c < 150:  # Sanity check
                            return temp_c
        except:
            pass

        # Prova con LibreHardwareMonitor via WMI
        try:
            import wmi
            c = wmi.WMI(namespace=r'root\LibreHardwareMonitor')
            temps = c.query("SELECT * FROM Sensor WHERE SensorType='Temperature'")
            for t in temps:
                val = getattr(t, 'Value', None)
                name = getattr(t, 'Name', '')
                if val and 'cpu' in str(name).lower():
                    return round(float(val), 1)
        except:
            pass

        return None

    def _get_gpu_stats(self) -> Optional[Dict[str, float]]:
        """Legge statistiche GPU via nvidia-smi o WMI."""
        # Prova nvidia-smi
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                if len(parts) >= 2:
                    return {
                        'gpu_percent': float(parts[0]),
                        'gpu_temp': float(parts[1]),
                        'mem_percent': float(parts[2]) / float(parts[3]) * 100 if float(parts[3]) > 0 else 0,
                    }
        except:
            pass

        return None

    def _get_top_processes(self, n: int = 5) -> List[Dict]:
        """Restituisce i processi piu' pesanti."""
        processes = []
        try:
            for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                               key=lambda p: p.info.get('cpu_percent', 0) or 0,
                               reverse=True)[:n]:
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': round(proc.info.get('cpu_percent', 0) or 0, 1),
                        'mem': round(proc.info.get('memory_percent', 0) or 0, 1),
                    })
                except:
                    pass
        except:
            pass
        return processes


# Singleton
_monitor_instance = None

def get_monitor() -> SystemMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor()
    return _monitor_instance


if __name__ == "__main__":
    import time
    mon = get_monitor()
    print("=== BalancePC — Monitor ===")
    for _ in range(5):
        s = mon.get_stats()
        print(f"CPU: {s.cpu_percent:5.1f}% | RAM: {s.ram_percent:5.1f}% | "
              f"DISK: {s.disk_percent:5.1f}% | "
              f"TEMP: {s.cpu_temp if s.cpu_temp else 'N/A'}°C | "
              f"UPTIME: {s.uptime_hours:.1f}h")
        print(f"  Top: {[p['name'] for p in s.top_processes]}")
        print(f"  Bottlenecks: {mon.get_bottlenecks()}")
        time.sleep(2)
