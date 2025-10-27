# Dual CSV Architecture - Design Document

## 📋 Nuova Struttura Dati

### **CSV 1: produced.csv (Stock e Cisterne - GIORNALIERO)**

**Contenuto:**
- Timestamp giornaliero (es: 2025-10-01 00:00:00)
- BBT tanks: Level, Plato, Material
- FST tanks: Level, Plato, Material
- RBT tanks: Level, Plato, Material
- Truck1: Level, Plato
- Truck2: Level, Plato

**NON contiene più:**
- ~~Packed OW1~~
- ~~Packed RGB~~
- ~~Packed OW2~~
- ~~Packed KEG~~

**Frequenza:** 1 riga per giorno

---

### **CSV 2: packed_hourly.csv (Packed - ORARIO)**

**Contenuto:**
- Timestamp orario (es: 2025-10-01 08:00:00, 2025-10-01 09:00:00, ...)
- Packed OW1
- Packed RGB
- Packed OW2
- Packed KEG

**Frequenza:** 24 righe per giorno (una per ogni ora)

**Esempio:**
```csv
Timestamp,Packed_OW1,Packed_RGB,Packed_OW2,Packed_KEG
2025-10-01 00:00:00,50.5,10.2,30.1,5.0
2025-10-01 01:00:00,52.3,11.0,31.5,5.2
2025-10-01 02:00:00,48.7,9.8,29.3,4.8
...
2025-10-01 23:00:00,51.2,10.5,30.8,5.1
2025-10-02 00:00:00,49.8,10.1,30.0,4.9
...
```

---

## 🔧 Modifiche Necessarie

### **1. Aggregazione Dati Packed**

Dovremo aggregare i dati orari per giorno:

```python
# Raggruppa per giorno
packed_hourly['Date'] = pd.to_datetime(packed_hourly['Timestamp']).dt.date

# Somma per giorno
packed_daily = packed_hourly.groupby('Date').agg({
    'Packed_OW1': 'sum',
    'Packed_RGB': 'sum',
    'Packed_OW2': 'sum',
    'Packed_KEG': 'sum'
}).reset_index()
```

### **2. Join dei DataFrame**

Unire i due CSV per data:

```python
# Converti date
produced_df['Date'] = pd.to_datetime(produced_df['Time']).dt.date

# Merge
final_df = produced_df.merge(packed_daily, on='Date', how='left')
```

### **3. Calcolo Produced**

Rimane identico:
```python
packed_total = Packed_OW1 + Packed_RGB + Packed_OW2 + Packed_KEG
produced = packed_total + (cisterne/2) + (delta_stock/2)
```

---

## 🖥️ Modifiche GUI

### **Tab "Carica Dati" - Aggiornato**

```
┌────────────────────────────────────────────┐
│ 📂 CARICAMENTO DATI                        │
├────────────────────────────────────────────┤
│                                             │
│ 1. CSV Stock e Cisterne (giornaliero)      │
│ [produced.csv              ] [Sfoglia...] │
│                                             │
│ 2. CSV Packed (orario)                     │
│ [packed_hourly.csv         ] [Sfoglia...] │
│                                             │
│ [Carica e Analizza]                        │
└────────────────────────────────────────────┘
```

---

## 📊 Vantaggi Nuova Architettura

✅ **Separazione dati** - Stock/Cisterne separati da Packed
✅ **Granularità oraria** - Analisi produzione ora per ora
✅ **Flessibilità** - Possibile analizzare Packed orario separatamente
✅ **Scalabilità** - Facile aggiungere altri CSV (es: qualità, temperatura)

---

## 🔄 Workflow

1. Utente carica 2 file CSV
2. Sistema legge `produced.csv` (giornaliero)
3. Sistema legge `packed_hourly.csv` (orario)
4. Sistema aggrega Packed per giorno
5. Sistema fa merge per data
6. Calcolo Produced identico a prima
7. Dashboard mostra risultati

---

## 📝 File da Modificare

- `produced_gui.py` - 2 file picker, aggregazione
- `produced_batch.py` - Lettura 2 CSV
- `produced_pdf_report.py` - Gestione 2 CSV
- `nan_handler.py` - Gestire NaN in entrambi i CSV
- README.md - Documentare nuova struttura

---

## ⚠️ Gestione Edge Cases

1. **Date mancanti in packed_hourly:**
   - Packed per quel giorno = 0 (warning)

2. **Ore mancanti:**
   - Sommare solo ore disponibili (warning se < 24 ore)

3. **Date non corrispondenti:**
   - Mostrare warning giorni presenti solo in un CSV

4. **Formati timestamp diversi:**
   - Normalizzare tutti a datetime

---

## 🎯 Prossimi Step

1. Creare esempio `packed_hourly.csv`
2. Modificare GUI per 2 file
3. Implementare aggregazione
4. Testare con dati reali
5. Aggiornare documentazione
