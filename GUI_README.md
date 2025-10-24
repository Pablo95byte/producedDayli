# 🎨 Produced Calculator - Interfaccia Grafica (GUI)

## 🚀 Avvio Rapido

```bash
python3 produced_gui.py
```

## 📋 Funzionalità

### 1️⃣ Tab "Carica Dati"
- **Selezione CSV**: Browser per scegliere il file
- **Rilevamento automatico NaN**: Mostra statistiche valori mancanti
- **Gestione interattiva**: 4 opzioni per gestire i NaN
  - Inserimento manuale
  - Valore predefinito
  - Forward-fill
  - Procedi senza modifiche
- **Info dati**: Visualizza righe, colonne, NaN rilevati

### 2️⃣ Tab "Dashboard"
- **Statistiche generali**:
  - Giorni elaborati
  - Produced totale (hl)
  - Produced medio (hl/giorno)
  - Packed totale (hl)
  - Cisterne totale (hl)

- **Tabella risultati dettagliati**:
  - Data
  - Produced
  - Packed
  - Cisterne
  - Stock Iniziale/Finale
  - Delta Stock

### 3️⃣ Tab "Grafici"
*In sviluppo*
- Produced giornaliero
- Produced settimanale
- Componenti stacked
- Evoluzione stock
- Tank specifico

### 4️⃣ Tab "Report PDF"
*Da completare*
- Opzioni personalizzabili
- Log generazione

### 5️⃣ Tab "Impostazioni"
- Visualizzazione mapping materiali
- Material ID → Grado Standard

## 🎯 Menu

### File
- **Apri CSV** (Ctrl+O): Carica file CSV
- **Esporta Risultati CSV**: Salva risultati
- **Esporta Risultati Excel**: Salva in formato .xlsx
- **Esci** (Ctrl+Q): Chiude applicazione

### Strumenti
- **Ricalcola Tutto**: Rielabora tutti i dati
- **Test Formule**: Testa calc_hl_std e plato_to_volumetric
- **Gestisci NaN**: Riapre dialog gestione NaN

### Aiuto
- **Documentazione**: Info sull'uso
- **About**: Informazioni app

## 💻 Requisiti

- Python 3.7+
- pandas
- tkinter (incluso in Python)

**Opzionale per Excel export:**
```bash
pip install openpyxl
```

## 🔧 Come Usare

1. **Avvia l'applicazione**
   ```bash
   python3 produced_gui.py
   ```

2. **Carica CSV**
   - Click "Sfoglia..." o Menu → File → Apri CSV
   - Seleziona `produced.csv`

3. **Gestisci NaN** (se presenti)
   - Scegli come gestire valori mancanti
   - Opzione consigliata: Forward-fill

4. **Visualizza Risultati**
   - Vai al tab "Dashboard"
   - Controlla statistiche e tabella

5. **Esporta** (opzionale)
   - Menu → File → Esporta CSV/Excel

## 🎨 Screenshot

```
┌─────────────────────────────────────────────────────┐
│ File  Strumenti  Aiuto                              │
├─────────────────────────────────────────────────────┤
│ [ Carica Dati ] [ Dashboard ] [ Grafici ] ...      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Statistiche Generali                               │
│  ┌────────────────────────────────────────────┐    │
│  │ Giorni:              31                    │    │
│  │ Produced Totale:     152,431.50 hl        │    │
│  │ Produced Medio:      4,917.15 hl/giorno   │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  Risultati Dettagliati                              │
│  ┌────────────────────────────────────────────┐    │
│  │ Data       │Produced│Packed│Cisterne│...   │    │
│  ├────────────┼────────┼──────┼─────────┼──   │    │
│  │ 2025-10-01 │4,823.12│3,200 │1,450.50 │...  │    │
│  │ 2025-10-02 │5,102.45│3,450 │1,523.20 │...  │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
├─────────────────────────────────────────────────────┤
│ Pronto                                      [====] │
└─────────────────────────────────────────────────────┘
```

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install pandas
```

**"Errore durante esportazione Excel"**
```bash
pip install openpyxl
```

**"CSV non caricato"**
- Verifica che il file esista
- Controlla che sia un CSV valido
- Prova ad aprirlo con un editor di testo

## 🚧 Sviluppo Futuro

- [ ] Integrazione matplotlib per grafici
- [ ] Generazione PDF da GUI
- [ ] Test formule interattivo
- [ ] Filtri e ricerca nella tabella
- [ ] Export grafico singolo
- [ ] Temi chiari/scuri
- [ ] Multi-lingua (IT/EN)

## 📝 Note

- L'interfaccia usa **tkinter** (nessuna installazione extra)
- I calcoli usano gli stessi algoritmi della versione CLI
- La gestione NaN è identica al modulo `nan_handler.py`
- Tutti i dati rimangono locali (nessuna connessione internet)

## 🤝 Contributi

Questo è un progetto interno. Per suggerimenti o bug report, contatta lo sviluppatore.

---

**Versione:** 2.0
**Ultimo aggiornamento:** 2025-10-24
**Developed with:** Python + tkinter + pandas
