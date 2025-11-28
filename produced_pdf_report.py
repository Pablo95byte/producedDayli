#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCED CALCULATOR - Report PDF Completo
Genera report PDF con grafici dettagliati e leggibili per ogni tank
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path
from colorama import Fore, Style
from nan_handler import handle_missing_values

# Rilevamento sistema operativo
IS_WINDOWS = sys.platform.startswith('win')
if IS_WINDOWS:
    # Path fisso per Windows
    CSV_STOCK_PATH = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App\produced_stock_only.csv"
    CSV_PACKED_PATH = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App\packed_hourly.csv"
    CSV_CISTERNE_PATH = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App\cisterne_hourly.csv"
    OUTPUT_DIR = r"C:\Users\arup01\OneDrive - Heineken International\Documents - Dashboard Assemini\General\producedGiornaliero\App"
else:
    CSV_STOCK_PATH = '/mnt/user-data/uploads/produced_stock_only.csv'
    CSV_PACKED_PATH = '/mnt/user-data/uploads/packed_hourly.csv'
    CSV_CISTERNE_PATH = '/mnt/user-data/uploads/cisterne_hourly.csv'
    OUTPUT_DIR = '/mnt/user-data/outputs'

# Importa matplotlib
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib import rcParams
    rcParams['font.size'] = 11
except ImportError:
    print(f"{Fore.RED}⚠️ matplotlib non installato!{Style.RESET_ALL}")
    print("Installa con: pip install matplotlib reportlab")
    sys.exit(1)

class ReportPDFProduced:
    def __init__(self, csv_path=None, df=None, csv_stock_path=None, csv_packed_path=None, csv_cisterne_path=None):
        """
        Inizializza il generatore di report PDF (Triple CSV Mode)

        Args:
            csv_path: Path del CSV unificato (deprecato, per retrocompatibilità GUI)
            df: DataFrame già mergato (usato dalla GUI)
            csv_stock_path: Path CSV Stock (solo BBT/FST/RBT)
            csv_packed_path: Path CSV Packed orario
            csv_cisterne_path: Path CSV Cisterne orario
        """
        self.csv_path = csv_path

        # Se viene passato un DataFrame, usalo direttamente
        if df is not None:
            self.df = df
        # Altrimenti, carica e mergia i 3 CSV
        elif csv_stock_path and csv_packed_path and csv_cisterne_path:
            print("Caricamento CSV Stock (solo BBT/FST/RBT)...")
            df_stock = pd.read_csv(csv_stock_path)

            # Rileva e normalizza il nome della colonna temporale
            time_col = None
            possible_time_cols = ['Time', 'Timestamp', 'DateTime', 'Date', 'time', 'timestamp', 'datetime', 'date']
            for col in possible_time_cols:
                if col in df_stock.columns:
                    time_col = col
                    break

            if time_col is None:
                raise ValueError(
                    f"❌ Colonna temporale non trovata nel CSV Stock!\n"
                    f"Colonne richieste: Time, Timestamp, DateTime, o Date\n"
                    f"Colonne trovate: {', '.join(df_stock.columns)}"
                )

            # Normalizza a 'Time' per compatibilità con il resto del codice
            if time_col != 'Time':
                print(f"  ℹ️  Colonna temporale rilevata: '{time_col}' → rinominata in 'Time'")
                df_stock = df_stock.rename(columns={time_col: 'Time'})

            print("Caricamento CSV Packed (orario)...")
            df_packed = pd.read_csv(csv_packed_path)

            print("Caricamento CSV Cisterne (orario)...")
            df_cisterne = pd.read_csv(csv_cisterne_path)

            print("Aggregazione dati Packed (SOMMA)...")
            packed_daily = self._aggregate_packed_hourly(df_packed)

            print("Aggregazione dati Cisterne (MEDIA)...")
            cisterne_daily = self._aggregate_cisterne_hourly(df_cisterne)

            print("Merge dei 3 DataFrame...")
            self.df = self._merge_stock_packed_cisterne(df_stock, packed_daily, cisterne_daily)

            # Gestione interattiva dei valori NaN
            self.df = handle_missing_values(self.df)
        # Fallback: carica CSV singolo (retrocompatibilità)
        elif csv_path:
            self.df = pd.read_csv(csv_path)

            # Rileva e normalizza il nome della colonna temporale
            time_col = None
            possible_time_cols = ['Time', 'Timestamp', 'DateTime', 'Date', 'time', 'timestamp', 'datetime', 'date']
            for col in possible_time_cols:
                if col in self.df.columns:
                    time_col = col
                    break

            if time_col is None:
                raise ValueError(
                    f"❌ Colonna temporale non trovata nel CSV!\n"
                    f"Colonne richieste: Time, Timestamp, DateTime, o Date\n"
                    f"Colonne trovate: {', '.join(self.df.columns)}"
                )

            # Normalizza a 'Time' per compatibilità con il resto del codice
            if time_col != 'Time':
                print(f"  ℹ️  Colonna temporale rilevata: '{time_col}' → rinominata in 'Time'")
                self.df = self.df.rename(columns={time_col: 'Time'})

            self.df = handle_missing_values(self.df)
        else:
            raise ValueError("Devi fornire df, oppure (csv_stock_path + csv_packed_path + csv_cisterne_path), oppure csv_path")

        self.results = []
        self.df_results = None
        self.data_warning = None  # Warning per dati incompleti

        # Liste tank
        self.BBT_TANKS = [111, 112, 121, 132, 211, 212, 221, 222, 231, 232, 241, 242, 251, 252]
        self.FST_TANKS = [111, 112, 121, 122, 131, 132, 141, 142, 151, 152, 161, 171, 172,
                         211, 212, 221, 222, 231, 232, 241, 242, 243]
        self.RBT_TANKS = [251, 252]

        self.MATERIAL_MAPPING = {
            0: 0, 1: 11.03, 2: 11.03, 3: 11.57, 7: 11.03, 8: 11.57,
            9: 11.68, 10: 11.03, 18: 11.68, 21: 11.68, 22: 11.68, 28: 11.68, 32: 11.03, 36: 11.03
        }

    def _aggregate_packed_hourly(self, df_packed):
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

    def _aggregate_cisterne_hourly(self, df_cisterne):
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

    def _merge_stock_packed_cisterne(self, df_stock, df_packed, df_cisterne):
        """Unisce i 3 DataFrame (Stock, Packed, Cisterne) per data"""
        # Converti Time del DataFrame stock a date
        df_stock['Date'] = pd.to_datetime(df_stock['Time']).dt.date

        # Merge 1: Stock + Packed (left join)
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
    
    def plato_to_volumetric(self, plato):
        if plato == 0:
            return 0
        plato = float(plato)
        grado_v = ((0.0000188792 * plato + 0.003646886) * plato + 1.001077) * plato - 0.01223565
        return grado_v

    def calc_hl_std(self, volume_hl, plato, material):
        try:
            volume_hl = float(volume_hl)
            plato = float(plato)
            material = int(float(material))
        except:
            raise ValueError(f"Valori non validi: volume_hl={volume_hl}, plato={plato}, material={material}")

        if volume_hl == 0 or plato == 0:
            return 0

        grado_vol = self.plato_to_volumetric(plato)
        if grado_vol == 0:
            return 0

        # Material è valido, usa il mapping
        if material not in self.MATERIAL_MAPPING:
            raise ValueError(f"Material {material} non trovato nel mapping")

        grado_std = self.MATERIAL_MAPPING[material]
        if grado_std == 0:
            # Material con grado_std = 0 nel mapping ritorna 0
            return 0

        hl_std = (volume_hl * grado_vol) / grado_std
        return hl_std
    
    def calcola_produced(self):
        """Calcola tutti i produced"""
        print(f"\n{Fore.CYAN}Elaborazione dati per report PDF...{Style.RESET_ALL}")
        
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
            truck1_hl_std = self.calc_hl_std(truck1_level, truck1_plato, 8)

            truck2_plato = float(row['Truck2 Average Plato'])
            truck2_level = float(row['Truck2 Level'])
            truck2_hl_std = self.calc_hl_std(truck2_level, truck2_plato, 8)
            
            cisterne_total = truck1_hl_std + truck2_hl_std
            
            # STOCK INIZIALE
            stock_iniziale = 0
            if idx > 0:
                prev_row = self.df.iloc[idx - 1]
                for tank_num in self.BBT_TANKS:
                    plato_col = f'BBT {tank_num} Average Plato'
                    level_col = f'BBT{tank_num} Level'
                    material_col = f'BBT{tank_num} Material'
                    if plato_col in prev_row.index and level_col in prev_row.index:
                        stock_iniziale += self.calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
                
                for tank_num in self.FST_TANKS:
                    plato_col = f'FST {tank_num} Average Plato'
                    level_col = f'FST{tank_num} Level '
                    material_col = f'FST{tank_num} Material'
                    if plato_col in prev_row.index and level_col in prev_row.index:
                        stock_iniziale += self.calc_hl_std(prev_row[level_col], prev_row[plato_col], prev_row[material_col])
            
            # STOCK FINALE
            stock_finale = 0
            for tank_num in self.BBT_TANKS:
                plato_col = f'BBT {tank_num} Average Plato'
                level_col = f'BBT{tank_num} Level'
                material_col = f'BBT{tank_num} Material'
                if plato_col in row.index and level_col in row.index:
                    stock_finale += self.calc_hl_std(row[level_col], row[plato_col], row[material_col])
            
            for tank_num in self.FST_TANKS:
                plato_col = f'FST {tank_num} Average Plato'
                level_col = f'FST{tank_num} Level '
                material_col = f'FST{tank_num} Material'
                if plato_col in row.index and level_col in row.index:
                    stock_finale += self.calc_hl_std(row[level_col], row[plato_col], row[material_col])
            
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
    
    def estrai_dati_truck(self, truck_num):
        """Estrae dati per un singolo truck (1 o 2)"""
        dati = []

        for idx, row in self.df.iterrows():
            plato_col = f'Truck{truck_num} Average Plato'
            level_col = f'Truck{truck_num} Level'

            if plato_col in row.index and level_col in row.index:
                plato = float(row[plato_col])
                level = float(row[level_col])
                hl_std = self.calc_hl_std(level, plato, 8)  # Material 8 per truck

                dati.append({
                    'Data': pd.to_datetime(row['Time']),
                    'Plato': plato,
                    'Level': level,
                    'hl_std': hl_std
                })

        return pd.DataFrame(dati)
    
    def estrai_dati_tank(self, tank_type, tank_num):
        """Estrae dati per un singolo tank"""
        dati = []

        for idx, row in self.df.iterrows():
            if tank_type == 'BBT':
                plato_col = f'BBT {tank_num} Average Plato'
                level_col = f'BBT{tank_num} Level'
                material_col = f'BBT{tank_num} Material'
            elif tank_type == 'FST':
                plato_col = f'FST {tank_num} Average Plato'
                level_col = f'FST{tank_num} Level '
                material_col = f'FST{tank_num} Material'
            else:  # RBT
                plato_col = f'RBT {tank_num} Average Plato'
                level_col = f'RBT{tank_num} Level'
                material_col = f'RBT{tank_num} Material'

            if plato_col in row.index and level_col in row.index:
                plato = float(row[plato_col])
                level = float(row[level_col])
                material = int(float(row[material_col]))
                hl_std = self.calc_hl_std(level, plato, material)

                dati.append({
                    'Data': pd.to_datetime(row['Time']),
                    'Plato': plato,
                    'Level': level,
                    'Material': material,
                    'hl_std': hl_std
                })

        return pd.DataFrame(dati)
    
    def genera_pdf_report(self):
        """Genera il report PDF completo"""
        if self.df_results is None:
            print(f"{Fore.RED}✗ Calcola i dati prima!{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Generazione report PDF...{Style.RESET_ALL}")

        # Crea cartella report se non esiste
        report_dir = os.path.join(OUTPUT_DIR, 'report')
        os.makedirs(report_dir, exist_ok=True)

        # Nome file con data di generazione
        data_generazione = datetime.now().strftime('%Y-%m-%d')
        filename = f'report_produced_{data_generazione}_PA.pdf'
        output_path = os.path.join(report_dir, filename)
        
        with PdfPages(output_path) as pdf:
            # PAGINA 1: Titolo e Sommario
            self._pagina_titolo(pdf)
            
            # PAGINA 2: Produced Completo
            self._pagina_produced_principale(pdf)
            
            # PAGINA 3-4: Analisi Settimanali
            self._pagina_analisi_settimanali(pdf)
            
            # PAGINE 5+: Grafici Tank BBT
            self._pagine_grafici_bbt(pdf)
            
            # PAGINE: Grafici Tank FST
            self._pagine_grafici_fst(pdf)
            
            # PAGINA: Grafici Truck (Cisterne)
            self._pagine_grafici_truck(pdf)
            
            # PAGINA: Grafici RBT
            self._pagine_grafici_rbt(pdf)
            
            # Metadati PDF
            d = pdf.infodict()
            d['Title'] = 'PRODUCED Report - Analisi Completa'
            d['Author'] = 'Produced Calculator'
            d['Subject'] = 'Analisi Produzione Giornaliera e Settimanale'
            d['CreationDate'] = datetime.now()
        
        print(f"{Fore.GREEN}✓ Report PDF generato: {output_path}{Style.RESET_ALL}\n")
    
    def _pagina_titolo(self, pdf):
        """Pagina titolo del report"""
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Titolo
        ax.text(0.5, 0.95, 'PRODUCED REPORT', 
                ha='center', va='top', fontsize=28, fontweight='bold')
        
        # Sottotitolo
        ax.text(0.5, 0.88, 'Analisi Produzione Giornaliera e Settimanale', 
                ha='center', va='top', fontsize=14, style='italic')
        
        # Data generazione
        ax.text(0.5, 0.80, f'Generato: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}', 
                ha='center', va='top', fontsize=11)
        
        # Separatore
        ax.plot([0.1, 0.9], [0.75, 0.75], 'k-', linewidth=2)
        
        # Statistiche generali
        y_pos = 0.65
        stats_text = f"""
PERIODO DI ANALISI
Data Inizio: {self.df_results['Data'].min().strftime('%d-%m-%Y')}
Data Fine: {self.df_results['Data'].max().strftime('%d-%m-%Y')}
Giorni Elaborati: {len(self.df_results)}

STATISTICHE PRODUCED
Totale: {self.df_results['Produced'].sum():.2f} hl
Media Giornaliera: {self.df_results['Produced'].mean():.2f} hl
Minimo: {self.df_results['Produced'].min():.2f} hl
Massimo: {self.df_results['Produced'].max():.2f} hl

STATISTICHE PACKED
Totale: {self.df_results['Packed'].sum():.2f} hl
Media Giornaliera: {self.df_results['Packed'].mean():.2f} hl

STATISTICHE CISTERNE
Totale: {self.df_results['Cisterne'].sum():.2f} hl
Media Giornaliera: {self.df_results['Cisterne'].mean():.2f} hl
        """
        
        ax.text(0.1, y_pos, stats_text, ha='left', va='top', fontsize=10,
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

        # Aggiungi warning se presente
        if self.data_warning:
            warning_text = "⚠️ ATTENZIONE - DATI INCOMPLETI\n\n" + self.data_warning
            ax.text(0.5, 0.12, warning_text, ha='center', va='top', fontsize=9,
                   family='monospace', color='red',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _pagina_produced_principale(self, pdf):
        """Pagina con grafici principali di produced"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Analisi PRODUCED Giornaliera e Settimanale', fontsize=14, fontweight='bold')
        
        # Grafico 1: Giornaliero (top)
        ax1 = plt.subplot(2, 1, 1)
        bars1 = ax1.bar(self.df_results['Data'], self.df_results['Produced'], 
                        color='steelblue', alpha=0.7, edgecolor='navy', linewidth=0.5)
        
        # Aggiungi valori sopra le barre (solo ogni 3 giorni per leggibilità)
        for i, (date, val) in enumerate(zip(self.df_results['Data'], self.df_results['Produced'])):
            if i % 3 == 0:  # Mostra ogni terzo valore
                ax1.text(date, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        ax1.set_ylabel('Produced (hl)', fontweight='bold', fontsize=11)
        ax1.set_title('Produced Giornaliero', fontweight='bold', fontsize=12)
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Grafico 2: Settimanale (bottom)
        ax2 = plt.subplot(2, 1, 2)
        weekly_produced = self.df_results.groupby('Week_Year')['Produced'].sum()
        bars2 = ax2.bar(range(len(weekly_produced)), weekly_produced.values, 
                        color='darkgreen', alpha=0.7, edgecolor='darkgreen', linewidth=1)
        
        # Aggiungi valori sopra le barre
        for i, val in enumerate(weekly_produced.values):
            ax2.text(i, val, f'{val:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax2.set_xlabel('Settimana', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Produced (hl)', fontweight='bold', fontsize=11)
        ax2.set_title('Produced Settimanale (Aggregato)', fontweight='bold', fontsize=12)
        ax2.set_xticks(range(len(weekly_produced)))
        ax2.set_xticklabels(weekly_produced.index, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _pagina_analisi_settimanali(self, pdf):
        """Pagina con analisi settimanali dettagliate"""
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle('Statistiche Settimanali Dettagliate', fontsize=14, fontweight='bold')
        
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        y_pos = 0.95
        
        for week, group in self.df_results.groupby('Week_Year'):
            produced_sum = group['Produced'].sum()
            produced_mean = group['Produced'].mean()
            produced_min = group['Produced'].min()
            produced_max = group['Produced'].max()
            packed_sum = group['Packed'].sum()
            date_first = group['Data'].min().strftime('%d-%m-%Y')
            date_last = group['Data'].max().strftime('%d-%m-%Y')
            
            text = f"""
{week}  ({date_first} → {date_last})
  Produced Totale: {produced_sum:10.2f} hl  |  Media: {produced_mean:8.2f} hl/giorno  |  Min: {produced_min:8.2f}  |  Max: {produced_max:8.2f}
  Packed Totale: {packed_sum:10.2f} hl
"""
            
            ax.text(0.05, y_pos, text, ha='left', va='top', fontsize=9.5, 
                   family='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
            
            y_pos -= 0.15
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _pagine_grafici_bbt(self, pdf):
        """Genera pagine con grafici per ogni BBT"""
        print(f"{Fore.CYAN}Generazione grafici BBT...{Style.RESET_ALL}")
        
        for tank_num in self.BBT_TANKS:
            df_tank = self.estrai_dati_tank('BBT', tank_num)
            
            if len(df_tank) == 0 or df_tank['Level'].sum() == 0:
                continue  # Salta se non ha dati
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle(f'BBT {tank_num} - Analisi Completa', fontsize=12, fontweight='bold')
            
            # Grafico 1: Level
            bars1 = ax1.bar(df_tank['Data'], df_tank['Level'], color='steelblue', alpha=0.7, edgecolor='navy')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['Level'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax1.text(date, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8)
            ax1.set_ylabel('Level (L)', fontweight='bold')
            ax1.set_title('Level nel Tempo', fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.tick_params(axis='x', rotation=45)
            
            # Grafico 2: Plato
            bars2 = ax2.bar(df_tank['Data'], df_tank['Plato'], color='orange', alpha=0.7, edgecolor='darkorange')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['Plato'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax2.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax2.set_ylabel('Plato (°)', fontweight='bold')
            ax2.set_title('Plato nel Tempo', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.tick_params(axis='x', rotation=45)
            
            # Grafico 3: hl std
            bars3 = ax3.bar(df_tank['Data'], df_tank['hl_std'], color='green', alpha=0.7, edgecolor='darkgreen')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['hl_std'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax3.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax3.set_ylabel('hl std', fontweight='bold')
            ax3.set_title('hl Standard nel Tempo', fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.tick_params(axis='x', rotation=45)
            
            # Grafico 4: Statistiche
            ax4.axis('off')
            stats_text = f"""
BBT {tank_num} - STATISTICHE

Level:
  Media: {df_tank['Level'].mean():.2f} L
  Min: {df_tank['Level'].min():.2f} L
  Max: {df_tank['Level'].max():.2f} L

Plato:
  Media: {df_tank['Plato'].mean():.2f} °
  Min: {df_tank['Plato'].min():.2f} °
  Max: {df_tank['Plato'].max():.2f} °

hl Standard:
  Totale: {df_tank['hl_std'].sum():.2f} hl
  Media: {df_tank['hl_std'].mean():.2f} hl
  Min: {df_tank['hl_std'].min():.2f} hl
  Max: {df_tank['hl_std'].max():.2f} hl

Material: {int(df_tank['Material'].mode()[0]) if len(df_tank) > 0 else 'N/A'}
"""
            ax4.text(0.1, 0.9, stats_text, ha='left', va='top', fontsize=10,
                    family='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    def _pagine_grafici_fst(self, pdf):
        """Genera pagine con grafici per ogni FST"""
        print(f"{Fore.CYAN}Generazione grafici FST...{Style.RESET_ALL}")
        
        for tank_num in self.FST_TANKS:
            df_tank = self.estrai_dati_tank('FST', tank_num)
            
            if len(df_tank) == 0 or df_tank['Level'].sum() == 0:
                continue  # Salta se non ha dati
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle(f'FST {tank_num} - Analisi Completa', fontsize=12, fontweight='bold')
            
            # Grafico 1: Level
            bars1 = ax1.bar(df_tank['Data'], df_tank['Level'], color='steelblue', alpha=0.7, edgecolor='navy')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['Level'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax1.text(date, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8)
            ax1.set_ylabel('Level (L)', fontweight='bold')
            ax1.set_title('Level nel Tempo', fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.tick_params(axis='x', rotation=45)
            
            # Grafico 2: Plato
            bars2 = ax2.bar(df_tank['Data'], df_tank['Plato'], color='orange', alpha=0.7, edgecolor='darkorange')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['Plato'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax2.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax2.set_ylabel('Plato (°)', fontweight='bold')
            ax2.set_title('Plato nel Tempo', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.tick_params(axis='x', rotation=45)
            
            # Grafico 3: hl std
            bars3 = ax3.bar(df_tank['Data'], df_tank['hl_std'], color='green', alpha=0.7, edgecolor='darkgreen')
            for i, (date, val) in enumerate(zip(df_tank['Data'], df_tank['hl_std'])):
                if i % max(1, len(df_tank)//5) == 0:
                    ax3.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax3.set_ylabel('hl std', fontweight='bold')
            ax3.set_title('hl Standard nel Tempo', fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.tick_params(axis='x', rotation=45)
            
            # Grafico 4: Statistiche
            ax4.axis('off')
            stats_text = f"""
FST {tank_num} - STATISTICHE

Level:
  Media: {df_tank['Level'].mean():.2f} L
  Min: {df_tank['Level'].min():.2f} L
  Max: {df_tank['Level'].max():.2f} L

Plato:
  Media: {df_tank['Plato'].mean():.2f} °
  Min: {df_tank['Plato'].min():.2f} °
  Max: {df_tank['Plato'].max():.2f} °

hl Standard:
  Totale: {df_tank['hl_std'].sum():.2f} hl
  Media: {df_tank['hl_std'].mean():.2f} hl
  Min: {df_tank['hl_std'].min():.2f} hl
  Max: {df_tank['hl_std'].max():.2f} hl

Material: {int(df_tank['Material'].mode()[0]) if len(df_tank) > 0 else 'N/A'}
"""
            ax4.text(0.1, 0.9, stats_text, ha='left', va='top', fontsize=10,
                    family='monospace', bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.5))
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

    def _pagine_grafici_truck(self, pdf):
        """Genera pagina con grafici per i truck (cisterne)"""
        print(f"{Fore.CYAN}Generazione grafici Truck...{Style.RESET_ALL}")
        
        for truck_num in [1, 2]:
            df_truck = self.estrai_dati_truck(truck_num)
            
            if len(df_truck) == 0 or df_truck['Level'].sum() == 0:
                continue  # Salta se non ha dati
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8.5))
            fig.suptitle(f'TRUCK {truck_num} - Analisi Completa', fontsize=12, fontweight='bold')
            
            # Grafico 1: Level
            bars1 = ax1.bar(df_truck['Data'], df_truck['Level'], color='steelblue', alpha=0.7, edgecolor='navy')
            for i, (date, val) in enumerate(zip(df_truck['Data'], df_truck['Level'])):
                if i % max(1, len(df_truck)//5) == 0:
                    ax1.text(date, val, f'{val:.0f}', ha='center', va='bottom', fontsize=8)
            ax1.set_ylabel('Level (L)', fontweight='bold')
            ax1.set_title('Level Cisterna nel Tempo', fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.tick_params(axis='x', rotation=45)
            
            # Grafico 2: Plato
            bars2 = ax2.bar(df_truck['Data'], df_truck['Plato'], color='orange', alpha=0.7, edgecolor='darkorange')
            for i, (date, val) in enumerate(zip(df_truck['Data'], df_truck['Plato'])):
                if i % max(1, len(df_truck)//5) == 0:
                    ax2.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax2.set_ylabel('Plato (°)', fontweight='bold')
            ax2.set_title('Plato Medio Cisterna', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.tick_params(axis='x', rotation=45)
            
            # Grafico 3: hl std
            bars3 = ax3.bar(df_truck['Data'], df_truck['hl_std'], color='green', alpha=0.7, edgecolor='darkgreen')
            for i, (date, val) in enumerate(zip(df_truck['Data'], df_truck['hl_std'])):
                if i % max(1, len(df_truck)//5) == 0:
                    ax3.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax3.set_ylabel('hl std', fontweight='bold')
            ax3.set_title('hl Standard Cisterna', fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
            ax3.tick_params(axis='x', rotation=45)
            
            # Grafico 4: Statistiche
            ax4.axis('off')
            stats_text = f"""
TRUCK {truck_num} - STATISTICHE

Level (Liters):
  Media: {df_truck['Level'].mean():.2f} L
  Min: {df_truck['Level'].min():.2f} L
  Max: {df_truck['Level'].max():.2f} L

Plato (°):
  Media: {df_truck['Plato'].mean():.2f} °
  Min: {df_truck['Plato'].min():.2f} °
  Max: {df_truck['Plato'].max():.2f} °

hl Standard:
  Totale: {df_truck['hl_std'].sum():.2f} hl
  Media: {df_truck['hl_std'].mean():.2f} hl
  Min: {df_truck['hl_std'].min():.2f} hl
  Max: {df_truck['hl_std'].max():.2f} hl

Giorni con dati: {len(df_truck[df_truck['Level'] > 0])}
"""
            ax4.text(0.1, 0.9, stats_text, ha='left', va='top', fontsize=10,
                    family='monospace', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
            
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    def _pagine_grafici_rbt(self, pdf):
        """Genera pagina con grafici per gli RBT"""
        print(f"{Fore.CYAN}Generazione grafici RBT...{Style.RESET_ALL}")
        
        # Una pagina con entrambi gli RBT
        df_rbt251 = []
        df_rbt252 = []
        
        for idx, row in self.df.iterrows():
            data = pd.to_datetime(row['Time'])

            # RBT 251
            plato_251 = float(row['RBT 251 Average Plato'])
            material_251 = row['RBT251 Material'] if 'RBT251 Material' in row.index else None
            df_rbt251.append({'Data': data, 'Plato': plato_251, 'Material': material_251})

            # RBT 252
            plato_252 = float(row['RBT 252 Average Plato'])
            material_252 = row['RBT252 Material'] if 'RBT252 Material' in row.index else None
            df_rbt252.append({'Data': data, 'Plato': plato_252, 'Material': material_252})
        
        df_rbt251 = pd.DataFrame(df_rbt251)
        df_rbt252 = pd.DataFrame(df_rbt252)
        
        if len(df_rbt251) == 0 and len(df_rbt252) == 0:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 8.5))
        fig.suptitle('RBT (Serbatoi di Riferimento) - Analisi Plato', fontsize=12, fontweight='bold')
        
        # Grafico RBT 251
        if len(df_rbt251) > 0 and df_rbt251['Plato'].sum() > 0:
            bars1 = ax1.bar(df_rbt251['Data'], df_rbt251['Plato'], color='purple', alpha=0.7, edgecolor='darkviolet')
            for i, (date, val) in enumerate(zip(df_rbt251['Data'], df_rbt251['Plato'])):
                if i % max(1, len(df_rbt251)//5) == 0 and val > 0:
                    ax1.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax1.set_ylabel('Plato (°)', fontweight='bold')
            ax1.set_title('RBT 251 - Plato nel Tempo', fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, 'Nessun dato disponibile', ha='center', va='center', fontsize=12)
            ax1.set_title('RBT 251 - Plato nel Tempo', fontweight='bold')
        
        # Grafico RBT 252
        if len(df_rbt252) > 0 and df_rbt252['Plato'].sum() > 0:
            bars2 = ax2.bar(df_rbt252['Data'], df_rbt252['Plato'], color='coral', alpha=0.7, edgecolor='darkred')
            for i, (date, val) in enumerate(zip(df_rbt252['Data'], df_rbt252['Plato'])):
                if i % max(1, len(df_rbt252)//5) == 0 and val > 0:
                    ax2.text(date, val, f'{val:.1f}', ha='center', va='bottom', fontsize=8)
            ax2.set_ylabel('Plato (°)', fontweight='bold')
            ax2.set_title('RBT 252 - Plato nel Tempo', fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.text(0.5, 0.5, 'Nessun dato disponibile', ha='center', va='center', fontsize=12)
            ax2.set_title('RBT 252 - Plato nel Tempo', fontweight='bold')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
        # Pagina con statistiche RBT
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis('off')
        fig.suptitle('RBT (Serbatoi) - Statistiche Dettagliate', fontsize=14, fontweight='bold')
        
        stats_rbt251 = f"""
RBT 251 - STATISTICHE

Plato (°):
  Media: {df_rbt251['Plato'].mean():.2f} °
  Min: {df_rbt251['Plato'].min():.2f} °
  Max: {df_rbt251['Plato'].max():.2f} °
  Giorni con dati: {len(df_rbt251[df_rbt251['Plato'] > 0])}

Material: {int(df_rbt251['Material'].mode()[0]) if len(df_rbt251) > 0 and pd.notna(df_rbt251['Material'].mode()[0]) else 'N/A'}
"""
        
        stats_rbt252 = f"""
RBT 252 - STATISTICHE

Plato (°):
  Media: {df_rbt252['Plato'].mean():.2f} °
  Min: {df_rbt252['Plato'].min():.2f} °
  Max: {df_rbt252['Plato'].max():.2f} °
  Giorni con dati: {len(df_rbt252[df_rbt252['Plato'] > 0])}

Material: {int(df_rbt252['Material'].mode()[0]) if len(df_rbt252) > 0 and pd.notna(df_rbt252['Material'].mode()[0]) else 'N/A'}
"""
        
        ax.text(0.05, 0.9, stats_rbt251, ha='left', va='top', fontsize=11,
                family='monospace', bbox=dict(boxstyle='round', facecolor='plum', alpha=0.5))
        ax.text(0.55, 0.9, stats_rbt252, ha='left', va='top', fontsize=11,
                family='monospace', bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.5))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

def main_pdf_report(csv_stock_path, csv_packed_path, csv_cisterne_path):
    """Funzione principale per generare report PDF (Triple CSV Mode)"""
    print("="*60)
    print("PRODUCED CALCULATOR - Report PDF (Triple CSV)")
    print("="*60)
    report = ReportPDFProduced(csv_stock_path=csv_stock_path, csv_packed_path=csv_packed_path, csv_cisterne_path=csv_cisterne_path)
    report.calcola_produced()
    report.genera_pdf_report()
    print(f"{Fore.GREEN}✓ Report PDF completato!{Style.RESET_ALL}\n")

if __name__ == '__main__':
    # Prova a trovare i file CSV
    if not os.path.exists(CSV_STOCK_PATH):
        # Cerca nella cartella corrente
        for file in os.listdir('.'):
            if 'stock' in file.lower() and file.endswith('.csv'):
                CSV_STOCK_PATH = os.path.join('.', file)
                break
            elif file == 'produced.csv':
                CSV_STOCK_PATH = os.path.join('.', file)
                break

    if not os.path.exists(CSV_PACKED_PATH):
        # Cerca nella cartella corrente
        for file in os.listdir('.'):
            if 'packed' in file.lower() and file.endswith('.csv'):
                CSV_PACKED_PATH = os.path.join('.', file)
                break

    if not os.path.exists(CSV_CISTERNE_PATH):
        # Cerca nella cartella corrente
        for file in os.listdir('.'):
            if 'cisterne' in file.lower() and file.endswith('.csv'):
                CSV_CISTERNE_PATH = os.path.join('.', file)
                break

    # Verifica esistenza tutti e 3 i CSV
    if not os.path.exists(CSV_STOCK_PATH):
        print(f"{Fore.RED}✗ CSV Stock non trovato: {CSV_STOCK_PATH}{Style.RESET_ALL}")
        print("  Cerca nella cartella corrente file con 'stock' nel nome o 'produced.csv'")
        sys.exit(1)

    if not os.path.exists(CSV_PACKED_PATH):
        print(f"{Fore.RED}✗ CSV Packed non trovato: {CSV_PACKED_PATH}{Style.RESET_ALL}")
        print("  Cerca nella cartella corrente file con 'packed' nel nome")
        sys.exit(1)

    if not os.path.exists(CSV_CISTERNE_PATH):
        print(f"{Fore.RED}✗ CSV Cisterne non trovato: {CSV_CISTERNE_PATH}{Style.RESET_ALL}")
        print("  Cerca nella cartella corrente file con 'cisterne' nel nome")
        sys.exit(1)

    print(f"✓ CSV Stock:    {os.path.basename(CSV_STOCK_PATH)}")
    print(f"✓ CSV Packed:   {os.path.basename(CSV_PACKED_PATH)}")
    print(f"✓ CSV Cisterne: {os.path.basename(CSV_CISTERNE_PATH)}\n")

    main_pdf_report(CSV_STOCK_PATH, CSV_PACKED_PATH, CSV_CISTERNE_PATH)