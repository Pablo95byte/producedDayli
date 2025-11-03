#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCED CALCULATOR - Versione Batch per Test Rapidi
Esporta tutti i risultati senza GUI
"""

import pandas as pd
import sys
import os
from pathlib import Path
from nan_handler import handle_missing_values

# Rilevamento sistema operativo e percorsi
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

# Determina il percorso della cartella di lavoro
# Usa la cartella corrente come default (portabile su qualsiasi PC)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

# Path di default (verranno cercati automaticamente se non esistono)
CSV_STOCK_PATH = os.path.join(SCRIPT_DIR, 'produced_stock_only.csv')
CSV_PACKED_PATH = os.path.join(SCRIPT_DIR, 'packed_hourly.csv')
CSV_CISTERNE_PATH = os.path.join(SCRIPT_DIR, 'cisterne_hourly.csv')

# Crea cartella output se non esiste
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Se i CSV non esistono, prova a trovarli nella cartella corrente
if not os.path.exists(CSV_STOCK_PATH):
    print(f"⚠️ CSV Stock non trovato in: {CSV_STOCK_PATH}")
    for file in os.listdir('.'):
        if 'stock' in file.lower() and file.endswith('.csv'):
            CSV_STOCK_PATH = os.path.join('.', file)
            print(f"   Trovato: {CSV_STOCK_PATH}")
            break
        elif file == 'produced.csv':
            CSV_STOCK_PATH = os.path.join('.', file)
            print(f"   Trovato: {CSV_STOCK_PATH}")
            break

if not os.path.exists(CSV_PACKED_PATH):
    print(f"⚠️ CSV Packed non trovato in: {CSV_PACKED_PATH}")
    for file in os.listdir('.'):
        if 'packed' in file.lower() and file.endswith('.csv'):
            CSV_PACKED_PATH = os.path.join('.', file)
            print(f"   Trovato: {CSV_PACKED_PATH}")
            break

if not os.path.exists(CSV_CISTERNE_PATH):
    print(f"⚠️ CSV Cisterne non trovato in: {CSV_CISTERNE_PATH}")
    for file in os.listdir('.'):
        if 'cisterne' in file.lower() and file.endswith('.csv'):
            CSV_CISTERNE_PATH = os.path.join('.', file)
            print(f"   Trovato: {CSV_CISTERNE_PATH}")
            break

# Mapping dei gradi volumetrici standard
MATERIAL_MAPPING = {
    0: 0, 1: 11.03, 2: 11.03, 3: 11.57, 7: 11.03, 8: 11.57, 
    9: 11.68, 10: 11.03, 21: 11.68, 22: 11.68, 28: 11.68, 32: 11.03, 36: 11.03
}

BBT_TANKS = [111, 112, 121, 132, 211, 212, 221, 222, 231, 232, 241, 242, 251, 252]
FST_TANKS = [111, 112, 121, 122, 131, 132, 141, 142, 151, 152, 161, 171, 172, 
             211, 212, 221, 222, 231, 232, 241, 242, 243]
RBT_TANKS = [251, 252]

def plato_to_volumetric(plato):
    if plato == 0:
        return 0
    plato = float(plato)
    grado_v = ((0.0000188792 * plato + 0.003646886) * plato + 1.001077) * plato - 0.01223565
    return grado_v

def calc_hl_std(volume_hl, plato, material):
    try:
        volume_hl = float(volume_hl)
        plato = float(plato)
        material = int(float(material))
    except:
        raise ValueError(f"Valori non validi: volume_hl={volume_hl}, plato={plato}, material={material}")

    if volume_hl == 0 or plato == 0:
        return 0

    grado_vol = plato_to_volumetric(plato)
    if grado_vol == 0:
        return 0

    # Material è valido, usa il mapping
    if material not in MATERIAL_MAPPING:
        raise ValueError(f"Material {material} non trovato nel mapping")

    grado_std = MATERIAL_MAPPING[material]
    if grado_std == 0:
        # Material con grado_std = 0 nel mapping ritorna 0
        return 0

    hl_std = (volume_hl * grado_vol) / grado_std
    return hl_std

def aggregate_packed_hourly(df_packed):
    """Aggrega i dati Packed orari in dati giornalieri"""
    # Trova la colonna temporale
    time_col = None
    possible_time_cols = ['Timestamp', 'Time', 'DateTime', 'Date', 'timestamp', 'time', 'datetime']

    for col in possible_time_cols:
        if col in df_packed.columns:
            time_col = col
            break

    if time_col is None:
        time_col = df_packed.columns[0]
        print(f"⚠️ Colonna temporale non trovata, uso: {time_col}")

    # Converti timestamp a datetime
    try:
        df_packed[time_col] = pd.to_datetime(df_packed[time_col])
    except Exception as e:
        raise ValueError(
            f"❌ Errore conversione timestamp nella colonna '{time_col}'!\n"
            f"Formato richiesto: YYYY-MM-DD HH:MM:SS\n"
            f"Errore: {str(e)}"
        )

    # Estrai solo la data (senza ora)
    df_packed['Date'] = df_packed[time_col].dt.date

    # Trova colonne Packed
    packed_cols_map = {}
    for orig_name, target_name in [
        ('Packed_OW1', 'Packed OW1'),
        ('Packed_RGB', 'Packed RGB'),
        ('Packed_OW2', 'Packed OW2'),
        ('Packed_KEG', 'Packed KEG'),
        ('OW1', 'Packed OW1'),
        ('RGB', 'Packed RGB'),
        ('OW2', 'Packed OW2'),
        ('KEG', 'Packed KEG')
    ]:
        if orig_name in df_packed.columns:
            packed_cols_map[orig_name] = target_name

    if not packed_cols_map:
        raise ValueError(
            f"❌ Colonne Packed non trovate!\n"
            f"Richieste: Packed_OW1, Packed_RGB, Packed_OW2, Packed_KEG\n"
            f"Trovate: {', '.join(df_packed.columns)}"
        )

    # Aggrega per giorno (somma di tutte le ore)
    agg_dict = {col: 'sum' for col in packed_cols_map.keys()}
    packed_daily = df_packed.groupby('Date').agg(agg_dict).reset_index()

    # Rinomina colonne per compatibilità
    packed_daily = packed_daily.rename(columns=packed_cols_map)

    return packed_daily

def aggregate_cisterne_hourly(df_cisterne):
    """Aggrega i dati Cisterne orari in dati giornalieri (MEDIA, non somma)"""
    # Trova la colonna temporale
    time_col = None
    possible_time_cols = ['Timestamp', 'Time', 'DateTime', 'Date', 'timestamp', 'time', 'datetime']

    for col in possible_time_cols:
        if col in df_cisterne.columns:
            time_col = col
            break

    if time_col is None:
        time_col = df_cisterne.columns[0]
        print(f"⚠️ Colonna temporale non trovata, uso: {time_col}")

    # Converti timestamp a datetime
    try:
        df_cisterne[time_col] = pd.to_datetime(df_cisterne[time_col])
    except Exception as e:
        raise ValueError(
            f"❌ Errore conversione timestamp nella colonna '{time_col}'!\n"
            f"Formato richiesto: YYYY-MM-DD HH:MM:SS\n"
            f"Errore: {str(e)}"
        )

    # Estrai solo la data (senza ora)
    df_cisterne['Date'] = df_cisterne[time_col].dt.date

    # Trova colonne Cisterne con vari formati possibili
    cisterne_cols_map = {}
    for orig_name, target_name in [
        ('Truck1_Level', 'Truck1 Level'),
        ('Truck1Level', 'Truck1 Level'),
        ('Truck1 Level', 'Truck1 Level'),
        ('Truck1_Plato', 'Truck1 Average Plato'),
        ('Truck1Plato', 'Truck1 Average Plato'),
        ('Truck1 Plato', 'Truck1 Average Plato'),
        ('Truck1_Average_Plato', 'Truck1 Average Plato'),
        ('Truck2_Level', 'Truck2 Level'),
        ('Truck2Level', 'Truck2 Level'),
        ('Truck2 Level', 'Truck2 Level'),
        ('Truck2_Plato', 'Truck2 Average Plato'),
        ('Truck2Plato', 'Truck2 Average Plato'),
        ('Truck2 Plato', 'Truck2 Average Plato'),
        ('Truck2_Average_Plato', 'Truck2 Average Plato'),
    ]:
        if orig_name in df_cisterne.columns:
            cisterne_cols_map[orig_name] = target_name

    if not cisterne_cols_map:
        raise ValueError(
            f"❌ Colonne Cisterne non trovate!\n"
            f"Richieste: Truck1_Level, Truck1_Plato, Truck2_Level, Truck2_Plato\n"
            f"Trovate: {', '.join(df_cisterne.columns)}"
        )

    # Aggrega per giorno: SOMMA per Level (volume in hl), MEDIA per Plato (concentrazione)
    # I dati truck CSV sono in hl e devono essere sommati per ottenere il totale giornaliero
    agg_dict = {}
    for col in cisterne_cols_map.keys():
        if 'Level' in col:
            agg_dict[col] = 'sum'  # SOMMA dei volumi
        else:
            agg_dict[col] = 'mean'  # MEDIA del Plato
    cisterne_daily = df_cisterne.groupby('Date').agg(agg_dict).reset_index()

    # Rinomina colonne per compatibilità
    cisterne_daily = cisterne_daily.rename(columns=cisterne_cols_map)

    return cisterne_daily

def merge_stock_packed_cisterne(df_stock, df_packed, df_cisterne):
    """Unisce i 3 DataFrame (Stock, Packed, Cisterne) per data"""
    # Converti Time del DataFrame stock a date
    df_stock['Date'] = pd.to_datetime(df_stock['Time']).dt.date

    # Merge 1: Stock + Packed (left join - mantiene tutte le date di Stock)
    df_merged = df_stock.merge(df_packed, on='Date', how='left')

    # Riempi NaN con 0 per i Packed
    packed_cols = ['Packed OW1', 'Packed RGB', 'Packed OW2', 'Packed KEG']
    for col in packed_cols:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0)

    # Merge 2: (Stock + Packed) + Cisterne (left join)
    df_merged = df_merged.merge(df_cisterne, on='Date', how='left')

    # Riempi NaN con 0 per le Cisterne
    cisterne_cols = ['Truck1 Level', 'Truck1 Average Plato', 'Truck2 Level', 'Truck2 Average Plato']
    for col in cisterne_cols:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0)

    # Rimuovi colonna Date temporanea
    df_merged = df_merged.drop('Date', axis=1)

    return df_merged

def process_all_days(csv_stock_path, csv_packed_path, csv_cisterne_path):
    """Processa tutti i giorni e esporta risultati (Triple CSV Mode)"""
    print("Caricamento CSV Stock (solo tanks BBT/FST/RBT)...")
    df_stock = pd.read_csv(csv_stock_path)

    print("Caricamento CSV Packed (orario)...")
    df_packed = pd.read_csv(csv_packed_path)
    print(f"  CSV Packed: {len(df_packed)} righe orarie")

    print("Caricamento CSV Cisterne (orario)...")
    df_cisterne = pd.read_csv(csv_cisterne_path)
    print(f"  CSV Cisterne: {len(df_cisterne)} righe orarie")

    print("Aggregazione dati Packed orari → giornalieri (SOMMA)...")
    packed_daily = aggregate_packed_hourly(df_packed)
    print(f"  Aggregati in {len(packed_daily)} giorni")

    print("Aggregazione dati Cisterne orari → giornalieri (MEDIA)...")
    cisterne_daily = aggregate_cisterne_hourly(df_cisterne)
    print(f"  Aggregati in {len(cisterne_daily)} giorni")

    print("Merge dei 3 DataFrame (Stock + Packed + Cisterne)...")
    df = merge_stock_packed_cisterne(df_stock, packed_daily, cisterne_daily)
    print(f"  DataFrame finale: {len(df)} righe\n")

    # Gestione interattiva dei valori NaN
    df = handle_missing_values(df)

    results = []

    print("Elaborazione in corso...")
    print(f"Totale giorni: {len(df)}\n")
    
    for idx in range(len(df)):
        row = df.iloc[idx]
        
        # PACKED
        packed_ow1 = float(row['Packed OW1'])
        packed_rgb = float(row['Packed RGB'])
        packed_ow2 = float(row['Packed OW2'])
        packed_keg = float(row['Packed KEG'])
        packed_total = packed_ow1 + packed_rgb + packed_ow2 + packed_keg

        # CISTERNE
        truck1_plato = float(row['Truck1 Average Plato'])
        truck1_level = float(row['Truck1 Level'])
        truck1_hl_std = calc_hl_std(truck1_level, truck1_plato, 8)

        truck2_plato = float(row['Truck2 Average Plato'])
        truck2_level = float(row['Truck2 Level'])
        truck2_hl_std = calc_hl_std(truck2_level, truck2_plato, 8)
        
        cisterne_total = truck1_hl_std + truck2_hl_std
        
        # STOCK INIZIALE
        stock_iniziale = 0
        if idx > 0:
            prev_row = df.iloc[idx - 1]
            for tank_num in BBT_TANKS:
                plato_col = f'BBT {tank_num} Average Plato'
                level_col = f'BBT{tank_num} Level'
                material_col = f'BBT{tank_num} Material'
                if plato_col in prev_row.index and level_col in prev_row.index:
                    stock_iniziale += calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
            
            for tank_num in FST_TANKS:
                plato_col = f'FST {tank_num} Average Plato'
                level_col = f'FST{tank_num} Level '
                material_col = f'FST{tank_num} Material'
                if plato_col in prev_row.index and level_col in prev_row.index:
                    stock_iniziale += calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
            
            for tank_num in RBT_TANKS:
                plato_col = f'RBT {tank_num} Average Plato'
                level_col = f'RBT{tank_num} Level'
                material_col = f'RBT{tank_num} Material'
                if plato_col in prev_row.index and level_col in prev_row.index and level_col in df.columns:
                    stock_iniziale += calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
        
        # STOCK FINALE
        stock_finale = 0
        for tank_num in BBT_TANKS:
            plato_col = f'BBT {tank_num} Average Plato'
            level_col = f'BBT{tank_num} Level'
            material_col = f'BBT{tank_num} Material'
            if plato_col in row.index and level_col in row.index:
                stock_finale += calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        for tank_num in FST_TANKS:
            plato_col = f'FST {tank_num} Average Plato'
            level_col = f'FST{tank_num} Level '
            material_col = f'FST{tank_num} Material'
            if plato_col in row.index and level_col in row.index:
                stock_finale += calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        for tank_num in RBT_TANKS:
            plato_col = f'RBT {tank_num} Average Plato'
            level_col = f'RBT{tank_num} Level'
            material_col = f'RBT{tank_num} Material'
            if plato_col in row.index and level_col in row.index and level_col in df.columns:
                stock_finale += calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        # DELTA STOCK e PRODUCED
        delta_stock = stock_finale - stock_iniziale
        produced = packed_total + (cisterne_total / 2) + (delta_stock / 2)
        
        result_dict = {
            'Data': row['Time'],
            # PACKED
            'Packed OW1': packed_ow1,
            'Packed RGB': packed_rgb,
            'Packed OW2': packed_ow2,
            'Packed KEG': packed_keg,
            'Packed Total': packed_total,
            # CISTERNE
            'Truck1 Plato': truck1_plato,
            'Truck1 Level': truck1_level,
            'Truck1 hl_std': truck1_hl_std,
            'Truck2 Plato': truck2_plato,
            'Truck2 Level': truck2_level,
            'Truck2 hl_std': truck2_hl_std,
            'Cisterne Total': cisterne_total,
        }
        
        # BBT TANKS DETTAGLI
        for tank_num in BBT_TANKS:
            plato_col = f'BBT {tank_num} Average Plato'
            level_col = f'BBT{tank_num} Level'
            material_col = f'BBT{tank_num} Material'
            if plato_col in row.index and level_col in row.index and material_col in row.index:
                plato_val = float(row[plato_col])
                level_val = float(row[level_col])
                material_val = row[material_col]
                hl_std_val = calc_hl_std(level_val, plato_val, material_val)
                result_dict[f'BBT{tank_num} Level'] = level_val
                result_dict[f'BBT{tank_num} Plato'] = plato_val
                result_dict[f'BBT{tank_num} hl_std'] = hl_std_val

        # FST TANKS DETTAGLI
        for tank_num in FST_TANKS:
            plato_col = f'FST {tank_num} Average Plato'
            level_col = f'FST{tank_num} Level '
            material_col = f'FST{tank_num} Material'
            if plato_col in row.index and level_col in row.index and material_col in row.index:
                plato_val = float(row[plato_col])
                level_val = float(row[level_col])
                material_val = row[material_col]
                hl_std_val = calc_hl_std(level_val, plato_val, material_val)
                result_dict[f'FST{tank_num} Level'] = level_val
                result_dict[f'FST{tank_num} Plato'] = plato_val
                result_dict[f'FST{tank_num} hl_std'] = hl_std_val

        # RBT TANKS DETTAGLI
        for tank_num in RBT_TANKS:
            plato_col = f'RBT {tank_num} Average Plato'
            material_col = f'RBT{tank_num} Material'
            if plato_col in row.index and material_col in row.index:
                plato_val = float(row[plato_col])
                material_val = row[material_col]
                # Nota: RBT non ha Level nel CSV, solo Plato e Material
                result_dict[f'RBT{tank_num} Plato'] = plato_val
                result_dict[f'RBT{tank_num} Material'] = material_val
        
        # STOCK E PRODUCED
        result_dict.update({
            'Stock Iniziale': stock_iniziale,
            'Stock Finale': stock_finale,
            'Delta Stock': delta_stock,
            'Produced': produced
        })
        
        results.append(result_dict)
        
        print(f"  [{idx+1:2d}] {row['Time']} → Produced: {produced:10.2f} hl")
    
    # Esporta CSV
    df_results = pd.DataFrame(results)
    output_path = os.path.join(OUTPUT_DIR, 'produced_results_batch.csv')
    df_results.to_csv(output_path, index=False)
    
    # Esporta anche Excel
    try:
        output_xlsx = os.path.join(OUTPUT_DIR, 'produced_results_batch.xlsx')
        df_results.to_excel(output_xlsx, index=False, sheet_name='Produced')
        print(f"\n✓ Export completato!")
        print(f"  CSV:  {output_path}")
        print(f"  XLSX: {output_xlsx}")
    except:
        print(f"\n✓ CSV esportato: {output_path}")
    
    # Statistiche
    print(f"\n{'='*60}")
    print("STATISTICHE")
    print(f"{'='*60}")
    print(f"Giorni elaborati:        {len(results)}")
    print(f"PRODUCED totale:         {df_results['Produced'].sum():.2f} hl")
    print(f"PRODUCED medio:          {df_results['Produced'].mean():.2f} hl")
    print(f"PRODUCED min:            {df_results['Produced'].min():.2f} hl")
    print(f"PRODUCED max:            {df_results['Produced'].max():.2f} hl")
    print(f"Packed totale:           {df_results['Packed Total'].sum():.2f} hl")
    print(f"Cisterne totale:         {df_results['Cisterne Total'].sum():.2f} hl")
    print(f"Stock iniziale (day 1):  {df_results['Stock Iniziale'].iloc[0]:.2f} hl std")
    print(f"Stock finale (day 31):   {df_results['Stock Finale'].iloc[-1]:.2f} hl std")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    print("="*60)
    print("PRODUCED CALCULATOR - Triple CSV Mode")
    print("="*60)
    print(f"Sistema: {'Windows' if IS_WINDOWS else 'Linux/Mac'}")
    print(f"Cartella di lavoro: {OUTPUT_DIR}\n")

    # Verifica esistenza tutti e 3 i CSV
    if not os.path.exists(CSV_STOCK_PATH):
        print(f"❌ CSV Stock non trovato: {CSV_STOCK_PATH}")
        print(f"   Assicurati che il file Stock (solo BBT/FST/RBT) sia disponibile")
        sys.exit(1)

    if not os.path.exists(CSV_PACKED_PATH):
        print(f"❌ CSV Packed non trovato: {CSV_PACKED_PATH}")
        print(f"   Assicurati che il file Packed (orario) sia disponibile")
        sys.exit(1)

    if not os.path.exists(CSV_CISTERNE_PATH):
        print(f"❌ CSV Cisterne non trovato: {CSV_CISTERNE_PATH}")
        print(f"   Assicurati che il file Cisterne (orario) sia disponibile")
        sys.exit(1)

    print(f"✓ CSV Stock:    {os.path.basename(CSV_STOCK_PATH)}")
    print(f"✓ CSV Packed:   {os.path.basename(CSV_PACKED_PATH)}")
    print(f"✓ CSV Cisterne: {os.path.basename(CSV_CISTERNE_PATH)}\n")

    try:
        process_all_days(CSV_STOCK_PATH, CSV_PACKED_PATH, CSV_CISTERNE_PATH)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)