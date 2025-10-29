# 📦 GUIDA INSTALLAZIONE - Produced Calculator

Guida completa per installare e usare Produced Calculator su **qualsiasi PC Windows**.

---

## ✅ Requisiti di Sistema

- **Windows** 10/11 (o Linux/Mac)
- **Python 3.8+** installato
- Connessione internet (solo per installazione iniziale)

---

## 🚀 Installazione Rapida

### 1️⃣ Scarica il Codice

Scarica tutto il repository in una cartella sul tuo PC, ad esempio:
```
C:\ProducedCalculator\
```

Oppure clona il repository:
```bash
git clone https://github.com/Pablo95byte/producedDayli.git
cd producedDayli
```

### 2️⃣ Installa le Dipendenze Python

Apri il **Prompt dei comandi** (CMD) nella cartella del progetto e esegui:

```bash
pip install pandas numpy matplotlib colorama openpyxl
```

Oppure usa il file requirements (se disponibile):
```bash
pip install -r requirements.txt
```

### 3️⃣ Prepara i File CSV

Metti i tuoi 3 file CSV nella **stessa cartella** degli script Python:

```
C:\ProducedCalculator\
  ├── produced_gui.py          ← Script GUI principale
  ├── produced_batch.py        ← Script batch
  ├── produced_pdf_report.py   ← Script PDF
  ├── produced_stock_only.csv  ← Il tuo CSV Stock (giornaliero)
  ├── packed_hourly.csv        ← Il tuo CSV Packed (orario)
  └── cisterne_hourly.csv      ← Il tuo CSV Cisterne (orario)
```

**IMPORTANTE**: I file CSV devono chiamarsi esattamente così, oppure contenere nel nome:
- `stock` (per il CSV Stock)
- `packed` (per il CSV Packed)
- `cisterne` (per il CSV Cisterne)

Il programma li troverà automaticamente!

---

## 🎯 Come Usare

### Opzione 1: GUI (Interfaccia Grafica) ⭐ CONSIGLIATO

Doppio click su `produced_gui.py` oppure esegui:

```bash
python produced_gui.py
```

**Cosa fare:**
1. Si aprirà una finestra grafica
2. Clicca sui 3 pulsanti "Sfoglia" per selezionare i tuoi CSV
3. Clicca "Carica e Calcola"
4. Usa i tab per vedere:
   - 📊 **Grafici**: Visualizzazioni interattive
   - 📄 **Tabella**: Dati calcolati
   - 📈 **Analisi Giornaliera**: Report dettagliato
   - 📑 **PDF**: Genera report PDF completo

### Opzione 2: Batch Processing (Senza GUI)

Per elaborare tutti i giorni velocemente:

```bash
python produced_batch.py
```

**Output:**
- `output/produced_results_batch.csv` - Risultati in CSV
- `output/produced_results_batch.xlsx` - Risultati in Excel

### Opzione 3: PDF Report Diretto

Per generare solo il PDF:

```bash
python produced_pdf_report.py
```

**Output:**
- `output/report/report_produced_YYYY-MM-DD_PA.pdf`

---

## 📂 Struttura Cartelle Output

Il programma crea automaticamente:

```
C:\ProducedCalculator\
  └── output\
      ├── produced_results_batch.csv
      ├── produced_results_batch.xlsx
      └── report\
          └── report_produced_2025-10-29_PA.pdf
```

**Tutti gli output vengono salvati in `output/`** - non servono path hardcoded!

---

## 🛠️ Risoluzione Problemi

### ❌ "Modulo pandas non trovato"
**Soluzione**: Installa le dipendenze
```bash
pip install pandas numpy matplotlib colorama openpyxl
```

### ❌ "CSV non trovato"
**Soluzione**:
1. Controlla che i 3 CSV siano nella stessa cartella degli script
2. Verifica i nomi dei file (devono contenere `stock`, `packed`, `cisterne`)
3. Nella GUI, usa i pulsanti "Sfoglia" per selezionarli manualmente

### ❌ "Errore TIMESTAMP column"
**Soluzione**: Il tuo CSV Packed/Cisterne deve avere una colonna con il timestamp.
Nomi supportati: `Time`, `Timestamp`, `DateTime`, `Date`

### ❌ La finestra GUI non si apre
**Soluzione**:
```bash
pip install tk
```
Oppure reinstalla Python con supporto Tkinter

### ❌ "Permission denied" quando salva il PDF
**Soluzione**: Chiudi il file PDF se è aperto in Adobe/Acrobat

---

## 📊 Formato CSV Richiesto

### CSV Stock (giornaliero)
```csv
Time,BBT111 Level,BBT 111 Average Plato,BBT111 Material,...
2025-10-01,1234.5,11.57,8,...
2025-10-02,1189.3,11.60,8,...
```

### CSV Packed (orario)
```csv
Time,Packed_OW1,Packed_RGB,Packed_OW2,Packed_KEG
2025-10-01 00:00:00,10.5,8.3,12.1,5.2
2025-10-01 01:00:00,11.2,9.1,11.8,4.9
...
```
**Aggregazione**: SOMMA delle 24 ore → totale giornaliero

### CSV Cisterne (orario)
```csv
Time,Truck1_Level,Truck1_Plato,Truck2_Level,Truck2_Plato
2025-10-01 00:00:00,120.5,11.21,85.3,11.15
2025-10-01 01:00:00,125.3,11.23,90.1,11.18
...
```
**Aggregazione**: MEDIA delle 24 ore → media giornaliera

---

## 🎓 Architettura Triple CSV

Il sistema richiede **3 file separati**:

1. **Stock CSV** (giornaliero): Dati tanks BBT/FST/RBT
2. **Packed CSV** (orario): Produzione OW1/RGB/OW2/KEG
3. **Cisterne CSV** (orario): Livello e Plato Truck1/Truck2

Il programma aggrega automaticamente i dati orari in dati giornalieri e li mergia per calcolare il **Produced**.

---

## 💡 Suggerimenti

✅ **Non modificare** i nomi degli script `.py`
✅ **Metti sempre** i 3 CSV nella cartella del programma
✅ **Usa la GUI** per la prima volta - è più facile!
✅ **Controlla** il tab "Analisi Giornaliera" per vedere i dettagli
✅ **Salva** i risultati batch in Excel per analisi ulteriori

---

## 📞 Supporto

Per problemi o domande:
- Controlla questa guida INSTALL.md
- Verifica i formati CSV sopra
- Assicurati di avere Python 3.8+ installato
- Verifica che tutte le dipendenze siano installate

---

**Versione**: Triple CSV Architecture
**Data**: Ottobre 2025
**Compatibilità**: Windows, Linux, macOS
