"""
Daemon — Servizio background per ottimizzazione continua
=========================================================
Esegue in background e ottimizza il sistema periodicamente.
"""

import time
import threading
import sys
from datetime import datetime

from .monitor import get_monitor
from .profiler import get_profiler
from .optimizer import clean_temp_files, clean_dns_cache


class BalanceDaemon:
    """
    Servizio background che mantiene il PC ottimizzato.
    Esegue controlli periodici e adatta il sistema.
    """

    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds  # 5 minuti tra controlli
        self._running = False
        self._thread: threading.Thread = None
        self._monitor = get_monitor()
        self._profiler = get_profiler()
        self._last_cleanup = 0

    def start(self):
        """Avvia il demone."""
        if self._running:
            return
        self._running = True
        self._profiler.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[BalancePC] Daemon avviato (check ogni {self.interval}s)")

    def stop(self):
        """Ferma il demone."""
        self._running = False
        self._profiler.stop()
        print("[BalancePC] Daemon fermato")

    def _loop(self):
        """Loop principale."""
        while self._running:
            try:
                self._tick()
            except Exception as e:
                print(f"[BalancePC] Errore: {e}")
            time.sleep(self.interval)

    def _tick(self):
        """Esegue un ciclo di controllo e ottimizzazione."""
        # Monitora
        stats = self._monitor.get_stats()
        bottlenecks = self._monitor.get_bottlenecks()

        # Pulizia temp ogni 30 minuti
        now = time.time()
        if now - self._last_cleanup > 1800:
            clean_temp_files()
            clean_dns_cache()
            self._last_cleanup = now

        # Log stato
        status = (
            f"CPU: {stats.cpu_percent}% | RAM: {stats.ram_percent}% | "
            f"DISK: {stats.disk_percent}% | "
            f"TEMP: {stats.cpu_temp if stats.cpu_temp else 'N/A'}°C | "
            f"PROC: {stats.process_count}"
        )

        if bottlenecks:
            status += f" | BOTTLENECKS: {', '.join(bottlenecks)}"

        print(f"[BalancePC] {datetime.now().strftime('%H:%M:%S')} {status}")


_daemon_instance = None


def run_daemon():
    """Avvia il demone (entry point)."""
    global _daemon_instance
    daemon = BalanceDaemon()
    _daemon_instance = daemon
    daemon.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == "__main__":
    run_daemon()
