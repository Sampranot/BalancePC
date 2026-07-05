"""
Optimizer — Azioni di ottimizzazione sistema
==============================================
Esegue ottimizzazioni in base allo stato corrente:
  - Pulizia file temporanei
  - Disabilitazione startup bloat
  - Ottimizzazione piano energia
  - Gestione processi pesanti
  - Pulizia cache
"""

import os
import sys
import subprocess
import tempfile
import shutil
import psutil
import platform
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime, timedelta

from .monitor import get_monitor, SystemSnapshot


# Directory da pulire
TEMP_DIRS = [
    os.environ.get('TEMP', ''),
    os.environ.get('TMP', ''),
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
    os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch'),
]

# Programmi di startup comuni non necessari
STARTUP_BLOAT_KEYWORDS = [
    'adobe updater', 'google updater', 'spotify', 'skype', 'discord',
    'steam', 'epic', 'origin', 'brave', 'opera', 'samsung',
    'hp', 'dell', 'lenovo', 'asus', 'acer', 'msi',
    'java', 'quicktime', 'apple', 'bonjour', 'itunes',
    'microsoft teams', 'skype', 'onedrive', 'teams',
    'vcredist', 'directx', 'vc_redist',
]


def clean_temp_files() -> Tuple[bool, str]:
    """Pulisce i file temporanei del sistema."""
    total_freed = 0
    cleaned = 0
    errors = 0

    for d in TEMP_DIRS:
        if not d or not os.path.exists(d):
            continue
        try:
            for root, dirs, files in os.walk(d, topdown=False):
                for name in files:
                    try:
                        fp = os.path.join(root, name)
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        total_freed += size
                        cleaned += 1
                    except:
                        errors += 1
                        continue
                for name in dirs:
                    try:
                        fp = os.path.join(root, name)
                        shutil.rmtree(fp, ignore_errors=True)
                    except:
                        continue
        except:
            continue

    freed_mb = round(total_freed / (1024**2), 1)
    return True, f"Puliti {cleaned} files, liberati {freed_mb} MB ({errors} errori ignorati)"


def clean_prefetch() -> Tuple[bool, str]:
    """Pulisce la cache Prefetch."""
    prefetch = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch')
    if not os.path.exists(prefetch):
        return False, "Prefetch non trovato"

    cleaned = 0
    try:
        for f in os.listdir(prefetch):
            fp = os.path.join(prefetch, f)
            if os.path.isfile(fp) and f.endswith('.pf'):
                try:
                    os.remove(fp)
                    cleaned += 1
                except:
                    pass
        return True, f"Puliti {cleaned} file Prefetch"
    except Exception as e:
        return False, str(e)


def clean_dns_cache() -> Tuple[bool, str]:
    """Pulisce la cache DNS."""
    try:
        result = subprocess.run(
            ['ipconfig', '/flushdns'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, "Cache DNS pulita"
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


# GUID piani energia standard Windows (potrebbero non esistere su tutti i PC)
_POWER_PLANS = {
    'high_performance': '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
    'balanced': '381b4222-f694-41f0-9685-ff5bb260df2e',
    'power_saver': 'a1841308-3541-4fab-bc81-f71556f20b4a',
}


def _get_available_power_plans() -> dict:
    """Recupera i piani energia disponibili sul sistema.
    Restituisce {nome: guid} per i piani esistenti.
    """
    plans = {}
    try:
        result = subprocess.run(
            ['powercfg', '/list'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            # Formato: "GUID123456  (Nome piano)"
            m = re.search(r'([0-9a-f\-]{36})\s+\(([^)]+)\)', line, re.IGNORECASE)
            if m:
                plans[m.group(2).strip()] = m.group(1)
    except Exception:
        pass
    return plans


def _set_power_plan(plan_name: str, plan_guid: str) -> Tuple[bool, str]:
    """Imposta un piano energia, verificando che esista."""
    try:
        available = _get_available_power_plans()
        if not available:
            # Fallback: prova il GUID diretto
            result = subprocess.run(
                ['powercfg', '/s', plan_guid],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return True, f"Piano energia: {plan_name}"
            return False, result.stderr.strip()

        # Cerca il GUID dal nome o usa il GUID predefinito
        guid = available.get(plan_name) or plan_guid
        result = subprocess.run(
            ['powercfg', '/s', guid],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, f"Piano energia: {plan_name}"
        return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def set_high_performance_power() -> Tuple[bool, str]:
    """Imposta il piano energia ad alte prestazioni."""
    return _set_power_plan('Alte prestazioni', _POWER_PLANS['high_performance'])


def set_balanced_power() -> Tuple[bool, str]:
    """Imposta il piano energia bilanciato."""
    return _set_power_plan('Bilanciato', _POWER_PLANS['balanced'])


def set_power_saver() -> Tuple[bool, str]:
    """Imposta il piano energia risparmio."""
    return _set_power_plan('Risparmio energia', _POWER_PLANS['power_saver'])


def disable_startup_bloat() -> Tuple[bool, str]:
    """Disabilita programmi startup non essenziali."""
    disabled = 0
    try:
        # Usa WMIC o il registro
        import winreg
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    name_lower = name.lower()
                    if any(bloat in name_lower for bloat in STARTUP_BLOAT_KEYWORDS):
                        winreg.DeleteValue(key, name)
                        disabled += 1
                    i += 1
                except OSError:
                    break
        return True, f"Disabilitati {disabled} programmi startup"
    except Exception as e:
        return False, str(e)


def kill_process(pid: int) -> bool:
    """Termina un processo per PID."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        return True
    except:
        try:
            proc = psutil.Process(pid)
            proc.kill()
            return True
        except:
            return False


def kill_top_processes(n: int = 3, min_cpu: float = 30.0) -> Tuple[bool, str]:
    """Termina i processi piu' pesanti che superano la soglia."""
    killed = []
    try:
        processes = sorted(
            psutil.process_iter(['pid', 'name', 'cpu_percent']),
            key=lambda p: p.info.get('cpu_percent', 0) or 0,
            reverse=True
        )
        for p in processes[:n]:
            try:
                cpu = p.info.get('cpu_percent', 0) or 0
                name = p.info.get('name', 'unknown')
                pid = p.info['pid']
                if cpu > min_cpu and pid > 0 and name.lower() not in ['system', 'idle']:
                    # Salta processi di sistema:
                    # Controllo robusto: non usare 'SYSTEM' che varia per lingua
                    # Usa l'ID sessione 0 (servizi/system) come discriminante
                    try:
                        proc = psutil.Process(pid)
                        # Salta processi con sessione 0 (servizi Windows)
                        # e processi di sistema noti
                        is_system = False
                        try:
                            is_system = proc.username().upper() in (
                                'SYSTEM', 'SISTEMA', 'NT AUTHORITY\\SYSTEM',
                                'AUTORITÀ NT\\SYSTEM', 'AUTORITA NT\\SYSTEM')
                        except Exception:
                            pass
                        if not is_system and name.lower() not in ['svchost.exe', 'services.exe', 'wininit.exe']:
                            kill_process(pid)
                            killed.append(f"{name} (CPU: {cpu}%)")
                    except Exception:
                        continue
            except:
                continue
    except:
        pass

    if killed:
        return True, f"Terminati: {', '.join(killed)}"
    return False, "Nessun processo pesante da terminare"


def _stop_service(service_name: str) -> bool:
    """Ferma un servizio Windows in modo non bloccante."""
    try:
        r = subprocess.run(
            ['net', 'stop', service_name],
            capture_output=True, text=True, timeout=15
        )
        return r.returncode == 0
    except Exception:
        return False


def _start_service(service_name: str) -> bool:
    """Avvia un servizio Windows in modo non bloccante."""
    try:
        r = subprocess.run(
            ['net', 'start', service_name],
            capture_output=True, text=True, timeout=15
        )
        return r.returncode == 0
    except Exception:
        return False


def clear_windows_update_cache() -> Tuple[bool, str]:
    """Pulisce la cache di Windows Update.
    NON bloccante: se il servizio non si ferma, prova a pulire lo stesso.
    """
    cache_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'),
                             'SoftwareDistribution', 'Download')
    if not os.path.exists(cache_dir):
        return False, "Cache Windows Update non trovata"

    # Tentativo di fermare il servizio (non fatale se fallisce)
    was_running = False
    try:
        was_running = _stop_service('wuauserv')
    except Exception:
        pass

    cleaned = 0
    try:
        for f in os.listdir(cache_dir):
            fp = os.path.join(cache_dir, f)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
                    cleaned += 1
                elif os.path.isdir(fp):
                    shutil.rmtree(fp, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass

    # Riavvia solo se era in esecuzione
    if was_running:
        try:
            _start_service('wuauserv')
        except Exception:
            pass

    if cleaned > 0:
        return True, f"Puliti {cleaned} file cache Windows Update"
    return True, "Cache Windows Update gia' pulita"


def empty_recycle_bin() -> Tuple[bool, str]:
    """Svuota il Cestino."""
    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
        return True, "Cestino svuotato"
    except Exception as e:
        return False, str(e)


def auto_optimize() -> Dict[str, Tuple[bool, str]]:
    """
    Esegue ottimizzazioni automatiche in base allo stato del sistema.
    Restituisce dizionario {azione: (successo, messaggio)}.
    """
    results = {}
    
    mon = get_monitor()
    stats = mon.get_stats()
    bottlenecks = mon.get_bottlenecks()
    
    # Pulizia temp
    results['clean_temp'] = clean_temp_files()
    
    # Cache DNS se connesso
    results['clean_dns'] = clean_dns_cache()
    
    # Cache Windows Update
    results['clean_wu_cache'] = clear_windows_update_cache()
    
    # Cestino
    results['empty_recycle'] = empty_recycle_bin()
    
    # Piano energia in base al carico
    if stats.cpu_percent > 70 or stats.ram_percent > 80:
        # Sotto carico — alte prestazioni
        results['power_plan'] = set_high_performance_power()
    elif stats.cpu_percent < 20 and stats.ram_percent < 40:
        # In idle — risparmio
        results['power_plan'] = set_power_saver()
    else:
        # Normale — bilanciato
        results['power_plan'] = set_balanced_power()
    
    # Processi pesanti
    if stats.cpu_percent > 85:
        results['kill_heavy'] = kill_top_processes(n=3, min_cpu=30.0)
    
    return results


def run_optimization() -> Dict[str, bool]:
    """Esegue ottimizzazione e restituisce risultati {azione: successo}."""
    results = auto_optimize()
    return {k: v[0] for k, v in results.items()}


if __name__ == "__main__":
    print("\n=== BalancePC — Ottimizzazione ===")
    results = auto_optimize()
    print()
    for action, (ok, msg) in results.items():
        print(f"  {'OK' if ok else 'FAIL'} {action}: {msg[:80]}")
