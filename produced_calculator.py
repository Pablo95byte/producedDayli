#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCED CALCULATOR - Applicazione interattiva per calcolo Produced con Debug
"""

import pandas as pd
import numpy as np
from datetime import datetime
from colorama import Fore, Back, Style, init
import os
import sys
from pathlib import Path
from nan_handler import handle_missing_values

init(autoreset=True)

# Rilevamento sistema operativo e percorsi
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

# Determina il percorso della cartella di lavoro
if IS_WINDOWS:
    # Path fisso per Windows
    CSV_PATH = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App\produced.csv"
    OUTPUT_DIR = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App"
    WORK_DIR = OUTPUT_DIR
else:
    # Su Linux/Mac usa i percorsi originali
    CSV_PATH = '/mnt/user-data/uploads/produced.csv'
    OUTPUT_DIR = '/mnt/user-data/outputs'
    WORK_DIR = OUTPUT_DIR

# Se il CSV non esiste, prova a trovarlo
if not os.path.exists(CSV_PATH):
    print(f"⚠️ CSV non trovato in: {CSV_PATH}")
    print("Provo nella cartella corrente...")
    # Cerca nella cartella corrente
    for file in os.listdir('.'):
        if file == 'produced.csv':
            CSV_PATH = os.path.join('.', file)
            print(f"✓ Trovato: {CSV_PATH}")
            break

# Mapping dei gradi volumetrici standard
MATERIAL_MAPPING = {
    0: 0, 1: 11.03, 2: 11.03, 3: 11.57, 7: 11.03, 8: 11.57, 
    9: 11.68, 10: 11.03, 21: 11.68, 22: 11.68, 28: 11.68, 32: 11.03, 36: 11.03
}

# Elenco tank
BBT_TANKS = [111, 112, 121, 132, 211, 212, 221, 222, 231, 232, 241, 242, 251, 252]
FST_TANKS = [111, 112, 121, 122, 131, 132, 141, 142, 151, 152, 161, 171, 172, 
             211, 212, 221, 222, 231, 232, 241, 242, 243]
RBT_TANKS = [251, 252]

class ProducedCalculator:
    def __init__(self, csv_path):
        """Inizializza il calcolatore con i dati dal CSV"""
        self.df = pd.read_csv(csv_path)
        print(f"{Fore.GREEN}✓ Dati caricati: {len(self.df)} giorni{Style.RESET_ALL}")

        # Gestione interattiva dei valori NaN
        self.df = handle_missing_values(self.df)

        self.debug_mode = False
        self.current_row_idx = 0
    
    @staticmethod
    def plato_to_volumetric(plato):
        """Converte gradi Plato a gradi volumetrici"""
        if plato == 0:
            return 0
        plato = float(plato)
        grado_v = ((0.0000188792 * plato + 0.003646886) * plato + 1.001077) * plato - 0.01223565
        return grado_v
    
    @staticmethod
    def calc_hl_std(volume_hl, plato, material):
        """Calcola hl standard dal volume, plato e materiale"""
        try:
            volume_hl = float(volume_hl)
            plato = float(plato)
            material = int(float(material))
        except:
            raise ValueError(f"Valori non validi: volume_hl={volume_hl}, plato={plato}, material={material}")

        if volume_hl == 0 or plato == 0:
            return 0

        grado_vol = ProducedCalculator.plato_to_volumetric(plato)
        if grado_vol == 0:
            return 0

        # Determina grado_std
        if material == 0:
            return 0  # Material 0 → ritorna 0

        # Material è valido, usa il mapping
        if material not in MATERIAL_MAPPING:
            raise ValueError(f"Material {material} non trovato nel mapping")

        grado_std = MATERIAL_MAPPING[material]
        if grado_std == 0:
            return 0

        hl_std = (volume_hl * grado_vol) / grado_std
        return hl_std
    
    def get_packed(self, row):
        """Calcola il totale Packed"""
        packed_ow1 = float(row['Packed OW1'])
        packed_rgb = float(row['Packed RGB'])
        packed_ow2 = float(row['Packed OW2'])
        packed_keg = float(row['Packed KEG'])

        return {
            'OW1': packed_ow1,
            'RGB': packed_rgb,
            'OW2': packed_ow2,
            'KEG': packed_keg,
            'TOTAL': packed_ow1 + packed_rgb + packed_ow2 + packed_keg
        }
    
    def get_cisterne(self, row):
        """Calcola le cisterne (Truck1 + Truck2)"""
        truck1_plato = float(row['Truck1 Average Plato'])
        truck1_level = float(row['Truck1 Level'])
        truck1_hl_std = self.calc_hl_std(truck1_level, truck1_plato, 8)

        truck2_plato = float(row['Truck2 Average Plato'])
        truck2_level = float(row['Truck2 Level'])
        truck2_hl_std = self.calc_hl_std(truck2_level, truck2_plato, 8)

        return {
            'truck1_plato': truck1_plato,
            'truck1_level': truck1_level,
            'truck1_hl_std': truck1_hl_std,
            'truck2_plato': truck2_plato,
            'truck2_level': truck2_level,
            'truck2_hl_std': truck2_hl_std,
            'TOTAL': truck1_hl_std + truck2_hl_std
        }
    
    def get_stock_iniziale(self, row_idx):
        """Calcola lo stock iniziale (giorno precedente)"""
        stock_iniziale = 0
        
        if row_idx == 0:
            return stock_iniziale
        
        prev_row = self.df.iloc[row_idx - 1]
        
        for tank_num in BBT_TANKS:
            plato_col = f'BBT {tank_num} Average Plato'
            level_col = f'BBT{tank_num} Level'
            material_col = f'BBT{tank_num} Material'
            if plato_col in prev_row.index and level_col in prev_row.index:
                stock_iniziale += self.calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
        
        for tank_num in FST_TANKS:
            plato_col = f'FST {tank_num} Average Plato'
            level_col = f'FST{tank_num} Level '
            material_col = f'FST{tank_num} Material'
            if plato_col in prev_row.index and level_col in prev_row.index:
                stock_iniziale += self.calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
        
        for tank_num in RBT_TANKS:
            plato_col = f'RBT {tank_num} Average Plato'
            level_col = f'RBT{tank_num} Level'
            material_col = f'RBT{tank_num} Material'
            if plato_col in prev_row.index and level_col in prev_row.index and level_col in self.df.columns:
                stock_iniziale += self.calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
        
        return stock_iniziale
    
    def get_stock_finale(self, row):
        """Calcola lo stock finale (giorno corrente)"""
        stock_finale = 0
        
        for tank_num in BBT_TANKS:
            plato_col = f'BBT {tank_num} Average Plato'
            level_col = f'BBT{tank_num} Level'
            material_col = f'BBT{tank_num} Material'
            if plato_col in row.index and level_col in row.index:
                stock_finale += self.calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        for tank_num in FST_TANKS:
            plato_col = f'FST {tank_num} Average Plato'
            level_col = f'FST{tank_num} Level '
            material_col = f'FST{tank_num} Material'
            if plato_col in row.index and level_col in row.index:
                stock_finale += self.calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        for tank_num in RBT_TANKS:
            plato_col = f'RBT {tank_num} Average Plato'
            level_col = f'RBT{tank_num} Level'
            material_col = f'RBT{tank_num} Material'
            if plato_col in row.index and level_col in row.index and level_col in self.df.columns:
                stock_finale += self.calc_hl_std(row[level_col], row[plato_col], row[material_col])
        
        return stock_finale
    
    def calculate_produced(self, row_idx):
        """Calcola il Produced per un giorno specifico"""
        row = self.df.iloc[row_idx]
        
        packed = self.get_packed(row)
        cisterne = self.get_cisterne(row)
        stock_iniziale = self.get_stock_iniziale(row_idx)
        stock_finale = self.get_stock_finale(row)
        delta_stock = stock_finale - stock_iniziale
        
        produced = packed['TOTAL'] + (cisterne['TOTAL'] / 2) + (delta_stock / 2)
        
        return {
            'date': row['Time'],
            'packed': packed,
            'cisterne': cisterne,
            'stock_iniziale': stock_iniziale,
            'stock_finale': stock_finale,
            'delta_stock': delta_stock,
            'produced': produced
        }

def print_menu():
    """Stampa il menu principale"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"   PRODUCED CALCULATOR - DEBUG MODE")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print("1. Seleziona un giorno")
    print("2. Visualizza risultati giorno corrente")
    print("3. Debug dettagliato (passo per passo)")
    print("4. Esporta tutti i risultati (CSV)")
    print("5. Genera grafici PNG 📊")
    print("6. Genera Report PDF 📄")
    print("7. Test formule")
    print("8. Esci")
    print()

def print_packed_details(packed):
    """Stampa dettagli Packed"""
    print(f"\n{Fore.YELLOW}📦 PACKED:{Style.RESET_ALL}")
    print(f"  OW1:   {packed['OW1']:.2f}")
    print(f"  RGB:   {packed['RGB']:.2f}")
    print(f"  OW2:   {packed['OW2']:.2f}")
    print(f"  KEG:   {packed['KEG']:.2f}")
    print(f"  {Fore.GREEN}TOTAL: {packed['TOTAL']:.2f}{Style.RESET_ALL}")

def print_cisterne_details(cisterne):
    """Stampa dettagli Cisterne"""
    print(f"\n{Fore.YELLOW}🚚 CISTERNE (Truck):{Style.RESET_ALL}")
    print(f"  Truck1 Plato:     {cisterne['truck1_plato']:.2f}°")
    print(f"  Truck1 Level:     {cisterne['truck1_level']:.2f} L")
    print(f"  Truck1 hl std:    {cisterne['truck1_hl_std']:.2f}")
    print(f"  Truck2 Plato:     {cisterne['truck2_plato']:.2f}°")
    print(f"  Truck2 Level:     {cisterne['truck2_level']:.2f} L")
    print(f"  Truck2 hl std:    {cisterne['truck2_hl_std']:.2f}")
    print(f"  {Fore.GREEN}TOTAL: {cisterne['TOTAL']:.2f}{Style.RESET_ALL}")

def print_stock_details(stock_iniziale, stock_finale, delta_stock):
    """Stampa dettagli Stock"""
    print(f"\n{Fore.YELLOW}📊 STOCK:{Style.RESET_ALL}")
    print(f"  Iniziale (giorno precedente): {stock_iniziale:.2f} hl std")
    print(f"  Finale (giorno corrente):     {stock_finale:.2f} hl std")
    print(f"  {Fore.CYAN}Delta: {delta_stock:.2f} hl std{Style.RESET_ALL}")

def print_produced_result(result):
    """Stampa il risultato finale"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"   CALCOLO PRODUCED")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"Data: {result['date']}")
    print_packed_details(result['packed'])
    print_cisterne_details(result['cisterne'])
    print_stock_details(result['stock_iniziale'], result['stock_finale'], result['delta_stock'])
    
    print(f"\n{Fore.CYAN}📐 FORMULA:{Style.RESET_ALL}")
    print(f"  Produced = Packed + (Cisterne / 2) + (Delta Stock / 2)")
    print(f"  Produced = {result['packed']['TOTAL']:.2f} + ({result['cisterne']['TOTAL']:.2f} / 2) + ({result['delta_stock']:.2f} / 2)")
    print(f"  Produced = {result['packed']['TOTAL']:.2f} + {result['cisterne']['TOTAL']/2:.2f} + {result['delta_stock']/2:.2f}")
    
    print(f"\n{Fore.GREEN}{Back.BLACK}{'='*60}")
    print(f"   PRODUCED = {result['produced']:.2f} hl")
    print(f"{'='*60}{Style.RESET_ALL}\n")

def select_day(calc):
    """Seleziona un giorno"""
    print(f"\n{Fore.CYAN}Giorni disponibili:{Style.RESET_ALL}")
    for i, date in enumerate(calc.df['Time']):
        print(f"  {i}: {date}")
    
    try:
        idx = int(input(f"\nSeleziona indice giorno (0-{len(calc.df)-1}): "))
        if 0 <= idx < len(calc.df):
            calc.current_row_idx = idx
            print(f"{Fore.GREEN}✓ Giorno selezionato: {calc.df.iloc[idx]['Time']}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}✗ Indice non valido{Style.RESET_ALL}")
            return False
    except ValueError:
        print(f"{Fore.RED}✗ Input non valido{Style.RESET_ALL}")
        return False

def debug_detailed(calc):
    """Debug dettagliato passo per passo"""
    result = calc.calculate_produced(calc.current_row_idx)
    print_produced_result(result)
    
    print(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
    input()

def export_all_results(calc):
    """Esporta tutti i risultati in CSV"""
    results = []
    
    print(f"\n{Fore.CYAN}Elaborazione in corso...{Style.RESET_ALL}")
    for idx in range(len(calc.df)):
        result = calc.calculate_produced(idx)
        results.append({
            'Data': result['date'],
            'Packed OW1': result['packed']['OW1'],
            'Packed RGB': result['packed']['RGB'],
            'Packed OW2': result['packed']['OW2'],
            'Packed KEG': result['packed']['KEG'],
            'Packed Total': result['packed']['TOTAL'],
            'Truck1 Plato': result['cisterne']['truck1_plato'],
            'Truck1 Level': result['cisterne']['truck1_level'],
            'Truck1 hl std': result['cisterne']['truck1_hl_std'],
            'Truck2 Plato': result['cisterne']['truck2_plato'],
            'Truck2 Level': result['cisterne']['truck2_level'],
            'Truck2 hl std': result['cisterne']['truck2_hl_std'],
            'Cisterne Total': result['cisterne']['TOTAL'],
            'Stock Iniziale': result['stock_iniziale'],
            'Stock Finale': result['stock_finale'],
            'Delta Stock': result['delta_stock'],
            'Produced': result['produced']
        })
    
    df_results = pd.DataFrame(results)
    output_path = os.path.join(OUTPUT_DIR, 'produced_results.csv')
    df_results.to_csv(output_path, index=False, decimal=',')
    print(f"{Fore.GREEN}✓ Esportato: {output_path}{Style.RESET_ALL}")
    print(f"  Righe: {len(results)}")

def test_formulas(calc):
    """Test delle formule individuali"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print("   TEST FORMULE")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    try:
        print("1. Test Plato → Grado Volumetrico")
        plato = float(input("   Inserisci gradi Plato: "))
        grado_v = calc.plato_to_volumetric(plato)
        print(f"   {Fore.GREEN}Risultato: {grado_v:.6f}{Style.RESET_ALL}\n")
        
        print("2. Test Calcolo hl std")
        volume = float(input("   Inserisci volume (L): "))
        plato = float(input("   Inserisci Plato: "))
        material = int(input("   Inserisci Material (0-36): "))
        
        if material not in MATERIAL_MAPPING:
            print(f"{Fore.RED}✗ Material non riconosciuto{Style.RESET_ALL}")
            print(f"  Materiali validi: {list(MATERIAL_MAPPING.keys())}")
            return
        
        hl_std = calc.calc_hl_std(volume, plato, material)
        grado_vol = calc.plato_to_volumetric(plato)
        grado_std = MATERIAL_MAPPING[material]
        
        print(f"\n   {Fore.CYAN}Dettagli calcolo:{Style.RESET_ALL}")
        print(f"   Volume:           {volume:.2f} L")
        print(f"   Plato:            {plato:.2f}°")
        print(f"   Material:         {material}")
        print(f"   Grado Volumetrico: {grado_vol:.6f}")
        print(f"   Grado Std:        {grado_std:.2f}")
        print(f"   {Fore.GREEN}hl std:           {hl_std:.4f}{Style.RESET_ALL}\n")
        
    except ValueError:
        print(f"{Fore.RED}✗ Input non valido{Style.RESET_ALL}\n")

def generate_grafici_menu(calc):
    """Genera grafici dal menu"""
    print(f"\n{Fore.CYAN}Generazione grafici in corso...{Style.RESET_ALL}")
    
    try:
        # Importa il modulo grafici
        from produced_grafici import GraficiProduced
        
        # Crea l'istanza
        grafici = GraficiProduced(CSV_PATH)
        grafici.calcola_produced()
        
        # Genera i grafici
        grafici.genera_grafici()
        grafici.genera_grafici_dettagliati()
        
        # Stampa statistiche
        grafici.stampa_statistiche_settimanali()
        
        # Esporta dati
        output_csv = os.path.join(OUTPUT_DIR, 'produced_per_grafici.csv')
        grafici.df_results.to_csv(output_csv, index=False)
        print(f"{Fore.GREEN}✓ Dati per grafici esportati: {output_csv}{Style.RESET_ALL}")
        
    except ImportError:
        print(f"{Fore.RED}✗ Modulo produced_grafici.py non trovato!{Style.RESET_ALL}")
        print(f"   Assicurati che sia nella stessa cartella\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Errore nella generazione grafici:{Style.RESET_ALL}")
        print(f"   {str(e)}\n")

def generate_pdf_report_menu(calc):
    """Genera report PDF dal menu"""
    print(f"\n{Fore.CYAN}Generazione report PDF in corso...{Style.RESET_ALL}")
    print(f"   Questo potrebbe richiedere qualche minuto (molti grafici)...")
    
    try:
        # Importa il modulo PDF report
        from produced_pdf_report import ReportPDFProduced
        
        # Crea l'istanza
        report = ReportPDFProduced(CSV_PATH)
        report.calcola_produced()
        report.genera_pdf_report()
        
        print(f"{Fore.GREEN}✓ Report PDF generato con successo!{Style.RESET_ALL}")
        print(f"   Troverai il file: produced_report.pdf\n")
        
    except ImportError:
        print(f"{Fore.RED}✗ Modulo produced_pdf_report.py non trovato!{Style.RESET_ALL}")
        print(f"   Assicurati che sia nella stessa cartella\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Errore nella generazione PDF:{Style.RESET_ALL}")
        print(f"   {str(e)}\n")

def main():
    """Main loop"""
    print(f"{Fore.CYAN}Sistema: {'Windows' if IS_WINDOWS else 'Linux/Mac'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Cartella di lavoro: {OUTPUT_DIR}{Style.RESET_ALL}\n")
    
    if not os.path.exists(CSV_PATH):
        print(f"{Fore.RED}✗ File CSV non trovato: {CSV_PATH}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Assicurati che 'produced.csv' sia nella cartella: {OUTPUT_DIR}{Style.RESET_ALL}")
        sys.exit(1)
    
    calc = ProducedCalculator(CSV_PATH)
    
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print_menu()
        
        choice = input("Scelta: ").strip()
        
        if choice == '1':
            select_day(calc)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '2':
            result = calc.calculate_produced(calc.current_row_idx)
            print_produced_result(result)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '3':
            debug_detailed(calc)
        
        elif choice == '4':
            export_all_results(calc)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '5':
            generate_grafici_menu(calc)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '6':
            generate_pdf_report_menu(calc)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '7':
            test_formulas(calc)
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")
        
        elif choice == '8':
            print(f"{Fore.GREEN}Arrivederci!{Style.RESET_ALL}")
            sys.exit(0)
        
        else:
            print(f"{Fore.RED}✗ Scelta non valida{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Premi ENTER per continuare...{Style.RESET_ALL}")

if __name__ == '__main__':
    main()