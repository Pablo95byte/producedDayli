#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script per FST 241 - 2025-10-07
"""

import pandas as pd

# Carica CSV senza gestione NaN
df = pd.read_csv('produced.csv')

# Trova la riga del 2025-10-07
row = df[df['Time'] == '2025-10-07 00:00:00']

if len(row) == 0:
    print("❌ Data 2025-10-07 non trovata!")
    exit(1)

row = row.iloc[0]

print("="*80)
print("DEBUG FST 241 - 2025-10-07")
print("="*80)

# Controlla le colonne FST 241
plato_col = 'FST 241 Average Plato'
level_col = 'FST241 Level '  # Nota lo spazio finale!
material_col = 'FST241 Material'

print(f"\nColonne nel DataFrame:")
print(f"  '{plato_col}' esiste: {plato_col in df.columns}")
print(f"  '{level_col}' esiste: {level_col in df.columns}")
print(f"  '{material_col}' esiste: {material_col in df.columns}")

print(f"\nValori RAW dal CSV:")
if plato_col in row.index:
    plato_val = row[plato_col]
    print(f"  Plato: {plato_val} (tipo: {type(plato_val).__name__}, isna: {pd.isna(plato_val)})")
else:
    print(f"  Plato: COLONNA NON TROVATA")

if level_col in row.index:
    level_val = row[level_col]
    print(f"  Level: {level_val} (tipo: {type(level_val).__name__}, isna: {pd.isna(level_val)})")
else:
    print(f"  Level: COLONNA NON TROVATA")

if material_col in row.index:
    material_val = row[material_col]
    print(f"  Material: {material_val} (tipo: {type(material_val).__name__}, isna: {pd.isna(material_val)})")
else:
    print(f"  Material: COLONNA NON TROVATA")

# Simula il calcolo
print(f"\n{'='*80}")
print("SIMULAZIONE CALCOLO")
print("="*80)

MATERIAL_MAPPING = {
    0: 0, 1: 11.03, 2: 11.03, 3: 11.57, 7: 11.03, 8: 11.57,
    9: 11.68, 10: 11.03, 21: 11.68, 22: 11.68, 28: 11.68, 32: 11.03, 36: 11.03
}

def plato_to_volumetric(plato):
    if plato == 0:
        return 0
    plato = float(plato)
    grado_v = ((0.0000188792 * plato + 0.003646886) * plato + 1.001077) * plato - 0.01223565
    return grado_v

def calc_hl_std(volume_hl, plato, material):
    print(f"\n  Input calc_hl_std:")
    print(f"    volume_hl = {volume_hl} (tipo: {type(volume_hl).__name__})")
    print(f"    plato = {plato} (tipo: {type(plato).__name__})")
    print(f"    material = {material} (tipo: {type(material).__name__})")

    # Check se sono NaN
    if pd.isna(volume_hl) or pd.isna(plato) or pd.isna(material):
        print(f"  ⚠️  Rilevato NaN: volume_hl={pd.isna(volume_hl)}, plato={pd.isna(plato)}, material={pd.isna(material)}")
        print(f"  → Con il nuovo codice, questo causerebbe un ValueError")
        return None

    try:
        volume_hl = float(volume_hl)
        plato = float(plato)
        material = int(float(material))
        print(f"  Dopo conversione: volume_hl={volume_hl}, plato={plato}, material={material}")
    except Exception as e:
        print(f"  ❌ ERRORE conversione: {e}")
        return None

    if volume_hl == 0 or plato == 0:
        print(f"  → RETURN 0: volume_hl o plato è zero")
        return 0

    grado_vol = plato_to_volumetric(plato)

    if grado_vol == 0:
        print(f"  → RETURN 0: grado_vol è zero")
        return 0

    if material == 0:
        print(f"  → RETURN 0: material è zero ⚠️")
        return 0

    if material not in MATERIAL_MAPPING:
        print(f"  ❌ Material {material} non nel mapping")
        return None

    grado_std = MATERIAL_MAPPING[material]

    if grado_std == 0:
        print(f"  → RETURN 0: grado_std è zero")
        return 0

    hl_std = (volume_hl * grado_vol) / grado_std
    print(f"  ✓ hl_std = ({volume_hl} * {grado_vol:.4f}) / {grado_std} = {hl_std:.2f}")
    return hl_std

# Estrai valori come fa il codice attuale
if plato_col in row.index and level_col in row.index:
    plato_raw = row[plato_col]
    level_raw = row[level_col]
    # Questo è il comportamento problematico:
    material_raw = row[material_col] if material_col in row.index else 0

    print(f"\nValori estratti (come fa il codice):")
    print(f"  plato_raw = {plato_raw}")
    print(f"  level_raw = {level_raw}")
    print(f"  material_raw = {material_raw}")

    result = calc_hl_std(level_raw, plato_raw, material_raw)

    print(f"\n{'='*80}")
    if result is None:
        print("❌ ERRORE NEL CALCOLO")
    elif result == 0:
        print(f"⚠️  RISULTATO: 0 hl std (PROBLEMA!)")
    else:
        print(f"✓ RISULTATO: {result:.2f} hl std")
    print("="*80)
else:
    print("❌ Colonne Plato o Level non trovate!")

# Verifica se ci sono NaN in tutta la riga
print(f"\n{'='*80}")
print("ANALISI NaN NELLA RIGA COMPLETA")
print("="*80)
nan_cols = [col for col in df.columns if pd.isna(row[col])]
if nan_cols:
    print(f"⚠️  Trovati {len(nan_cols)} NaN in questa riga:")
    for col in nan_cols[:20]:  # Mostra solo i primi 20
        print(f"  - {col}")
    if len(nan_cols) > 20:
        print(f"  ... e altri {len(nan_cols) - 20} NaN")
else:
    print("✓ Nessun NaN trovato in questa riga")
