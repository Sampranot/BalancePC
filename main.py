#!/usr/bin/env python3
"""
BalancePC — System Optimizer
=============================
Mantiene il PC in equilibrio in base all'utilizzo reale.
Adatta CPU, RAM, disco e GPU alle tue esigenze in tempo reale.
Niente bloat, niente pubblicita'.

Utilizzo:
    python main.py              Avvia la GUI
    python main.py --monitor    Avvia monitoraggio da terminale
    python main.py --optimize   Esegue ottimizzazione immediata
    python main.py --tray       Avvia in system tray
    python main.py --daemon     Avvia come servizio background
"""

import sys
import os
import platform
import argparse

VERSION = "1.0.0"
APP_NAME = "BalancePC"

if platform.system() != "Windows":
    print("BalancePC richiede Windows 10/11.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="BalancePC - System Optimizer")
    parser.add_argument("--monitor", action="store_true", help="Monitoraggio risorse")
    parser.add_argument("--optimize", action="store_true", help="Ottimizzazione immediata")
    parser.add_argument("--tray", action="store_true", help="Avvia in system tray")
    parser.add_argument("--daemon", action="store_true", help="Avvia come servizio background")
    parser.add_argument("--silent", action="store_true", help="Esecuzione silenziosa")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{VERSION}")
    args = parser.parse_args()

    if args.monitor:
        from core.monitor import SystemMonitor
        mon = SystemMonitor()
        print("\n=== BalancePC — Monitoraggio ===")
        print("Premi Ctrl+C per uscire\n")
        try:
            import time
            while True:
                stats = mon.get_stats()
                cpu = getattr(stats, 'cpu_percent', 0) or 0
                ram = getattr(stats, 'ram_percent', 0) or 0
                disk = getattr(stats, 'disk_percent', 0) or 0
                temp = getattr(stats, 'cpu_temp', None) or 'N/A'
                procs = getattr(stats, 'process_count', 0) or 0
                print(f"\rCPU: {cpu:5.1f}% | "
                      f"RAM: {ram:5.1f}% | "
                      f"DISK: {disk:5.1f}% | "
                      f"TEMP: {temp}°C | "
                      f"PROCESSI: {procs:4d}    ", end="")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nFermo.")
        return

    if args.optimize:
        from core.optimizer import run_optimization
        results = run_optimization()
        print("\n=== Ottimizzazione completata ===")
        for action, ok in results.items():
            print(f"  {'OK' if ok else 'FAIL'} {action}")
        return

    if args.daemon:
        from core.daemon import run_daemon
        run_daemon()
        return

    # GUI
    try:
        from ui.app import run_app
        run_app(tray_mode=args.tray, silent=args.silent)
    except ImportError as e:
        print(f"Errore: {e}")
        print("Esegui: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
