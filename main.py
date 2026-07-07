#!/usr/bin/env python3
"""
BalancePC — System Optimizer
=============================
Mantiene il PC in equilibrio in base all'utilizzo reale.
Adatta CPU, RAM, disco e GPU alle tue esigenze in tempo reale.
Niente bloat, niente pubblicita'.

Utilizzo:
    BalancePC.exe                    Avvia la GUI
    BalancePC.exe --optimize         Ottimizzazione immediata con report
    BalancePC.exe --monitor          Monitoraggio risorse in tempo reale
    BalancePC.exe --check-update     Controlla aggiornamenti
    BalancePC.exe --install          Installa avvio automatico + ottimizzazione oraria
    BalancePC.exe --uninstall        Rimuovi avvio automatico
    BalancePC.exe --status           Stato del sistema e della persistenza
    BalancePC.exe --tray             Avvia in system tray
    BalancePC.exe --daemon           Avvia come servizio background
"""

import sys
import os
import platform
import argparse
from datetime import datetime

VERSION = "1.0.0"
APP_NAME = "BalancePC"

if platform.system() != "Windows":
    print("BalancePC richiede Windows 10/11.")
    sys.exit(1)


def print_banner():
    print(f"""
{'='*55}
  {APP_NAME} v{VERSION} — Il tuo PC si adatta a te
{'='*55}
""")


def cmd_monitor():
    """Monitoraggio risorse in tempo reale."""
    from core.monitor import SystemMonitor
    mon = SystemMonitor()
    print_banner()
    print(" Monitoraggio in tempo reale (Ctrl+C per uscire)\n")
    print(f"{'CPU':>8s} {'RAM':>8s} {'DISK':>8s} {'TEMP':>8s} {'PROC':>6s}  {'STATO'}")
    print("-" * 55)
    try:
        import time
        while True:
            stats = mon.get_stats()
            cpu = getattr(stats, 'cpu_percent', 0) or 0
            ram = getattr(stats, 'ram_percent', 0) or 0
            disk = getattr(stats, 'disk_percent', 0) or 0
            temp = getattr(stats, 'cpu_temp', None) or 0
            procs = getattr(stats, 'process_count', 0) or 0
            bottlenecks = mon.get_bottlenecks()
            stato = "OK" if not bottlenecks else f"⚠ {bottlenecks[0][:25]}"
            print(f"\r{cpu:7.1f}% {ram:7.1f}% {disk:7.1f}% {temp:7.0f}°C {procs:5d}  {stato:30s}", end="")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n Monitoraggio terminato.")
        # Mostra sommario finale
        stats = mon.get_stats()
        summary = mon.get_summary()
        print(f" Salute sistema: {summary.get('health', 'N/A')}")
        print(f" Uptime: {stats.uptime_hours:.1f} ore")
        print(f" Processi: {stats.process_count}")
        print(" Grazie per aver usato BalancePC!")


def cmd_optimize(silent: bool = False):
    """Esegue ottimizzazione immediata con report dettagliato."""
    from core.optimizer import auto_optimize
    from core.notifications import notify_optimization_complete

    if not silent:
        print_banner()
        print(" Esecuzione ottimizzazione in corso...\n")

    start = datetime.now()
    results = auto_optimize()
    elapsed = (datetime.now() - start).total_seconds()

    if silent:
        # Solo notifica
        notify_optimization_complete(results)
        return

    # Report dettagliato
    ok_count = sum(1 for v in results.values() if isinstance(v, tuple) and v[0])
    total = len(results)

    print(f"{'='*55}")
    print(f" REPORT OTTIMIZZAZIONE — {ok_count}/{total} operazioni completate")
    print(f"{'='*55}\n")

    for action, (ok, msg) in sorted(results.items()):
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {action}")
        if msg:
            print(f"       {msg}")
        print()

    # Riepilogo finale
    print(f"{'='*55}")
    print(f" Tempo: {elapsed:.1f}s | {ok_count}/{total} azioni completate")
    print(f" Consiglio: tieni BalancePC in esecuzione per ottimizzazione continua")
    print(f"            o usa --install per avvio automatico.")
    print(f"{'='*55}")

    # Notifica in background
    notify_optimization_complete(results)


def cmd_check_update():
    """Controlla aggiornamenti disponibili."""
    from core.self_update import check_for_updates, download_update
    from core.notifications import notify_update_available

    print_banner()
    print(" Controllo aggiornamenti in corso...\n")
    ok, msg, data = check_for_updates()
    print(f" {msg}")

    if ok and data:
        print("\n Nuova versione trovata! Download in corso...")
        ok2, path = download_update(data)
        if ok2:
            print(f" ✅ Scaricato ({os.path.getsize(path) // 1024} KB)")
            print(" Applicazione aggiornamento...")
            from core.self_update import apply_update
            ok3, msg3 = apply_update(path)
            print(f" {msg3}")
            notify_update_available(
                data.get('tag_name', '?').lstrip('v'),
                VERSION,
                data.get('body', '')
            )
        else:
            print(f" ❌ {path}")
    elif not ok:
        print("\n Non e' possibile verificare ora. Riprova piu' tardi.")
    else:
        print("\n Sei aggiornato. Nessuna azione necessaria.")


def cmd_install():
    """Installa persistenza (avvio automatico + ottimizzazione oraria)."""
    from core.persistence import install_autostart, install_hourly_task
    from core.notifications import notify_balloon

    print_banner()
    print(" Installazione persistenza...\n")

    ok1, msg1 = install_autostart()
    print(f" {'✅' if ok1 else '❌'} Avvio automatico: {msg1}")

    ok2, msg2 = install_hourly_task()
    print(f" {'✅' if ok2 else '❌'} Ottimizzazione oraria: {msg2}")

    if ok1 or ok2:
        print(f"\n ✅ {APP_NAME} e' ora installato come servizio di sistema.")
        print("    Partira' automaticamente all'accesso e ottimizzera' ogni ora.")
        notify_balloon(f"{APP_NAME} — Installato",
                       f"Avvio automatico e ottimizzazione oraria attivi.",
                       duration_sec=4)


def cmd_uninstall():
    """Rimuovi persistenza."""
    from core.persistence import uninstall_autostart

    print_banner()
    print(" Rimozione persistenza...\n")
    ok, msg = uninstall_autostart()
    print(f" {msg}")
    print(f"\n ✅ Persistenza rimossa. {APP_NAME} non partira' piu' automaticamente.")


def cmd_status():
    """Mostra stato completo del sistema e della persistenza."""
    from core.monitor import get_monitor
    from core.persistence import status as persistence_status

    print_banner()
    mon = get_monitor()
    summary = mon.get_summary()
    stats = mon.get_stats()

    print(" STATO SISTEMA")
    print(f"  Salute:     {'🟢 Buona' if summary.get('health') == 'good' else '🟡 Attenzione'}")
    print(f"  CPU:        {summary.get('cpu', 'N/A'):.1f}%")
    print(f"  RAM:        {summary.get('ram', 'N/A'):.1f}%")
    print(f"  Disco:      {summary.get('disk', 'N/A'):.1f}%")
    print(f"  Temperatura:{' ' + str(summary.get('temp', 'N/A')) + '°C' if summary.get('temp') else ' N/A'}")
    print(f"  Processi:   {summary.get('processes', 'N/A')}")
    print(f"  Uptime:     {stats.uptime_hours:.1f} ore")
    print(f"  Versione:   {VERSION}")
    print()

    bottlenecks = mon.get_bottlenecks()
    if bottlenecks:
        print(" ⚠ COLLI DI BOTTIGLIA:")
        for b in bottlenecks:
            print(f"    • {b}")
    else:
        print(" ✅ Sistema in equilibrio. Nessun collo di bottiglia.")
    print()

    print(" PERSISTENZA:")
    print(f"  {persistence_status()}")
    print()
    print(f" Per installare avvio automatico: {APP_NAME}.exe --install")
    print(f" Per controllare aggiornamenti:   {APP_NAME}.exe --check-update")


def cmd_update_done():
    """Chiamato dopo un aggiornamento riuscito (dal batch di update)."""
    from core.notifications import notify_balloon
    notify_balloon(f"{APP_NAME} — Aggiornato",
                   f"{APP_NAME} e' stato aggiornato con successo!",
                   duration_sec=4)
    print(f"{APP_NAME} aggiornato con successo.")


def main():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} - System Optimizer",
        epilog=f"Esempio: {APP_NAME}.exe --optimize  (ottimizza e mostra report)"
    )
    parser.add_argument("--monitor", action="store_true", help="Monitoraggio risorse in tempo reale")
    parser.add_argument("--optimize", action="store_true", help="Ottimizzazione immediata con report")
    parser.add_argument("--tray", action="store_true", help="Avvia in system tray")
    parser.add_argument("--daemon", action="store_true", help="Avvia come servizio background (monitoraggio continuo)")
    parser.add_argument("--silent", action="store_true", help="Esecuzione silenziosa (solo notifiche)")
    parser.add_argument("--check-update", action="store_true", help="Controlla e installa aggiornamenti")
    parser.add_argument("--install", action="store_true", help="Installa avvio automatico + ottimizzazione oraria")
    parser.add_argument("--uninstall", action="store_true", help="Rimuovi avvio automatico")
    parser.add_argument("--status", action="store_true", help="Mostra stato sistema e persistenza")
    parser.add_argument("--update-done", action="store_true", help="[Interno] Notifica aggiornamento completato")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} v{VERSION}")
    args = parser.parse_args()

    # Comandi
    if args.update_done:
        cmd_update_done()
        return

    if args.status:
        cmd_status()
        return

    if args.check_update:
        cmd_check_update()
        return

    if args.install:
        cmd_install()
        return

    if args.uninstall:
        cmd_uninstall()
        return

    if args.monitor:
        cmd_monitor()
        return

    if args.optimize:
        cmd_optimize(silent=args.silent)
        return

    if args.daemon:
        from core.daemon import run_daemon
        run_daemon()
        return

    # GUI (default)
    try:
        from ui.app import run_app
        run_app(tray_mode=args.tray, silent=args.silent)
    except ImportError as e:
        print(f"Errore: {e}")
        print("Esegui: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Errore: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
