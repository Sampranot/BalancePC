# BalancePC

Mantiene il PC in equilibrio in base all'utilizzo reale.  
Adatta CPU, RAM, disco e piano energia automaticamente.  
Niente bloat, niente pubblicità.

## Come funziona

1. **Monitoraggio** — raccoglie metriche in tempo reale (CPU, RAM, disco, GPU, temperatura)
2. **Profilo adattivo** — riconosce cosa stai facendo (gaming, lavoro, sviluppo, idle)
3. **Ottimizzazione** — applica le impostazioni migliori per il tuo utilizzo corrente
4. **Demone** — opzionalmente, resta in background e ottimizza continuamente

## Utilizzo

```
python main.py              Avvia interfaccia grafica
python main.py --monitor    Monitoraggio in tempo reale da terminale
python main.py --optimize   Ottimizzazione immediata
python main.py --daemon     Avvia come servizio background
python main.py --tray       Avvia in system tray
```

## Installazione

```bash
pip install -r requirements.txt
python main.py
```

## Profili rilevati automaticamente

| Profilo | Cosa fa |
|---|---|
| Gaming | Massime prestazioni GPU, minimizza background |
| Lavoro | Piano bilanciato, priorità CPU |
| Sviluppo | Alte prestazioni, mantiene strumenti aperti |
| Streaming | Bilanciato, priorità multimediale |
| Riposo | Risparmio energetico |

## Requisiti

- Windows 10 o 11
- Python 3.8+

## Progetti correlati

- **DriverPulse** — mantiene i driver sempre aggiornati

---

*BalancePC — Solo utility. Nessun bloat. Nessuna pubblicità.*
