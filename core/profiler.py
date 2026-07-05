"""
Usage Profiler — Rileva pattern di utilizzo e adatta il sistema
================================================================
Analizza l'utilizzo del PC nel tempo e adatta
automaticamente CPU, RAM e piano energia al tuo stile.
"""

import time
import json
import os
import threading
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

from .monitor import get_monitor, SystemSnapshot
from .optimizer import auto_optimize


# Profilo configurazione
PROFILES = {
    'gaming': {
        'name': 'Gioco',
        'power_plan': 'high_performance',
        'priority': 'gpu',
        'minimize_background': True,
        'description': 'Massime prestazioni per gaming',
    },
    'work': {
        'name': 'Lavoro',
        'power_plan': 'balanced',
        'priority': 'cpu',
        'minimize_background': False,
        'description': 'Bilanciato per produttivita\'',
    },
    'idle': {
        'name': 'Riposo',
        'power_plan': 'power_saver',
        'priority': 'none',
        'minimize_background': False,
        'description': 'Risparmio energetico',
    },
    'streaming': {
        'name': 'Multimedia',
        'power_plan': 'balanced',
        'priority': 'gpu',
        'minimize_background': True,
        'description': 'Ottimizzato per video e streaming',
    },
    'development': {
        'name': 'Sviluppo',
        'power_plan': 'high_performance',
        'priority': 'cpu',
        'minimize_background': False,
        'description': 'Per compilazione e sviluppo',
    },
}


class UsageProfiler:
    """
    Rileva il pattern di utilizzo e adatta il sistema.
    Analizza: CPU, RAM, GPU, processi in esecuzione.
    """

    def __init__(self, history_minutes: int = 30, auto_adapt: bool = True):
        self.history = deque(maxlen=history_minutes * 6)  # 6 campioni/min
        self.current_profile = 'balanced'
        self.auto_adapt = auto_adapt
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_optimization = time.time()
        self._monitor = get_monitor()

    def start(self):
        """Avvia il profiling in background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Ferma il profiling."""
        self._running = False

    def add_sample(self, stats: SystemSnapshot):
        """Aggiunge un campione alla cronologia."""
        with self._lock:
            self.history.append({
                'timestamp': stats.timestamp,
                'cpu': stats.cpu_percent,
                'ram': stats.ram_percent,
                'disk': stats.disk_percent,
                'gpu': stats.gpu_percent or 0,
                'process_count': stats.process_count,
                'top_processes': [p['name'] for p in stats.top_processes],
                'uptime': stats.uptime_hours,
            })

    def detect_profile(self) -> str:
        """
        Rileva il profilo di utilizzo corrente basato sui campioni recenti.
        Restituisce: 'gaming', 'work', 'idle', 'streaming', 'development', 'balanced'
        """
        with self._lock:
            if len(self.history) < 3:
                return 'balanced'

            # Calcola medie recenti
            recent = list(self.history)[-min(18, len(self.history)):]  # ultimi ~3 minuti
            avg_cpu = sum(s['cpu'] for s in recent) / len(recent)
            avg_gpu = sum(s['gpu'] for s in recent) / len(recent)
            max_cpu = max(s['cpu'] for s in recent)
            processes = set()
            for s in recent:
                for p in s['top_processes']:
                    processes.add(p.lower() if p else '')

            # Rilevamento pattern
            # Gaming: GPU alta, CPU media-alta
            if avg_gpu > 60 and avg_cpu > 40:
                return 'gaming'

            # Sviluppo: CPU alta, molti processi, IDE presenti
            dev_tools = {'code.exe', 'devenv.exe', 'clion64.exe', 'pycharm64.exe',
                        'idea64.exe', 'eclipse.exe', 'sublime_text.exe', 'notepad++.exe',
                        'vim.exe', 'nvim.exe', 'wsl.exe', 'docker.exe', 'node.exe'}
            if avg_cpu > 50 and len(processes & dev_tools) > 0:
                return 'development'

            # Streaming: GPU media, processi multimediali
            media_tools = {'chrome.exe', 'firefox.exe', 'vlc.exe', 'mpc-hc.exe',
                          'spotify.exe', 'obs64.exe', 'obs32.exe'}
            if avg_gpu > 30 and len(processes & media_tools) > 0:
                return 'streaming'

            # Lavoro: CPU media, processi ufficio
            work_tools = {'winword.exe', 'excel.exe', 'powerpnt.exe', 'outlook.exe',
                         'teams.exe', 'slack.exe', 'zoom.exe', 'chrome.exe', 'firefox.exe'}
            if avg_cpu > 25 and len(processes & work_tools) > 0:
                return 'work'

            # Idle: CPU bassa, nessuna attivita'
            if avg_cpu < 15 and avg_gpu < 10 and max_cpu < 30:
                return 'idle'

            return 'balanced'

    def adapt_system(self, force: bool = False) -> Dict:
        """
        Adatta il sistema al profilo rilevato.
        Restituisce le azioni eseguite.
        """
        if not self.auto_adapt and not force:
            return {'adapted': False, 'reason': 'auto_adapt_disabled'}

        now = time.time()
        if now - self._last_optimization < 120 and not force:  # min 2 min tra adattamenti
            return {'adapted': False, 'reason': 'too_soon'}

        profile = self.detect_profile()
        if profile == self.current_profile and not force:
            return {'adapted': False, 'reason': 'same_profile'}

        self.current_profile = profile
        profile_config = PROFILES.get(profile, PROFILES['balanced'])

        actions = {}

        # Applica piano energia
        from .optimizer import (set_high_performance_power, set_balanced_power, set_power_saver)
        power_map = {
            'high_performance': set_high_performance_power,
            'balanced': set_balanced_power,
            'power_saver': set_power_saver,
        }
        power_fn = power_map.get(profile_config['power_plan'], set_balanced_power)
        ok, msg = power_fn()
        actions['power_plan'] = {'ok': ok, 'msg': msg}

        # Minimizza processi background se richiesto
        if profile_config['minimize_background']:
            from .optimizer import kill_top_processes
            ok, msg = kill_top_processes(n=2, min_cpu=40.0)
            if ok:
                actions['kill_background'] = {'ok': ok, 'msg': msg}

        self._last_optimization = now

        return {
            'adapted': True,
            'profile': profile,
            'profile_name': profile_config['name'],
            'actions': actions,
        }

    def get_status(self) -> Dict:
        """Restituisce lo stato corrente del profiler."""
        with self._lock:
            return {
                'current_profile': self.current_profile,
                'profile_name': PROFILES.get(self.current_profile, {}).get('name', 'Sconosciuto'),
                'auto_adapt': self.auto_adapt,
                'samples': len(self.history),
                'running': self._running,
                'last_optimization': self._last_optimization,
            }

    def _loop(self):
        """Loop principale di campionamento e adattamento."""
        while self._running:
            try:
                stats = self._monitor.get_stats()
                self.add_sample(stats)
                self.adapt_system()
                time.sleep(10)  # campiona ogni 10 secondi
            except:
                time.sleep(30)


# Singleton
_profiler_instance = None

def get_profiler() -> UsageProfiler:
    global _profiler_instance
    if _profiler_instance is None:
        _profiler_instance = UsageProfiler()
    return _profiler_instance


if __name__ == "__main__":
    profiler = get_profiler()
    profiler.start()
    print("=== BalancePC — Profiler ===")
    try:
        while True:
            time.sleep(5)
            status = profiler.get_status()
            print(f"Profilo: {status['profile_name']} | "
                  f"Campioni: {status['samples']} | "
                  f"Auto: {status['auto_adapt']}")
            if status['samples'] > 0:
                profile = profiler.detect_profile()
                print(f"Rilevato: {profile} ({PROFILES.get(profile, {}).get('name', '?')})")
    except KeyboardInterrupt:
        profiler.stop()
        print("\nFermo.")
