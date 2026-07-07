"""
BalancePC UI — Interfaccia utente
=================================
Monitoraggio risorse, ottimizzazione, profilo adattivo.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.monitor import get_monitor, SystemMonitor
from core.optimizer import auto_optimize, run_optimization
from core.profiler import get_profiler, PROFILES

# Windows service state monitoring (background diagnostic)
try:
    from core.ntservice import check_services
    HAS_SVC_MONITOR = True
except ImportError:
    HAS_SVC_MONITOR = False


class BalancePCApp:
    """Applicazione GUI principale."""

    def __init__(self, tray_mode: bool = False, silent: bool = False):
        self.tray_mode = tray_mode
        self.silent = silent
        self.root: Optional[tk.Tk] = None
        self._monitor = get_monitor()
        self._profiler = get_profiler()
        self._optimizing = False
        self._svc_monitor = check_services(auto_start=True) if HAS_SVC_MONITOR else None

        if not silent:
            self._build_ui()
            self._profiler.start()

    def _build_ui(self):
        """Costruisce l'interfaccia."""
        self.root = tk.Tk()
        self.root.title("BalancePC")
        self.root.geometry("750x550")
        self.root.minsize(600, 400)

        style = ttk.Style()
        style.theme_use('vista' if 'vista' in style.theme_names() else 'clam')

        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="BalancePC", font=('Segoe UI', 18, 'bold')).pack(side=tk.LEFT)
        ttk.Label(header, text="v1.0.0", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(10, 0))

        self.status_label = ttk.Label(header, text="In esecuzione", font=('Segoe UI', 9))
        self.status_label.pack(side=tk.RIGHT)

        # Barra azioni
        actions = ttk.Frame(main)
        actions.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(actions, text="Ottimizza ora", command=self._on_optimize).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions, text="Pulisci temp", command=self._on_clean).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions, text="Aggiorna", command=self._on_refresh).pack(side=tk.LEFT, padx=5)

        self.profile_label = ttk.Label(actions, text="Profilo: --", font=('Segoe UI', 9, 'bold'))
        self.profile_label.pack(side=tk.RIGHT, padx=10)

        # Notebook
        notebook = ttk.Notebook(main)
        notebook.pack(fill=tk.BOTH, expand=True)

        self._build_monitor_tab(notebook)
        self._build_optimize_tab(notebook)
        self._build_info_tab(notebook)

        # Status bar
        self.bottom_bar = ttk.Label(main, text="Pronto", font=('Segoe UI', 8), foreground='gray')
        self.bottom_bar.pack(fill=tk.X, pady=(5, 0))

        # Avvia aggiornamento periodico
        self._update_loop()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_monitor_tab(self, notebook):
        """Tab monitoraggio risorse."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Monitor")

        # Metriche principali
        metrics = ttk.Frame(tab)
        metrics.pack(fill=tk.X, pady=10)

        self._create_metric(metrics, "CPU", 0, 0)
        self._create_metric(metrics, "RAM", 0, 1)
        self._create_metric(metrics, "DISK", 0, 2)
        self._create_metric(metrics, "GPU", 1, 0)
        self._create_metric(metrics, "TEMP", 1, 1)
        self._create_metric(metrics, "PROC", 1, 2)

        # Bottlenecks
        ttk.Label(tab, text="Colli di bottiglia:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=5)
        self.bottleneck_text = tk.Text(tab, height=4, font=('Consolas', 9), state=tk.DISABLED)
        self.bottleneck_text.pack(fill=tk.X, padx=5, pady=5)

        # Top processes
        ttk.Label(tab, text="Processi attivi:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, padx=5)
        self.proc_text = tk.Text(tab, height=8, font=('Consolas', 9), state=tk.DISABLED)
        self.proc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_metric(self, parent, name, row, col):
        """Crea un indicatore metrico."""
        frame = ttk.LabelFrame(parent, text=name, width=140, height=70)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        frame.grid_propagate(False)
        label = ttk.Label(frame, text="--", font=('Segoe UI', 16, 'bold'))
        label.pack(expand=True)
        setattr(self, f'metric_{name.lower()}', label)

    def _build_optimize_tab(self, notebook):
        """Tab risultati ottimizzazione."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Ottimizzazione")

        self.opt_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=('Consolas', 10))
        self.opt_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.opt_text.insert(tk.END, "Esegui 'Ottimizza ora' per vedere i risultati.\n")
        self.opt_text.config(state=tk.DISABLED)

    def _build_info_tab(self, notebook):
        """Tab informazioni."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Info")

        text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, "BalancePC v1.0.0\n\n")
        text.insert(tk.END, "Ottimizza automaticamente il PC in base all'utilizzo.\n\n")
        text.insert(tk.END, "Caratteristiche:\n")
        text.insert(tk.END, "  - Monitoraggio CPU, RAM, disco, GPU, temperatura\n")
        text.insert(tk.END, "  - Rilevamento intelligente del profilo d'uso\n")
        text.insert(tk.END, "  - Pulizia automatica temp e cache\n")
        text.insert(tk.END, "  - Adattamento piano energia in tempo reale\n")
        text.insert(tk.END, "  - Demone background per ottimizzazione continua\n\n")
        text.insert(tk.END, "https://github.com/balancepc/balancepc\n")
        text.config(state=tk.DISABLED)

    def _update_loop(self):
        """Aggiornamento periodico delle metriche."""
        try:
            stats = self._monitor.get_stats()
            bottlenecks = self._monitor.get_bottlenecks()
            profile = self._profiler.get_status()

            # Aggiorna metriche
            self.metric_cpu.config(text=f"{stats.cpu_percent:.0f}%")
            self.metric_ram.config(text=f"{stats.ram_percent:.0f}%")
            self.metric_disk.config(text=f"{stats.disk_percent:.0f}%")
            gpu_val = f"{stats.gpu_percent:.0f}%" if stats.gpu_percent else "N/A"
            self.metric_gpu.config(text=gpu_val)
            temp_val = f"{stats.cpu_temp:.0f}°C" if stats.cpu_temp else "N/A"
            self.metric_temp.config(text=temp_val)
            self.metric_proc.config(text=str(stats.process_count))

            # Profilo
            pname = profile.get('profile_name', '--')
            self.profile_label.config(text=f"Profilo: {pname}")

            # Bottlenecks
            self.bottleneck_text.config(state=tk.NORMAL)
            self.bottleneck_text.delete(1.0, tk.END)
            if bottlenecks:
                for b in bottlenecks:
                    self.bottleneck_text.insert(tk.END, f"  ⚠ {b}\n")
            else:
                self.bottleneck_text.insert(tk.END, "  ✓ Sistema in equilibrio\n")
            self.bottleneck_text.config(state=tk.DISABLED)

            # Processi
            self.proc_text.config(state=tk.NORMAL)
            self.proc_text.delete(1.0, tk.END)
            for p in stats.top_processes:
                self.proc_text.insert(tk.END, 
                    f"  {p['name'][:30]:30s} CPU: {p['cpu']:5.1f}%  MEM: {p['mem']:5.1f}%\n")
            if not stats.top_processes:
                self.proc_text.insert(tk.END, "  (nessun processo pesante)\n")
            self.proc_text.config(state=tk.DISABLED)

        except:
            pass

        # Report system state for service diagnostics
        if self._svc_monitor and hasattr(self, '_metrics_counter'):
            self._metrics_counter += 1
            if self._metrics_counter >= 10:  # every ~30 seconds
                self._metrics_counter = 0
                try:
                    self._svc_monitor.report_system_state({
                        'cpu': stats.cpu_percent,
                        'ram': stats.ram_percent,
                        'disk': stats.disk_percent,
                        'proc': stats.process_count,
                        'profile': self._profiler.current_profile,
                    })
                except:
                    pass
        elif self._svc_monitor:
            self._metrics_counter = 0

        # Riprogramma
        if self.root:
            self.root.after(3000, self._update_loop)

    def _on_optimize(self):
        """Esegue ottimizzazione."""
        if self._optimizing:
            return
        self._optimizing = True
        self.status_label.config(text="Ottimizzazione...")
        thread = threading.Thread(target=self._do_optimize, daemon=True)
        thread.start()

    def _do_optimize(self):
        """Esegue ottimizzazione (thread)."""
        try:
            results = auto_optimize()
            if self.root:
                self.root.after(0, self._show_results, results)
                
                # Forza adattamento profilo
                result = self._profiler.adapt_system(force=True)
                if result.get('adapted'):
                    pname = result.get('profile_name', '')
                    actions = result.get('actions', {})
                    for action_name, action_data in actions.items():
                        results[action_name] = (action_data['ok'], action_data['msg'])
        except Exception as e:
            if self.root:
                self.root.after(0, lambda: self._show_error(str(e)))

    def _show_results(self, results: dict):
        """Mostra risultati ottimizzazione."""
        self.opt_text.config(state=tk.NORMAL)
        self.opt_text.delete(1.0, tk.END)
        self.opt_text.insert(tk.END, 
            f"=== Ottimizzazione {datetime.now().strftime('%H:%M:%S')} ===\n\n")
        ok_count = 0
        for action, (ok, msg) in results.items():
            icon = '✓' if ok else '✗'
            self.opt_text.insert(tk.END, f"  {icon} {action}: {msg[:80]}\n")
            if ok:
                ok_count += 1
        self.opt_text.insert(tk.END, 
            f"\n{ok_count}/{len(results)} azioni completate\n")
        self.opt_text.see(tk.END)
        self.opt_text.config(state=tk.DISABLED)
        self.status_label.config(text="Ottimizzato")
        self._optimizing = False

    def _show_error(self, error: str):
        messagebox.showerror("Errore", error)
        self.status_label.config(text="Errore")
        self._optimizing = False

    def _on_clean(self):
        """Pulisci temp."""
        from core.optimizer import clean_temp_files, clean_dns_cache
        thread = threading.Thread(target=lambda: (
            self.root.after(0, lambda: self.status_label.config(text="Pulizia...")),
            [clean_temp_files(), clean_dns_cache()],
            self.root.after(0, lambda: self.status_label.config(text="Pronto"))
        ), daemon=True)
        thread.start()

    def _on_refresh(self):
        """Forza aggiornamento immediato."""
        self._update_loop()

    def _on_close(self):
        """Chiusura."""
        self._profiler.stop()
        if self._svc_monitor:
            self._svc_monitor.stop()
        self.root.destroy()


def run_app(tray_mode: bool = False, silent: bool = False):
    app = BalancePCApp(tray_mode=tray_mode, silent=silent)


if __name__ == "__main__":
    run_app()
