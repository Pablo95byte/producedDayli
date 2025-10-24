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
if IS_WINDOWS:
    # Path fisso per Windows
    CSV_PATH = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App\produced.csv"
    OUTPUT_DIR = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App"
else:
    CSV_PATH = '/mnt/user-data/uploads/produced.csv'
    OUTPUT_DIR = '/mnt/user-data/outputs'

# Se il CSV non esiste, prova a trovarlo
if not os.path.exists(CSV_PATH):
    print(f"⚠️ CSV non trovato in: {CSV_PATH}")
    for file in os.listdir('.'):
        if file == 'produced.csv':
            CSV_PATH = os.path.join('.', file)
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

def process_all_days(csv_path):
    """Processa tutti i giorni e esporta risultati"""
    df = pd.read_csv(csv_path)

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
    print(f"Sistema: {'Windows' if IS_WINDOWS else 'Linux/Mac'}")
    print(f"Cartella di lavoro: {OUTPUT_DIR}\n")
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ File CSV non trovato: {CSV_PATH}")
        print(f"   Assicurati che 'produced.csv' sia nella cartella: {OUTPUT_DIR}")
        sys.exit(1)
    
    try:
        process_all_days(CSV_PATH)
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        sys.exit(1)