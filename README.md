# Produced Calculator - Dashboard Assemini

Sistema di calcolo **Produced giornaliero** con interfaccia grafica interattiva per l'analisi della produzione birra.

---

## 🚀 Quick Start

```bash
# Installa dipendenze
pip install pandas matplotlib colorama

# Avvia GUI
python produced_gui.py
```

---

## 📊 Formula Produced

```
Produced = Packed + (Cisterne/2) + (ΔStock/2)
```

Dove:
- **Packed** = OW1 + RGB + OW2 + KEG
- **Cisterne** = Truck1 + Truck2 (hl standard)
- **ΔStock** = Stock Finale - Stock Iniziale (BBT + FST)

---

## 📁 Struttura Progetto

```
producedDayli/
│
├── README.md                    # Documentazione
├── .gitignore                   # Git configuration
├── produced.csv                 # Dati di input
│
├── produced_gui.py              # GUI principale ⭐
├── produced_pdf_report.py       # Generazione report PDF
├── produced_batch.py            # Processing batch (senza GUI)
├── nan_handler.py               # Gestione interattiva valori NaN
│
├── archive/                     # File obsoleti/backup
│   ├── produced_calculator.py
│   ├── produced_grafici.py
│   └── debug_fst241.py
│
└── report/                      # Report PDF generati (auto-creata)
    └── report_produced_YYYY-MM-DD_PA.pdf
```

**File Core (4):**
| File | Scopo | Dimensione |
|------|-------|------------|
| `produced_gui.py` | GUI principale con 5 tab | ~37 KB |
| `produced_pdf_report.py` | Generazione PDF con grafici | ~32 KB |
| `produced_batch.py` | Processing batch senza GUI | ~11 KB |
| `nan_handler.py` | Gestione interattiva NaN | ~7 KB |

---

## 🎨 Funzionalità GUI

### 1️⃣ Tab "Carica Dati"
- Selezione CSV con browser
- Rilevamento automatico valori NaN
- Gestione interattiva NaN (4 opzioni):
  - Inserimento manuale
  - Valore predefinito
  - Forward-fill
  - Procedi senza modifiche

### 2️⃣ Tab "Dashboard"
**Statistiche generali:**
- Giorni elaborati
- Produced totale/medio (hl)
- Packed totale (hl)
- Cisterne totale (hl)

**Tabella risultati:**
- Data, Produced, Packed, Cisterne
- Stock Iniziale/Finale
- Delta Stock

### 3️⃣ Tab "Grafici"
**4 grafici matplotlib interattivi:**

1. **Produced Giornaliero** - Barre giornaliere con valori annotati
2. **Produced Settimanale** - Aggregato per settimana (2025-W01, etc.)
3. **Componenti Stacked** - Breakdown: Packed + Cisterne/2 + ΔStock/2
4. **Evoluzione Stock** - Trend Stock Iniziale vs Finale

**Toolbar inclusa:**
- Home, Pan, Zoom, Save PNG
- Navigazione cronologia

### 4️⃣ Tab "Report PDF"
- Generazione report completo con grafici
- Opzioni personalizzabili:
  - Includi grafici principali
  - Includi dettagli tank (BBT/FST)
  - Includi analisi settimanali
- Log generazione in tempo reale
- Salvataggio automatico in `report/report_produced_YYYY-MM-DD_PA.pdf`

### 5️⃣ Tab "Impostazioni"
- Visualizzazione mapping materiali
- Material ID → Grado Standard volumetrico

---

## 🔧 Utilizzo

### Metodo 1: GUI (consigliato)

```bash
python produced_gui.py
```

1. Click "Sfoglia..." e seleziona `produced.csv`
2. Gestisci eventuali NaN
3. Visualizza risultati in Dashboard
4. Esplora grafici interattivi
5. Genera report PDF

### Metodo 2: Batch Processing

```bash
python produced_batch.py
```

Elabora il CSV e esporta risultati senza GUI.

---

## 📄 Report PDF

I report vengono salvati automaticamente in:
```
report/report_produced_2025-10-27_PA.pdf
```

**Contenuto report:**
- Pagina titolo con statistiche generali
- Grafici Produced giornaliero/settimanale
- Analisi settimanali dettagliate
- Grafici per ogni tank BBT/FST
- Grafici truck (cisterne)
- Statistiche RBT

---

## 💻 Requisiti

**Python 3.8+**

**Dipendenze necessarie:**
```bash
pip install pandas matplotlib colorama
```

**Opzionale (per export Excel):**
```bash
pip install openpyxl
```

**Incluso in Python:**
- tkinter (GUI)

---

## 🎯 Menu GUI

### File
- **Apri CSV** (Ctrl+O)
- **Esporta CSV/Excel**
- **Esci** (Ctrl+Q)

### Strumenti
- **Ricalcola Tutto**
- **Test Formule**
- **Gestisci NaN**

### Aiuto
- **Documentazione**
- **About**

---

## 📐 Calcolo hl Standard

### Formula:
```python
hl_std = (volume_hl × grado_volumetrico) / grado_standard
```

### Grado Volumetrico (da Plato):
```python
grado_v = ((0.0000188792 × P + 0.003646886) × P + 1.001077) × P - 0.01223565
```

### Mapping Materiali:
| Material ID | Grado Standard |
|-------------|----------------|
| 0 | 0.00 (vuoto) |
| 1, 2, 7, 10, 32, 36 | 11.03 |
| 3, 8 | 11.57 |
| 9, 21, 22, 28 | 11.68 |

---

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install pandas matplotlib
```

**"Errore esportazione Excel"**
```bash
pip install openpyxl
```

**"Tank ritorna 0 hl standard con livello alto"**
- Verifica il campo Material nel CSV
- Material=0 significa "tank vuoto"
- Correggi Material con il valore appropriato (1-36)

**"CSV non caricato"**
- Verifica percorso file
- Controlla che sia CSV valido
- Verifica encoding (UTF-8)

---

## 📦 Archivio

La cartella `archive/` contiene versioni precedenti obsolete:
- `produced_calculator.py` - Vecchia versione CLI interattiva
- `produced_grafici.py` - Generazione grafici standalone
- `debug_fst241.py` - Script debug temporaneo

Questi file non sono più necessari ma sono mantenuti per riferimento storico.

---

## 🔒 Gestione NaN

Il sistema **NON applica più valori di default automatici**.

Quando rileva NaN nel CSV, chiede all'utente come gestirli:
1. **Inserimento manuale** - Inserisci valore per ogni NaN
2. **Valore predefinito** - Usa stesso valore per tutti i NaN di una colonna
3. **Forward-fill** - Propaga ultimo valore valido
4. **Procedi senza modifiche** - Lascia NaN (può causare errori)

---

## 📝 Note Tecniche

- Calcoli identici tra GUI e batch mode
- Tutti i dati rimangono locali (no internet)
- Material=0 nel CSV indica tank vuoto/nessun materiale
- La formula ΔStock/2 riflette il contributo effettivo allo stock
- Report PDF usa matplotlib con backend PdfPages

---

## 🆕 Changelog

### v2.0 (2025-10-27)
- ✅ GUI completa con 5 tab
- ✅ Grafici matplotlib interattivi embedded
- ✅ Generazione PDF da GUI
- ✅ Report salvati in cartella dedicata `report/`
- ✅ Nome file con data: `report_produced_YYYY-MM-DD_PA.pdf`
- ✅ Riorganizzazione progetto minimale
- ✅ Gestione NaN user-driven (no default automatici)

### v1.0 (2025-10-01)
- Versione CLI iniziale
- Calcolo produced giornaliero
- Export CSV/Excel

---

## 👨‍💻 Sviluppo

**Tecnologie:**
- Python 3
- tkinter (GUI)
- pandas (data processing)
- matplotlib (grafici e PDF)
- colorama (output colorato CLI)

**Struttura codice:**
- GUI: Classe `ProducedGUI` con pattern MVC
- PDF: Classe `ReportPDFProduced` modulare
- Batch: Funzioni standalone

---

## 📧 Supporto

Progetto interno Heineken - Dashboard Assemini

Per supporto o bug report, contattare il team di sviluppo.

---

**Versione:** 2.0
**Ultimo aggiornamento:** 27 Ottobre 2025
**Developed with Python + tkinter + pandas + matplotlib**
