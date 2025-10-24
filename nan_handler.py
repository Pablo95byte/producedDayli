#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NAN HANDLER - Gestione interattiva dei valori NaN
Rileva i valori mancanti e richiede l'input all'utente
"""

import pandas as pd
import numpy as np
from colorama import Fore, Style, init

init(autoreset=True)

class NaNHandler:
    def __init__(self, df):
        """Inizializza il gestore NaN con un DataFrame"""
        self.df = df
        self.missing_values = {}

    def detect_missing_values(self):
        """Rileva tutti i valori NaN nel DataFrame e ritorna un report dettagliato"""
        missing_report = []

        for idx, row in self.df.iterrows():
            row_date = row.get('Time', f'Riga {idx}')
            row_missing = []

            for col in self.df.columns:
                if col == 'Time':
                    continue

                value = row[col]
                if pd.isna(value) or value == '':
                    row_missing.append({
                        'row_idx': idx,
                        'date': row_date,
                        'column': col,
                        'value': value
                    })

            if row_missing:
                missing_report.extend(row_missing)

        return missing_report

    def print_missing_report(self, missing_report):
        """Stampa un report dei valori mancanti"""
        if not missing_report:
            print(f"\n{Fore.GREEN}✓ Nessun valore mancante rilevato!{Style.RESET_ALL}\n")
            return False

        print(f"\n{Fore.YELLOW}{'='*80}")
        print(f"   VALORI MANCANTI RILEVATI")
        print(f"{'='*80}{Style.RESET_ALL}\n")

        # Raggruppa per data
        from collections import defaultdict
        by_date = defaultdict(list)
        for item in missing_report:
            by_date[item['date']].append(item)

        print(f"{Fore.CYAN}Totale valori mancanti: {len(missing_report)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Giorni con valori mancanti: {len(by_date)}{Style.RESET_ALL}\n")

        for date, items in list(by_date.items())[:5]:  # Mostra solo i primi 5 giorni
            print(f"{Fore.YELLOW}Data: {date}{Style.RESET_ALL}")
            for item in items[:10]:  # Mostra solo le prime 10 colonne per data
                print(f"  - {item['column']}")
            if len(items) > 10:
                print(f"  ... e altri {len(items) - 10} valori mancanti")
            print()

        if len(by_date) > 5:
            print(f"{Fore.YELLOW}... e altri {len(by_date) - 5} giorni con valori mancanti{Style.RESET_ALL}\n")

        return True

    def request_missing_values_interactive(self, missing_report):
        """Chiede all'utente di inserire i valori mancanti in modo interattivo"""
        if not missing_report:
            return self.df

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"   INSERIMENTO VALORI MANCANTI")
        print(f"{'='*80}{Style.RESET_ALL}\n")

        print(f"{Fore.YELLOW}Opzioni disponibili:{Style.RESET_ALL}")
        print("1. Inserisci tutti i valori manualmente (uno per uno)")
        print("2. Usa un valore predefinito per tutti i NaN")
        print("3. Usa forward-fill (propaga ultimo valore valido)")
        print("4. Esci senza modificare (i calcoli potrebbero fallire)")
        print()

        choice = input(f"{Fore.CYAN}Scegli un'opzione (1-4): {Style.RESET_ALL}").strip()

        if choice == '1':
            return self._fill_manually(missing_report)
        elif choice == '2':
            return self._fill_with_default()
        elif choice == '3':
            return self._fill_forward()
        elif choice == '4':
            print(f"\n{Fore.RED}⚠️  ATTENZIONE: Procedere senza riempire i NaN potrebbe causare errori nei calcoli!{Style.RESET_ALL}\n")
            return self.df
        else:
            print(f"\n{Fore.RED}Scelta non valida. Uscita senza modifiche.{Style.RESET_ALL}\n")
            return self.df

    def _fill_manually(self, missing_report):
        """Riempie i valori mancanti chiedendo all'utente uno per uno"""
        print(f"\n{Fore.CYAN}Inserimento manuale dei valori...{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Suggerimento: premi ENTER per saltare (il valore rimarrà NaN){Style.RESET_ALL}\n")

        df_copy = self.df.copy()

        for i, item in enumerate(missing_report):
            if i >= 20:  # Limita a 20 richieste per evitare che diventi troppo lungo
                print(f"\n{Fore.YELLOW}Troppi valori mancanti ({len(missing_report)}). ")
                print(f"Riempiti i primi 20. Per gli altri usa l'opzione 2 o 3.{Style.RESET_ALL}\n")
                break

            row_idx = item['row_idx']
            col = item['column']
            date = item['date']

            print(f"{Fore.CYAN}[{i+1}/{min(20, len(missing_report))}] Data: {date} | Colonna: {col}{Style.RESET_ALL}")
            value = input(f"  Inserisci valore (ENTER per saltare): ").strip()

            if value:
                try:
                    # Tenta di convertire a float
                    value_float = float(value)
                    df_copy.at[row_idx, col] = value_float
                    print(f"  {Fore.GREEN}✓ Valore {value_float} inserito{Style.RESET_ALL}\n")
                except ValueError:
                    print(f"  {Fore.RED}✗ Valore non valido, saltato{Style.RESET_ALL}\n")
            else:
                print(f"  {Fore.YELLOW}⊘ Saltato{Style.RESET_ALL}\n")

        return df_copy

    def _fill_with_default(self):
        """Riempie tutti i NaN con un valore predefinito"""
        print(f"\n{Fore.CYAN}Inserisci il valore predefinito per tutti i NaN:{Style.RESET_ALL}")
        value = input(f"Valore (default 0): ").strip()

        if not value:
            value = 0
        else:
            try:
                value = float(value)
            except ValueError:
                print(f"{Fore.RED}Valore non valido, uso 0{Style.RESET_ALL}")
                value = 0

        df_copy = self.df.fillna(value)
        print(f"\n{Fore.GREEN}✓ Tutti i NaN sono stati sostituiti con {value}{Style.RESET_ALL}\n")
        return df_copy

    def _fill_forward(self):
        """Riempie i NaN con forward-fill (propaga ultimo valore valido)"""
        df_copy = self.df.copy()

        # Forward fill per tutte le colonne numeriche
        for col in df_copy.columns:
            if col != 'Time':
                df_copy[col] = df_copy[col].ffill()
                # Riempie eventuali NaN rimanenti (inizio dataset) con 0
                df_copy[col] = df_copy[col].fillna(0)

        print(f"\n{Fore.GREEN}✓ Forward-fill applicato a tutte le colonne{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  (I NaN rimanenti all'inizio sono stati sostituiti con 0){Style.RESET_ALL}\n")
        return df_copy

    def process(self):
        """Processo completo: rileva, mostra report e richiede valori"""
        missing_report = self.detect_missing_values()
        has_missing = self.print_missing_report(missing_report)

        if not has_missing:
            return self.df

        # Chiedi all'utente come gestire i valori mancanti
        return self.request_missing_values_interactive(missing_report)


def handle_missing_values(df):
    """Funzione di utilità per gestire i valori mancanti in un DataFrame"""
    handler = NaNHandler(df)
    return handler.process()
