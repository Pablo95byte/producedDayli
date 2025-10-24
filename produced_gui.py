#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRODUCED CALCULATOR - GUI Application
Interfaccia grafica completa per il calcolo Produced
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from pathlib import Path

# Import moduli esistenti
from nan_handler import NaNHandler
from produced_batch import calc_hl_std, plato_to_volumetric, MATERIAL_MAPPING, BBT_TANKS, FST_TANKS, RBT_TANKS

class ProducedGUI:
    def __init__(self, root):
        """Inizializza l'interfaccia grafica"""
        self.root = root
        self.root.title("Produced Calculator - Dashboard")
        self.root.geometry("1200x800")

        # Variabili di stato
        self.df = None
        self.csv_path = None
        self.results_df = None

        # Crea interfaccia
        self.create_menu_bar()
        self.create_main_interface()
        self.create_status_bar()

    def create_menu_bar(self):
        """Crea la barra dei menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Apri CSV...", command=self.load_csv, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Esporta Risultati CSV...", command=self.export_csv)
        file_menu.add_command(label="Esporta Risultati Excel...", command=self.export_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit, accelerator="Ctrl+Q")

        # Menu Strumenti
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="Ricalcola Tutto", command=self.recalculate_all)
        tools_menu.add_command(label="Test Formule", command=self.show_formula_test)
        tools_menu.add_separator()
        tools_menu.add_command(label="Gestisci NaN", command=self.manage_nan)

        # Menu Aiuto
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Documentazione", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)

        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.load_csv())
        self.root.bind('<Control-q>', lambda e: self.root.quit())

    def create_main_interface(self):
        """Crea l'interfaccia principale con tab"""
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab 1: Carica Dati
        self.tab_load = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_load, text="📂 Carica Dati")
        self.create_load_tab()

        # Tab 2: Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="📊 Dashboard")
        self.create_dashboard_tab()

        # Tab 3: Grafici
        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text="📈 Grafici")
        self.create_charts_tab()

        # Tab 4: Report PDF
        self.tab_pdf = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pdf, text="📄 Report PDF")
        self.create_pdf_tab()

        # Tab 5: Impostazioni
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="⚙️ Impostazioni")
        self.create_settings_tab()

    def create_load_tab(self):
        """Crea il tab per caricare i dati"""
        # Frame principale
        main_frame = ttk.Frame(self.tab_load, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Titolo
        title = ttk.Label(main_frame, text="Caricamento Dati CSV",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Frame selezione file
        file_frame = ttk.LabelFrame(main_frame, text="Seleziona File CSV", padding="10")
        file_frame.pack(fill='x', pady=10)

        self.csv_path_var = tk.StringVar(value="Nessun file selezionato")
        path_label = ttk.Label(file_frame, textvariable=self.csv_path_var,
                              foreground='gray')
        path_label.pack(side='left', padx=5)

        browse_btn = ttk.Button(file_frame, text="Sfoglia...",
                               command=self.browse_csv)
        browse_btn.pack(side='right', padx=5)

        # Frame info dati caricati
        self.info_frame = ttk.LabelFrame(main_frame, text="Informazioni Dati", padding="10")
        self.info_frame.pack(fill='both', expand=True, pady=10)

        self.info_text = tk.Text(self.info_frame, height=15, state='disabled',
                                font=('Courier', 10))
        self.info_text.pack(fill='both', expand=True)

        # Scrollbar per info
        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.info_text.config(yscrollcommand=scrollbar.set)

        # Bottoni azione
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=10)

        load_btn = ttk.Button(action_frame, text="Carica e Analizza",
                             command=self.load_and_analyze,
                             style='Accent.TButton')
        load_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(action_frame, text="Pulisci",
                              command=self.clear_data)
        clear_btn.pack(side='left', padx=5)

    def create_dashboard_tab(self):
        """Crea il tab dashboard con risultati"""
        # Frame principale
        main_frame = ttk.Frame(self.tab_dashboard, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Titolo
        title = ttk.Label(main_frame, text="Dashboard Risultati",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Frame statistiche
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiche Generali", padding="10")
        stats_frame.pack(fill='x', pady=5)

        # Grid per statistiche
        self.stat_labels = {}
        stats = [
            ('Giorni', 'days'),
            ('Produced Totale (hl)', 'total_produced'),
            ('Produced Medio (hl/giorno)', 'avg_produced'),
            ('Packed Totale (hl)', 'total_packed'),
            ('Cisterne Totale (hl)', 'total_cisterne')
        ]

        for i, (label, key) in enumerate(stats):
            ttk.Label(stats_frame, text=f"{label}:", font=('Arial', 10, 'bold')).grid(
                row=i, column=0, sticky='w', padx=5, pady=2)
            self.stat_labels[key] = ttk.Label(stats_frame, text="--",
                                             font=('Arial', 10))
            self.stat_labels[key].grid(row=i, column=1, sticky='w', padx=5, pady=2)

        # Tabella risultati
        table_frame = ttk.LabelFrame(main_frame, text="Risultati Dettagliati", padding="10")
        table_frame.pack(fill='both', expand=True, pady=5)

        # Treeview per tabella
        columns = ('Data', 'Produced', 'Packed', 'Cisterne', 'Stock Iniziale', 'Stock Finale', 'Delta Stock')
        self.results_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120, anchor='center')

        self.results_tree.pack(side='left', fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical',
                                 command=self.results_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.results_tree.config(yscrollcommand=scrollbar.set)

    def create_charts_tab(self):
        """Crea il tab per i grafici"""
        main_frame = ttk.Frame(self.tab_charts, padding="10")
        main_frame.pack(fill='both', expand=True)

        title = ttk.Label(main_frame, text="Grafici",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Frame selezione tipo grafico
        chart_select_frame = ttk.LabelFrame(main_frame, text="Seleziona Grafico", padding="10")
        chart_select_frame.pack(fill='x', pady=5)

        self.chart_var = tk.StringVar(value='produced_daily')
        chart_types = [
            ('Produced Giornaliero', 'produced_daily'),
            ('Produced Settimanale', 'produced_weekly'),
            ('Componenti Stacked', 'components_stacked'),
            ('Evoluzione Stock', 'stock_evolution'),
            ('Tank Specifico', 'tank_specific')
        ]

        for text, value in chart_types:
            ttk.Radiobutton(chart_select_frame, text=text,
                           variable=self.chart_var, value=value,
                           command=self.update_chart).pack(side='left', padx=10)

        # Frame per il grafico (verrà popolato con matplotlib)
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill='both', expand=True, pady=10)

        # Placeholder
        placeholder = ttk.Label(self.chart_frame,
                               text="Carica dati per visualizzare i grafici",
                               font=('Arial', 12))
        placeholder.pack(expand=True)

    def create_pdf_tab(self):
        """Crea il tab per generare PDF"""
        main_frame = ttk.Frame(self.tab_pdf, padding="10")
        main_frame.pack(fill='both', expand=True)

        title = ttk.Label(main_frame, text="Generazione Report PDF",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Opzioni PDF
        options_frame = ttk.LabelFrame(main_frame, text="Opzioni Report", padding="10")
        options_frame.pack(fill='x', pady=10)

        self.pdf_include_charts = tk.BooleanVar(value=True)
        self.pdf_include_tanks = tk.BooleanVar(value=True)
        self.pdf_include_weekly = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Includi grafici principali",
                       variable=self.pdf_include_charts).pack(anchor='w', pady=2)
        ttk.Checkbutton(options_frame, text="Includi dettagli tank",
                       variable=self.pdf_include_tanks).pack(anchor='w', pady=2)
        ttk.Checkbutton(options_frame, text="Includi analisi settimanali",
                       variable=self.pdf_include_weekly).pack(anchor='w', pady=2)

        # Bottone genera
        generate_btn = ttk.Button(main_frame, text="Genera Report PDF",
                                 command=self.generate_pdf,
                                 style='Accent.TButton')
        generate_btn.pack(pady=20)

        # Area log
        log_frame = ttk.LabelFrame(main_frame, text="Log Generazione", padding="10")
        log_frame.pack(fill='both', expand=True, pady=10)

        self.pdf_log = tk.Text(log_frame, height=10, state='disabled',
                              font=('Courier', 9))
        self.pdf_log.pack(fill='both', expand=True)

    def create_settings_tab(self):
        """Crea il tab impostazioni"""
        main_frame = ttk.Frame(self.tab_settings, padding="10")
        main_frame.pack(fill='both', expand=True)

        title = ttk.Label(main_frame, text="Impostazioni",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Material Mapping
        mapping_frame = ttk.LabelFrame(main_frame, text="Mapping Materiali", padding="10")
        mapping_frame.pack(fill='both', expand=True, pady=10)

        # Treeview per mapping
        columns = ('Material ID', 'Grado Standard')
        self.mapping_tree = ttk.Treeview(mapping_frame, columns=columns,
                                        show='headings', height=12)

        for col in columns:
            self.mapping_tree.heading(col, text=col)
            self.mapping_tree.column(col, width=150, anchor='center')

        # Popola con mapping corrente
        for material_id, grado in sorted(MATERIAL_MAPPING.items()):
            self.mapping_tree.insert('', 'end', values=(material_id, f"{grado:.2f}"))

        self.mapping_tree.pack(fill='both', expand=True)

    def create_status_bar(self):
        """Crea la barra di stato"""
        self.status_bar = ttk.Frame(self.root, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')

        self.status_label = ttk.Label(self.status_bar, text="Pronto",
                                     font=('Arial', 9))
        self.status_label.pack(side='left', padx=5)

        self.progress = ttk.Progressbar(self.status_bar, mode='indeterminate',
                                       length=200)

    # ============== METODI DI UTILITÀ ==============

    def set_status(self, message, show_progress=False):
        """Imposta il messaggio nella barra di stato"""
        self.status_label.config(text=message)
        if show_progress:
            self.progress.pack(side='right', padx=5)
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.pack_forget()
        self.root.update_idletasks()

    def update_info_text(self, text):
        """Aggiorna il testo informativo"""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', 'end')
        self.info_text.insert('1.0', text)
        self.info_text.config(state='disabled')

    # ============== FUNZIONI PRINCIPALI ==============

    def browse_csv(self):
        """Apre dialog per selezionare CSV"""
        filename = filedialog.askopenfilename(
            title="Seleziona file CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path = filename
            self.csv_path_var.set(filename)

    def load_csv(self):
        """Carica CSV dal menu"""
        self.browse_csv()
        if self.csv_path:
            self.load_and_analyze()

    def load_and_analyze(self):
        """Carica il CSV e analizza i dati"""
        if not self.csv_path:
            messagebox.showwarning("Attenzione", "Seleziona prima un file CSV")
            return

        try:
            self.set_status("Caricamento CSV in corso...", show_progress=True)

            # Carica CSV
            self.df = pd.read_csv(self.csv_path)

            # Analizza NaN
            handler = NaNHandler(self.df)
            missing_report = handler.detect_missing_values()

            # Mostra info
            info = f"File CSV caricato: {os.path.basename(self.csv_path)}\n"
            info += f"Righe: {len(self.df)}\n"
            info += f"Colonne: {len(self.df.columns)}\n\n"

            if missing_report:
                info += f"⚠️ ATTENZIONE: Rilevati {len(missing_report)} valori NaN!\n\n"
                info += "Giorni con NaN:\n"
                by_date = {}
                for item in missing_report:
                    date = item['date']
                    if date not in by_date:
                        by_date[date] = []
                    by_date[date].append(item['column'])

                for date, cols in list(by_date.items())[:10]:
                    info += f"  {date}: {len(cols)} colonne\n"

                if len(by_date) > 10:
                    info += f"  ... e altri {len(by_date) - 10} giorni\n"

                info += "\nUsa Menu → Strumenti → Gestisci NaN per risolverli"
            else:
                info += "✓ Nessun valore NaN rilevato\n"
                info += "\nDati pronti per l'elaborazione!"

            self.update_info_text(info)
            self.set_status(f"CSV caricato: {len(self.df)} righe")

            # Se non ci sono NaN, calcola automaticamente
            if not missing_report:
                self.recalculate_all()

        except Exception as e:
            self.set_status("Errore durante il caricamento")
            messagebox.showerror("Errore", f"Errore durante il caricamento:\n{str(e)}")

    def manage_nan(self):
        """Gestisce i valori NaN interattivamente"""
        if self.df is None:
            messagebox.showwarning("Attenzione", "Carica prima un file CSV")
            return

        handler = NaNHandler(self.df)
        self.df = handler.process()

        # Aggiorna info
        self.update_info_text("✓ NaN gestiti. Dati pronti per l'elaborazione!")

        # Ricalcola
        self.recalculate_all()

    def recalculate_all(self):
        """Ricalcola tutti i risultati"""
        if self.df is None:
            return

        try:
            self.set_status("Calcolo risultati in corso...", show_progress=True)

            results = []

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
                        if all(col in prev_row.index for col in [plato_col, level_col, material_col]):
                            stock_iniziale += calc_hl_std(prev_row[level_col],
                                                          prev_row[plato_col],
                                                          prev_row[material_col])

                    for tank_num in FST_TANKS:
                        plato_col = f'FST {tank_num} Average Plato'
                        level_col = f'FST{tank_num} Level '
                        material_col = f'FST{tank_num} Material'
                        if all(col in prev_row.index for col in [plato_col, level_col, material_col]):
                            stock_iniziale += calc_hl_std(prev_row[level_col],
                                                          prev_row[plato_col],
                                                          prev_row[material_col])

                # STOCK FINALE
                stock_finale = 0
                for tank_num in BBT_TANKS:
                    plato_col = f'BBT {tank_num} Average Plato'
                    level_col = f'BBT{tank_num} Level'
                    material_col = f'BBT{tank_num} Material'
                    if all(col in row.index for col in [plato_col, level_col, material_col]):
                        stock_finale += calc_hl_std(row[level_col],
                                                    row[plato_col],
                                                    row[material_col])

                for tank_num in FST_TANKS:
                    plato_col = f'FST {tank_num} Average Plato'
                    level_col = f'FST{tank_num} Level '
                    material_col = f'FST{tank_num} Material'
                    if all(col in row.index for col in [plato_col, level_col, material_col]):
                        stock_finale += calc_hl_std(row[level_col],
                                                    row[plato_col],
                                                    row[material_col])

                # PRODUCED
                delta_stock = stock_finale - stock_iniziale
                produced = packed_total + (cisterne_total / 2) + (delta_stock / 2)

                results.append({
                    'Data': row['Time'],
                    'Produced': produced,
                    'Packed': packed_total,
                    'Cisterne': cisterne_total,
                    'Stock_Iniziale': stock_iniziale,
                    'Stock_Finale': stock_finale,
                    'Delta_Stock': delta_stock
                })

            # Salva risultati
            self.results_df = pd.DataFrame(results)

            # Aggiorna dashboard
            self.update_dashboard()

            self.set_status(f"Calcolo completato: {len(results)} giorni elaborati")
            messagebox.showinfo("Successo", f"Calcolo completato!\n{len(results)} giorni elaborati")

        except Exception as e:
            self.set_status("Errore durante il calcolo")
            messagebox.showerror("Errore", f"Errore durante il calcolo:\n{str(e)}")

    def update_dashboard(self):
        """Aggiorna il dashboard con i risultati"""
        if self.results_df is None:
            return

        # Aggiorna statistiche
        self.stat_labels['days'].config(text=str(len(self.results_df)))
        self.stat_labels['total_produced'].config(
            text=f"{self.results_df['Produced'].sum():.2f}")
        self.stat_labels['avg_produced'].config(
            text=f"{self.results_df['Produced'].mean():.2f}")
        self.stat_labels['total_packed'].config(
            text=f"{self.results_df['Packed'].sum():.2f}")
        self.stat_labels['total_cisterne'].config(
            text=f"{self.results_df['Cisterne'].sum():.2f}")

        # Pulisci tabella
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Popola tabella
        for _, row in self.results_df.iterrows():
            self.results_tree.insert('', 'end', values=(
                row['Data'],
                f"{row['Produced']:.2f}",
                f"{row['Packed']:.2f}",
                f"{row['Cisterne']:.2f}",
                f"{row['Stock_Iniziale']:.2f}",
                f"{row['Stock_Finale']:.2f}",
                f"{row['Delta_Stock']:.2f}"
            ))

    def clear_data(self):
        """Pulisce i dati caricati"""
        self.df = None
        self.results_df = None
        self.csv_path = None
        self.csv_path_var.set("Nessun file selezionato")
        self.update_info_text("")
        self.set_status("Pronto")

        # Pulisci statistiche
        for key in self.stat_labels:
            self.stat_labels[key].config(text="--")

        # Pulisci tabella
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def export_csv(self):
        """Esporta risultati in CSV"""
        if self.results_df is None:
            messagebox.showwarning("Attenzione", "Nessun dato da esportare")
            return

        filename = filedialog.asksaveasfilename(
            title="Salva risultati come CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.results_df.to_csv(filename, index=False)
                messagebox.showinfo("Successo", f"Risultati esportati in:\n{filename}")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'esportazione:\n{str(e)}")

    def export_excel(self):
        """Esporta risultati in Excel"""
        if self.results_df is None:
            messagebox.showwarning("Attenzione", "Nessun dato da esportare")
            return

        filename = filedialog.asksaveasfilename(
            title="Salva risultati come Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.results_df.to_excel(filename, index=False, sheet_name='Produced')
                messagebox.showinfo("Successo", f"Risultati esportati in:\n{filename}")
            except Exception as e:
                messagebox.showerror("Errore",
                                   f"Errore durante l'esportazione:\n{str(e)}\n\n"
                                   "Nota: Richiede openpyxl installato")

    def update_chart(self):
        """Aggiorna il grafico visualizzato"""
        # TODO: Implementare con matplotlib
        pass

    def generate_pdf(self):
        """Genera il report PDF"""
        messagebox.showinfo("Info", "Generazione PDF... (da implementare)")

    def show_formula_test(self):
        """Mostra dialog per testare le formule"""
        # TODO: Implementare dialog test
        messagebox.showinfo("Info", "Test formule (da implementare)")

    def show_docs(self):
        """Mostra la documentazione"""
        messagebox.showinfo("Documentazione",
                           "Produced Calculator v2.0\n\n"
                           "Interfaccia grafica per il calcolo Produced.\n\n"
                           "Funzionalità:\n"
                           "- Caricamento CSV con gestione NaN\n"
                           "- Dashboard risultati\n"
                           "- Grafici interattivi\n"
                           "- Esportazione PDF\n"
                           "- Configurazione mapping materiali")

    def show_about(self):
        """Mostra informazioni sull'app"""
        messagebox.showinfo("About",
                           "Produced Calculator GUI\n"
                           "Versione 2.0\n\n"
                           "Sistema di calcolo Produced con interfaccia grafica.\n\n"
                           "Sviluppato con Python + tkinter")


def main():
    """Funzione principale"""
    root = tk.Tk()

    # Stile moderno
    style = ttk.Style()
    style.theme_use('clam')

    # Crea applicazione
    app = ProducedGUI(root)

    # Avvia loop
    root.mainloop()


if __name__ == '__main__':
    main()
