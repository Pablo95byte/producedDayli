# Produced Calculator - Dashboard Assemini

Sistema di calcolo **Produced giornaliero** con interfaccia grafica interattiva per l'analisi della produzione birra.

**✅ PORTABILE** - Funziona su qualsiasi PC senza path hardcoded!

---

## 🚀 Quick Start

```bash
# 1. Installa dipendenze
pip install pandas matplotlib colorama openpyxl numpy

# 2. Metti i 3 CSV nella stessa cartella degli script Python

# 3. Avvia GUI
python produced_gui.py
```

📖 **Per istruzioni dettagliate, leggi [INSTALL.md](INSTALL.md)**

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

## 📊 Architettura Triple CSV

Il sistema utilizza **3 file CSV separati** per massima flessibilità:

### **CSV 1: Stock (giornaliero)**
Contiene:
- Timestamp giornaliero (es: 2025-10-01 00:00:00)
- Livelli, Plato e Material per tutti i tank (BBT, FST, RBT)

⚠️ **IMPORTANTE:** Solo tanks - NO Packed, NO Cisterne

### **CSV 2: Packed (orario) - OBBLIGATORIO**
Contiene:
- Timestamp orario (es: 2025-10-01 08:00:00, 09:00:00, ...)
- Packed_OW1, Packed_RGB, Packed_OW2, Packed_KEG (hl prodotti in quell'ora)

**Frequenza:** 24 righe per giorno (una per ogni ora)
**Aggregazione:** SOMMA → totale giornaliero

### **CSV 3: Cisterne (orario) - OBBLIGATORIO**
Contiene:
- Timestamp orario (es: 2025-10-01 08:00:00, 09:00:00, ...)
- Truck1_Level, Truck1_Plato, Truck2_Level, Truck2_Plato

**Frequenza:** 24 righe per giorno (una per ogni ora)
**Aggregazione:** MEDIA → media giornaliera

**Esempio `packed_hourly.csv`:**
```csv
Timestamp,Packed_OW1,Packed_RGB,Packed_OW2,Packed_KEG
2025-10-01 00:00:00,50.5,0.0,30.1,0.0
2025-10-01 01:00:00,52.3,0.0,31.5,0.0
...
2025-10-01 23:00:00,51.4,0.0,38.0,0.0
```

Il sistema **aggrega automaticamente** i dati orari in totali giornalieri e li **mergia** con lo Stock per data.

---

## 📁 Struttura Progetto

```
producedDayli/
│
├── README.md                    # Documentazione
├── DUAL_CSV_DESIGN.md           # Architettura Dual CSV
├── .gitignore                   # Git configuration
│
├── produced_stock_only.csv      # CSV 1: Stock/Cisterne (giornaliero)
├── packed_hourly.csv            # CSV 2: Packed (orario) ⚠️ OBBLIGATORIO
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

### 1️⃣ Tab "Carica Dati" (Triple CSV Mode)

**Caricamento 3 file CSV:**

1. **CSV Stock (giornaliero)** ⚠️ OBBLIGATORIO
   - Seleziona file con browser
   - Contiene livelli tanks BBT/FST/RBT, plato, material

2. **CSV Packed (orario)** ⚠️ OBBLIGATORIO
   - Seleziona file con browser
   - Contiene dati Packed ora per ora (OW1, RGB, OW2, KEG)

3. **CSV Cisterne (orario)** ⚠️ OBBLIGATORIO
   - Seleziona file con browser
   - Contiene livelli Truck1/Truck2 ora per ora

**Dopo caricamento:**
- Aggregazione automatica Packed orario → giornaliero (SOMMA)
- Aggregazione automatica Cisterne orario → giornaliero (MEDIA)
- Merge automatico dei 3 CSV per data
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
**4 grafici matplotlib interattivi con tooltip hover:**

1. **Produced Giornaliero** - Barre giornaliere
   - 🖱️ Passa il mouse su una barra per vedere data e valore esatto

2. **Produced Settimanale** - Aggregato per settimana (2025-W01, etc.)
   - Valori totali annotati sulle barre
   - 🖱️ Hover per vedere: Totale, Media giornaliera, N° giorni

3. **Componenti Stacked** - Breakdown: Packed + Cisterne/2 + ΔStock/2
   - 🖱️ Hover per vedere Produced totale del giorno

4. **Evoluzione Stock** - Trend Stock Iniziale vs Finale
   - Linee con marker per visualizzare l'andamento

**Tooltip interattivi:**
- ✨ Passa il mouse sopra le barre per vedere i valori esatti
- Box giallo/verde con dettagli completi
- Nessun clic necessario, solo hover!

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

### Dual CSV - Troubleshooting

**"Seleziona il file CSV Packed (orario)"**
- Il CSV Packed è **OBBLIGATORIO** per calcolare Produced
- Senza dati Packed il calcolo è impossibile
- Verifica di avere il file packed_hourly.csv

**"Date non corrispondenti tra Stock e Packed"**
- Il sistema esegue left join su Stock
- Date presenti solo in Packed vengono ignorate
- Date in Stock ma non in Packed avranno Packed=0
- Verifica che entrambi i CSV coprano lo stesso periodo

**"Ore mancanti nel CSV Packed"**
- Il sistema somma solo le ore disponibili
- Se hai < 24 ore per un giorno, il totale sarà parziale
- Verifica di avere 24 righe per ogni giorno

**"Come creare packed_hourly.csv dai miei dati?"**
- Formato richiesto: Timestamp,Packed_OW1,Packed_RGB,Packed_OW2,Packed_KEG
- Timestamp formato: YYYY-MM-DD HH:MM:SS (es: 2025-10-01 08:00:00)
- 24 righe per giorno, una per ogni ora (00:00 a 23:00)
- Valori in ettolitri (hl)

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

## 🌍 Portabilità - Funziona su Qualsiasi PC!

### ✅ Nessun Path Hardcoded

Il software è completamente **portabile**:
- Non servono percorsi assoluti Windows specifici
- Tutto si basa sulla **cartella corrente** dello script
- Output automaticamente in `./output/`

### 📂 Come Usare su un Nuovo PC

1. **Copia l'intera cartella** del progetto sul PC
2. **Metti i 3 CSV** nella stessa cartella degli script `.py`
3. **Avvia** `produced_gui.py` (doppio click o da terminale)
4. Fatto! 🎉

### 🔍 Auto-Detection dei File

Il sistema cerca automaticamente i CSV se non li trova:
- Cerca file con `stock` nel nome → CSV Stock
- Cerca file con `packed` nel nome → CSV Packed
- Cerca file con `cisterne` nel nome → CSV Cisterne

**Non servono configurazioni!**

### 📊 Output Automatico

Tutti gli output vengono salvati in:
```
./output/
  ├── produced_results_batch.csv
  ├── produced_results_batch.xlsx
  └── report/
      └── report_produced_YYYY-MM-DD_PA.pdf
```

La cartella `output/` viene **creata automaticamente** nella stessa directory degli script.

### 🛠️ Guida Installazione Completa

Per istruzioni dettagliate su come installare e usare il software su qualsiasi PC, leggi:

📖 **[INSTALL.md](INSTALL.md)** - Guida passo-passo con troubleshooting

---

## 📧 Supporto

Progetto interno Heineken - Dashboard Assemini

Per supporto o bug report, contattare il team di sviluppo.

---

**Versione:** 3.0 - Triple CSV Architecture
**Ultimo aggiornamento:** 29 Ottobre 2025
**Developed with Python + tkinter + pandas + matplotlib**
✅ **Portabile** - Funziona su Windows, Linux, macOS
