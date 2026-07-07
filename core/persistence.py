"""
persistence — Auto-avvio e persistenza
=========================================
Crea uno Scheduled Task di Windows che lancia
l'eseguibile all'accesso dell'utente e/o ogni
X ore per mantenere il sistema ottimizzato.

Usa schtasks.exe (presente su ogni Windows).
"""

import os
import sys
import subprocess
from typing import Tuple

APP_NAME = "BalancePC"
TASK_NAME = f"{APP_NAME}"


def get_exe_path() -> str:
    """Restituisce il percorso dell'eseguibile corrente."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    # In sviluppo: restituisci il path a main.py
    main_py = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'main.py')
    if os.path.exists(main_py):
        return f'python "{main_py}"'
    return sys.executable


def install_autostart(args: str = "--tray") -> Tuple[bool, str]:
    """
    Crea uno scheduled task per l'avvio automatico all'accesso.
    """
    exe = get_exe_path()
    if not os.path.exists(exe.replace('python "', '').replace('"', '')) and not getattr(sys, 'frozen', False):
        return False, "Eseguibile non trovato."

    cmd = (
        f'schtasks /create /tn "{TASK_NAME}" /tr "{exe} {args}" '
        f'/sc onlogon /rl highest /f /it'
    )

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            return True, f"Avvio automatico installato. {APP_NAME} partira' all'accesso."
        else:
            return False, f"Errore: {result.stderr.strip()}"
    except Exception as e:
        return False, str(e)


def install_hourly_task(args: str = "--optimize --silent") -> Tuple[bool, str]:
    """
    Crea uno scheduled task che esegue l'ottimizzazione ogni ora.
    """
    exe = get_exe_path()
    task_name = f"{TASK_NAME}_Hourly"

    cmd = (
        f'schtasks /create /tn "{task_name}" /tr "{exe} {args}" '
        f'/sc hourly /mo 1 /rl lowest /f /it'
    )

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            return True, f"Ottimizzazione automatica ogni ora attivata."
        else:
            return False, f"Errore: {result.stderr.strip()}"
    except Exception as e:
        return False, str(e)


def uninstall_autostart() -> Tuple[bool, str]:
    """Rimuove lo scheduled task di avvio automatico."""
    tasks = [TASK_NAME, f"{TASK_NAME}_Hourly"]
    results = []

    for task in tasks:
        try:
            result = subprocess.run(
                f'schtasks /delete /tn "{task}" /f',
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                results.append(f"{task}: rimosso")
        except:
            results.append(f"{task}: errore rimozione")

    if results:
        return True, " | ".join(results)
    return False, "Nessun task trovato."


def is_installed() -> Tuple[bool, bool]:
    """Verifica se i task sono installati.
    Restituisce: (autostart, hourly)"""
    autostart = False
    hourly = False

    try:
        result = subprocess.run(
            f'schtasks /query /tn "{TASK_NAME}"',
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        autostart = result.returncode == 0
    except:
        pass

    try:
        result = subprocess.run(
            f'schtasks /query /tn "{TASK_NAME}_Hourly"',
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        hourly = result.returncode == 0
    except:
        pass

    return autostart, hourly


def status() -> str:
    """Resoconto dello stato della persistenza."""
    auto, hourly = is_installed()
    parts = []
    parts.append(f"Avvio automatico: {'✅ ATTIVO' if auto else '❌ NON ATTIVO'}")
    parts.append(f"Ottimizzazione oraria: {'✅ ATTIVA' if hourly else '❌ NON ATTIVA'}")
    return " | ".join(parts)


if __name__ == "__main__":
    print(f"=== {APP_NAME} — Persistenza ===")
    print(status())
    print()
    cmd = input("Cosa fare? [install/uninstall/status]: ").strip().lower()
    if cmd == 'install':
        ok, msg = install_autostart()
        print(msg)
        ok2, msg2 = install_hourly_task()
        print(msg2)
    elif cmd == 'uninstall':
        ok, msg = uninstall_autostart()
        print(msg)
    else:
        print(status())
