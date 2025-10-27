#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per analizzare componenti del Produced per una data specifica
"""

import pandas as pd
import sys

# Importa funzioni di calcolo
from produced_batch import calc_hl_std, BBT_TANKS, FST_TANKS

def analyze_produced_for_date(csv_path, target_date_or_index):
    """
    Analizza i componenti del Produced per una data specifica

    Args:
        csv_path: Path al CSV
        target_date_or_index: Data (formato YYYY-MM-DD) o numero riga (1-based)
    """
    df = pd.read_csv(csv_path)

    # Trova la riga target
    if isinstance(target_date_or_index, str) and '-' in target_date_or_index:
        # È una data
        df['Date_Only'] = pd.to_datetime(df['Time']).dt.date.astype(str)
        matches = df[df['Date_Only'] == target_date_or_index]
        if len(matches) == 0:
            print(f"❌ Data {target_date_or_index} non trovata nel CSV")
            print(f"\nDate disponibili:")
            for idx, date in enumerate(df['Time'].head(10), 1):
                print(f"  {idx}. {pd.to_datetime(date).strftime('%Y-%m-%d')}")
            return
        idx = matches.index[0]
        row = df.iloc[idx]
    else:
        # È un indice (1-based)
        idx = int(target_date_or_index) - 1
        if idx < 0 or idx >= len(df):
            print(f"❌ Riga {target_date_or_index} non valida (range: 1-{len(df)})")
            return
        row = df.iloc[idx]

    # Data
    date_str = pd.to_datetime(row['Time']).strftime('%Y-%m-%d')
    print(f"\n{'='*70}")
    print(f"ANALISI PRODUCED - {date_str} (riga {idx+1}/{len(df)})")
    print(f"{'='*70}\n")

    # === PACKED ===
    print("📦 PACKED:")
    packed_ow1 = float(row['Packed OW1'])
    packed_rgb = float(row['Packed RGB'])
    packed_ow2 = float(row['Packed OW2'])
    packed_keg = float(row['Packed KEG'])
    packed_total = packed_ow1 + packed_rgb + packed_ow2 + packed_keg

    print(f"  - OW1: {packed_ow1:>10.2f} hl")
    print(f"  - RGB: {packed_rgb:>10.2f} hl")
    print(f"  - OW2: {packed_ow2:>10.2f} hl")
    print(f"  - KEG: {packed_keg:>10.2f} hl")
    print(f"  {'─'*40}")
    print(f"  TOTALE PACKED: {packed_total:>10.2f} hl")

    # === CISTERNE ===
    print(f"\n🚚 CISTERNE:")
    truck1_plato = float(row['Truck1 Average Plato'])
    truck1_level = float(row['Truck1 Level'])
    truck1_hl_std = calc_hl_std(truck1_level, truck1_plato, 8)

    truck2_plato = float(row['Truck2 Average Plato'])
    truck2_level = float(row['Truck2 Level'])
    truck2_hl_std = calc_hl_std(truck2_level, truck2_plato, 8)

    cisterne_total = truck1_hl_std + truck2_hl_std

    print(f"  - Truck1: Plato={truck1_plato:.2f}°, Level={truck1_level:.2f}L → {truck1_hl_std:.2f} hl std")
    print(f"  - Truck2: Plato={truck2_plato:.2f}°, Level={truck2_level:.2f}L → {truck2_hl_std:.2f} hl std")
    print(f"  {'─'*40}")
    print(f"  TOTALE CISTERNE: {cisterne_total:>10.2f} hl std")
    print(f"  CONTRIBUTO (÷2):  {cisterne_total/2:>10.2f} hl")

    # === STOCK ===
    print(f"\n📊 STOCK:")

    # Stock Iniziale (dal giorno precedente)
    stock_iniziale = 0
    if idx > 0:
        prev_row = df.iloc[idx - 1]
        prev_date = pd.to_datetime(prev_row['Time']).strftime('%Y-%m-%d')
        print(f"  Stock Iniziale (da {prev_date}):")

        bbt_stock = 0
        for tank_num in BBT_TANKS:
            plato_col = f'BBT {tank_num} Average Plato'
            level_col = f'BBT{tank_num} Level'
            material_col = f'BBT{tank_num} Material'
            if all(col in prev_row.index for col in [plato_col, level_col, material_col]):
                hl = calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
                if hl > 0:
                    bbt_stock += hl

        fst_stock = 0
        for tank_num in FST_TANKS:
            plato_col = f'FST {tank_num} Average Plato'
            level_col = f'FST{tank_num} Level '
            material_col = f'FST{tank_num} Material'
            if all(col in prev_row.index for col in [plato_col, level_col, material_col]):
                hl = calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
                if hl > 0:
                    fst_stock += hl

        stock_iniziale = bbt_stock + fst_stock
        print(f"    - BBT tanks: {bbt_stock:>10.2f} hl std")
        print(f"    - FST tanks: {fst_stock:>10.2f} hl std")
        print(f"    {'─'*40}")
        print(f"    TOTALE:      {stock_iniziale:>10.2f} hl std")
    else:
        print(f"  Stock Iniziale: 0.00 hl (primo giorno) ⚠️")

    # Stock Finale (del giorno corrente)
    print(f"\n  Stock Finale ({date_str}):")
    bbt_stock_f = 0
    for tank_num in BBT_TANKS:
        plato_col = f'BBT {tank_num} Average Plato'
        level_col = f'BBT{tank_num} Level'
        material_col = f'BBT{tank_num} Material'
        if all(col in row.index for col in [plato_col, level_col, material_col]):
            hl = calc_hl_std(row[level_col], row[plato_col], row[material_col])
            if hl > 0:
                bbt_stock_f += hl

    fst_stock_f = 0
    for tank_num in FST_TANKS:
        plato_col = f'FST {tank_num} Average Plato'
        level_col = f'FST{tank_num} Level '
        material_col = f'FST{tank_num} Material'
        if all(col in row.index for col in [plato_col, level_col, material_col]):
            hl = calc_hl_std(row[level_col], row[plato_col], row[material_col])
            if hl > 0:
                fst_stock_f += hl

    stock_finale = bbt_stock_f + fst_stock_f
    print(f"    - BBT tanks: {bbt_stock_f:>10.2f} hl std")
    print(f"    - FST tanks: {fst_stock_f:>10.2f} hl std")
    print(f"    {'─'*40}")
    print(f"    TOTALE:      {stock_finale:>10.2f} hl std")

    delta_stock = stock_finale - stock_iniziale
    print(f"\n  Delta Stock (Finale - Iniziale):")
    print(f"    {stock_finale:.2f} - {stock_iniziale:.2f} = {delta_stock:>10.2f} hl std")
    print(f"  CONTRIBUTO (÷2): {delta_stock/2:>10.2f} hl")

    # === PRODUCED FINALE ===
    print(f"\n{'='*70}")
    print(f"🎯 CALCOLO PRODUCED:")
    print(f"{'='*70}")
    print(f"  Packed:            {packed_total:>10.2f} hl")
    print(f"  Cisterne/2:        {cisterne_total/2:>10.2f} hl")
    print(f"  Delta Stock/2:     {delta_stock/2:>10.2f} hl")
    print(f"  {'─'*40}")

    produced = packed_total + (cisterne_total / 2) + (delta_stock / 2)
    print(f"  PRODUCED TOTALE:   {produced:>10.2f} hl")
    print(f"{'='*70}\n")

    # Analisi componenti
    print("📈 CONTRIBUTO PERCENTUALE:")
    if produced != 0:
        packed_pct = (packed_total / produced) * 100
        cisterne_pct = ((cisterne_total/2) / produced) * 100
        delta_pct = ((delta_stock/2) / produced) * 100

        print(f"  - Packed:       {packed_pct:>6.2f}%")
        print(f"  - Cisterne/2:   {cisterne_pct:>6.2f}%")
        print(f"  - Delta Stock/2: {delta_pct:>6.2f}%")

    # Warning se necessario
    if idx == 0 and stock_iniziale == 0 and stock_finale > 0:
        print(f"\n⚠️  ATTENZIONE: Primo giorno con Stock Iniziale = 0")
        print(f"   Il Produced potrebbe essere IMPRECISO!")
        print(f"   Manca il giorno precedente per il calcolo corretto dello stock.\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python debug_produced_date.py <data_o_riga>")
        print("\nEsempi:")
        print("  python debug_produced_date.py 2025-10-07")
        print("  python debug_produced_date.py 7  # riga 7")
        sys.exit(1)

    target = sys.argv[1]
    csv_path = 'produced.csv'

    analyze_produced_for_date(csv_path, target)
