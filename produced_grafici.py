#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCED CALCULATOR - Modulo Grafici
Genera grafici giornalieri e settimanali
"""

import pandas as pd
import numpy as np
from datetime import datetime
from colorama import Fore, Back, Style
import os
import sys
from pathlib import Path
from nan_handler import handle_missing_values

# Rilevamento sistema operativo e percorsi
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

if IS_WINDOWS:
    OUTPUT_DIR = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App"
else:
    OUTPUT_DIR = '/mnt/user-data/outputs'

# Importa matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams
    rcParams['font.size'] = 10
except ImportError:
    print(f"{Fore.RED}⚠️ matplotlib non installato!{Style.RESET_ALL}")
    print("Installa con: pip install matplotlib")
    sys.exit(1)

class GraficiProduced:
    def __init__(self, csv_path):
        """Inizializza il generatore di grafici"""
        self.df = pd.read_csv(csv_path)

        # Gestione interattiva dei valori NaN
        self.df = handle_missing_values(self.df)

        self.results = []
        self.df_results = None
        
    def calcola_produced(self):
        """Calcola tutti i produced (copiato dal calculator)"""
        # Mapping materiali
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

            # Material 0 ritorna 0
            if material == 0:
                return 0

            # Material è valido, usa il mapping
            if material not in MATERIAL_MAPPING:
                raise ValueError(f"Material {material} non trovato nel mapping")

            grado_std = MATERIAL_MAPPING[material]
            if grado_std == 0:
                return 0

            hl_std = (volume_hl * grado_vol) / grado_std
            return hl_std
        
        print(f"\n{Fore.CYAN}Elaborazione dati per grafici...{Style.RESET_ALL}")
        
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            
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
                prev_row = self.df.iloc[idx - 1]
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
                    if plato_col in prev_row.index and level_col in prev_row.index and level_col in self.df.columns:
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
                if plato_col in row.index and level_col in row.index and level_col in self.df.columns:
                    stock_finale += calc_hl_std(row[level_col], row[plato_col], row[material_col])
            
            # PRODUCED
            delta_stock = stock_finale - stock_iniziale
            produced = packed_total + (cisterne_total / 2) + (delta_stock / 2)
            
            self.results.append({
                'Data': row['Time'],
                'Produced': produced,
                'Packed': packed_total,
                'Cisterne': cisterne_total,
                'Stock_Iniziale': stock_iniziale,
                'Stock_Finale': stock_finale,
                'Delta_Stock': delta_stock
            })
        
        self.df_results = pd.DataFrame(self.results)
        self.df_results['Data'] = pd.to_datetime(self.df_results['Data'])
        self.df_results['Week'] = self.df_results['Data'].dt.isocalendar().week
        self.df_results['Year'] = self.df_results['Data'].dt.isocalendar().year
        self.df_results['Week_Year'] = self.df_results['Year'].astype(str) + '-W' + self.df_results['Week'].astype(str).str.zfill(2)
        
        print(f"{Fore.GREEN}✓ Dati calcolati{Style.RESET_ALL}")
    
    def genera_grafici(self):
        """Genera tutti i grafici"""
        if self.df_results is None:
            print(f"{Fore.RED}✗ Calcola i dati prima!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Generazione grafici...{Style.RESET_ALL}")
        
        # Figura con 2 subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle('PRODUCED - Analisi Giornaliera e Settimanale', fontsize=16, fontweight='bold')
        
        # GRAFICO 1: Produced Giornaliero
        ax1.bar(self.df_results['Data'], self.df_results['Produced'], color='steelblue', alpha=0.7)
        ax1.set_xlabel('Data', fontweight='bold')
        ax1.set_ylabel('Produced (hl)', fontweight='bold')
        ax1.set_title('Produced Giornaliero', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # GRAFICO 2: Produced Settimanale
        weekly_produced = self.df_results.groupby('Week_Year')['Produced'].sum()
        ax2.bar(range(len(weekly_produced)), weekly_produced.values, color='darkgreen', alpha=0.7)
        ax2.set_xlabel('Settimana', fontweight='bold')
        ax2.set_ylabel('Produced (hl)', fontweight='bold')
        ax2.set_title('Produced Settimanale', fontweight='bold')
        ax2.set_xticks(range(len(weekly_produced)))
        ax2.set_xticklabels(weekly_produced.index, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Salva PNG
        output_path = os.path.join(OUTPUT_DIR, 'produced_grafici.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"{Fore.GREEN}✓ Grafico PNG salvato: {output_path}{Style.RESET_ALL}")
        
        plt.close()
    
    def genera_grafici_dettagliati(self):
        """Genera grafici dettagliati con tutte le componenti"""
        if self.df_results is None:
            print(f"{Fore.RED}✗ Calcola i dati prima!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Generazione grafici dettagliati...{Style.RESET_ALL}")
        
        # Figura con 4 subplot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle('PRODUCED - Analisi Dettagliata', fontsize=16, fontweight='bold')
        
        # GRAFICO 1: Produced
        ax1.bar(self.df_results['Data'], self.df_results['Produced'], color='steelblue', alpha=0.7)
        ax1.set_ylabel('Produced (hl)', fontweight='bold')
        ax1.set_title('Produced Giornaliero', fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # GRAFICO 2: Componenti Stacked
        ax2.bar(self.df_results['Data'], self.df_results['Packed'], label='Packed', alpha=0.8)
        ax2.bar(self.df_results['Data'], self.df_results['Cisterne']/2, bottom=self.df_results['Packed'], 
                label='Cisterne/2', alpha=0.8)
        ax2.bar(self.df_results['Data'], self.df_results['Delta_Stock']/2, 
                bottom=self.df_results['Packed'] + self.df_results['Cisterne']/2, 
                label='Delta Stock/2', alpha=0.8)
        ax2.set_ylabel('Valore (hl)', fontweight='bold')
        ax2.set_title('Componenti del Produced', fontweight='bold')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # GRAFICO 3: Stock
        ax3.plot(self.df_results['Data'], self.df_results['Stock_Iniziale'], marker='o', label='Stock Iniziale', linewidth=2)
        ax3.plot(self.df_results['Data'], self.df_results['Stock_Finale'], marker='s', label='Stock Finale', linewidth=2)
        ax3.fill_between(self.df_results['Data'], self.df_results['Stock_Iniziale'], self.df_results['Stock_Finale'], alpha=0.3)
        ax3.set_ylabel('Stock (hl std)', fontweight='bold')
        ax3.set_title('Evoluzione Stock', fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax3.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # GRAFICO 4: Settimanale
        weekly_produced = self.df_results.groupby('Week_Year')['Produced'].agg(['sum', 'mean', 'max'])
        x = range(len(weekly_produced))
        width = 0.25
        ax4.bar([i - width for i in x], weekly_produced['sum'], width, label='Totale', alpha=0.8)
        ax4.bar(x, [v*7 for v in weekly_produced['mean']], width, label='Media*7', alpha=0.8)
        ax4.bar([i + width for i in x], weekly_produced['max'], width, label='Massimo', alpha=0.8)
        ax4.set_ylabel('Produced (hl)', fontweight='bold')
        ax4.set_xlabel('Settimana', fontweight='bold')
        ax4.set_title('Statistiche Settimanali', fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(weekly_produced.index, rotation=45, ha='right')
        ax4.legend()
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Salva PNG
        output_path = os.path.join(OUTPUT_DIR, 'produced_grafici_dettagliati.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"{Fore.GREEN}✓ Grafico dettagliato salvato: {output_path}{Style.RESET_ALL}")
        
        plt.close()
    
    def stampa_statistiche_settimanali(self):
        """Stampa statistiche per settimana"""
        if self.df_results is None:
            print(f"{Fore.RED}✗ Calcola i dati prima!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"   STATISTICHE SETTIMANALI")
        print(f"{'='*70}{Style.RESET_ALL}\n")
        
        weekly_stats = self.df_results.groupby('Week_Year').agg({
            'Produced': ['sum', 'mean', 'min', 'max'],
            'Data': ['first', 'last'],
            'Packed': 'sum',
            'Cisterne': 'sum'
        }).round(2)
        
        for week, row in self.df_results.groupby('Week_Year'):
            print(f"{Fore.CYAN}Settimana {week}{Style.RESET_ALL}")
            produced_total = row['Produced'].sum()
            produced_mean = row['Produced'].mean()
            produced_min = row['Produced'].min()
            produced_max = row['Produced'].max()
            date_first = row['Data'].min().strftime('%d-%m-%Y')
            date_last = row['Data'].max().strftime('%d-%m-%Y')
            packed_total = row['Packed'].sum()
            
            print(f"  Periodo:         {date_first} → {date_last}")
            print(f"  Produced Totale: {Fore.GREEN}{produced_total:10.2f}{Style.RESET_ALL} hl")
            print(f"  Produced Media:  {produced_mean:10.2f} hl/giorno")
            print(f"  Produced Min:    {produced_min:10.2f} hl")
            print(f"  Produced Max:    {Fore.YELLOW}{produced_max:10.2f}{Style.RESET_ALL} hl")
            print(f"  Packed Totale:   {packed_total:10.2f} hl")
            print()
        
        print(f"{Fore.CYAN}TOTALE GENERALE{Style.RESET_ALL}")
        print(f"  Giorni:          {len(self.df_results)}")
        print(f"  Produced Totale: {Fore.GREEN}{self.df_results['Produced'].sum():10.2f}{Style.RESET_ALL} hl")
        print(f"  Produced Media:  {self.df_results['Produced'].mean():10.2f} hl/giorno")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}\n")

def main_grafici(csv_path):
    """Funzione principale per generare grafici"""
    grafici = GraficiProduced(csv_path)
    grafici.calcola_produced()
    grafici.genera_grafici()
    grafici.genera_grafici_dettagliati()
    grafici.stampa_statistiche_settimanali()
    
    # Esporta anche i dati
    output_csv = os.path.join(OUTPUT_DIR, 'produced_per_grafici.csv')
    grafici.df_results.to_csv(output_csv, index=False)
    print(f"{Fore.GREEN}✓ Dati per grafici esportati: {output_csv}{Style.RESET_ALL}\n")

if __name__ == '__main__':
    csv_path = os.path.join(OUTPUT_DIR, 'produced.csv')
    
    if not os.path.exists(csv_path):
        print(f"{Fore.RED}✗ File CSV non trovato: {csv_path}{Style.RESET_ALL}")
        sys.exit(1)
    
    main_grafici(csv_path)