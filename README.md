# BalancePC

> **Il tuo PC si adatta a te, non il contrario.**

BalancePC monitora come usi il PC e ottimizza CPU, RAM, disco e piano energia di conseguenza. Senza chiederti niente. Senza pubblicità.

Scarica il `.exe` e via.

```
Scarica da GitHub → Doppio click su --optimize → 8.8GB liberati in 10 secondi
```

## Perché BalancePC?

| CCleaner / System Mechanic / Razer Cortex | BalancePC |
|---|---|
| Versione "free" fa quasi niente | **100% gratuito**, tutto funziona |
| Pieno di pubblicità e offerte | **Zero pubblicità, zero popup** |
| Ottimizzazioni generiche | **Si adatta a COSA stai facendo** (gaming, lavoro, sviluppo, idle) |
| 50MB+ di installer | **7MB**, un exe |

## Scarica

| Piattaforma | Link |
|---|---|
| **Windows 10/11 64bit** | [`BalancePC.exe`](https://github.com/Sampranot/BalancePC/releases) (singolo eseguibile) |
| **Python (tutte le versioni)** | `pip install -r requirements.txt && python main.py` |

## Come si usa

```cmd
BalancePC.exe --optimize    Pulisce e ottimizza SUBITO
BalancePC.exe --monitor     Mostra CPU/RAM/DISK/TEMP in tempo reale
BalancePC.exe               Avvia interfaccia grafica
```

### Esempio reale

```
=== BalancePC — Ottimizzazione ===
  ✅ Puliti 8.8GB di file temporanei
  ✅ Cache DNS pulita
  ✅ Cache Windows Update pulita
  ✅ Cestino svuotato
  ✅ Piano energia: Alte prestazioni
  ✅ Processi pesanti terminati

Risultato: 8.8GB liberati, sistema più reattivo.
```

## Cosa fa esattamente

### Quando esegui `--optimize`

| Azione | Cosa fa |
|---|---|
| `clean_temp` | Svuota TEMP, Prefetch, cache browser, log di Windows |
| `clean_dns` | Svuota cache DNS (risolve rallentamenti navigazione) |
| `clean_wu_cache` | Pulisce cache Windows Update (può liberare GB) |
| `empty_recycle` | Svuota cestino |
| `power_plan` | Imposta piano energia adatto al tuo utilizzo |
| `kill_heavy` | Termina processi che consumano troppa CPU (senza mai toccare processi di sistema) |
| *(in arrivo)* TRIM manuale, restore point automatico |

### Monitoraggio in tempo reale

```cmd
BalancePC.exe --monitor
CPU:  12.3% | RAM:  45.2% | DISK:  8.1% | TEMP: 42°C | PROCESSI:  189
```

### Riconoscimento automatico profili

| Se stai... | Il profilo è... | Cosa fa |
|---|---|---|
| Giocando | **Gaming** | Massime prestazioni GPU, minimizza background |
| Lavorando | **Work** | Piano bilanciato, priorità CPU alle app attive |
| Programma | **Development** | Alte prestazioni, mantiene IDE/tools aperti |
| Guardando video | **Streaming** | Bilanciato, priorità multimediale |
| Non tocchi niente | **Idle** | Risparmio energetico |

Tutto automatico. Senza config.

## Compatibilità

- ✅ Windows 10 (tutte le build)
- ✅ Windows 11 (tutte le build + 24H2)
- ✅ Supporto multi-lingua (controllo SYSTEM locale-safe)
- ✅ Funziona anche senza admin (azioni limitate, sicuro)
- ✅ Rileva e gestisce piani energia assenti/nascosti

## Build da sorgente

```cmd
git clone https://github.com/Sampranot/BalancePC
cd BalancePC
pip install -r requirements.txt
python main.py --optimize
```

## Roadmap

- [x] Pulizia temp, cache, prefetch, DNS, WU cache, cestino
- [x] Cambio piano energia adattivo (con verifica GUID)
- [x] Gestione processi pesanti (locale-safe, no BSOD)
- [x] Profiler automatico (gaming/work/dev/idle/streaming)
- [x] Demone background (monitoraggio e ottimizzazione continua)
- [x] Eseguibile standalone (no Python)
- [ ] Integrazione con DriverPulse per aggiornamento driver
- [ ] Restore point automatico prima di ottimizzazioni distruttive

## Filosofia

- **Adattivo**. Si adatta al tuo utilizzo, non viceversa.
- **Sicuro**. Non tocca mai processi di sistema, qualunque sia la lingua di Windows.
- **Leggero**. Un exe da 7MB. Niente bloat, niente servizi in background (se non vuoi).

---

*Creato da Samuele. BalancePC è software libero.*
