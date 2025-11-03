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
import sys
from pathlib import Path

# Matplotlib per grafici
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Import moduli esistenti
from nan_handler import NaNHandler
from produced_batch import calc_hl_std, plato_to_volumetric, MATERIAL_MAPPING, BBT_TANKS, FST_TANKS, RBT_TANKS

# Rilevamento sistema operativo
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')

class ProducedGUI:
    def __init__(self, root):
        """Inizializza l'interfaccia grafica"""
        self.root = root
        self.root.title("🍺 Produced Calculator - Dashboard Heineken")
        self.root.geometry("1400x900")

        # Configura stile moderno
        self.setup_modern_style()

        # Variabili di stato
        self.df = None
        self.df_packed = None  # DataFrame Packed orario
        self.df_cisterne = None  # DataFrame Cisterne orario
        self.csv_path = None
        self.packed_csv_path = None  # Path CSV Packed
        self.cisterne_csv_path = None  # Path CSV Cisterne
        self.results_df = None
        self.data_warning = None  # Warning per dati incompleti

        # Crea interfaccia
        self.create_menu_bar()
        self.create_main_interface()
        self.create_status_bar()

    def setup_modern_style(self):
        """Configura uno stile moderno e professionale per la GUI"""
        style = ttk.Style()

        # Tema base
        try:
            style.theme_use('clam')  # Tema moderno multi-piattaforma
        except:
            pass  # Se clam non è disponibile, usa il tema di default

        # Colori Heineken professionali
        heineken_green = '#00A74A'      # Verde Heineken principale
        dark_green = '#008037'          # Verde scuro
        light_green = '#E8F5E9'         # Verde chiaro per sfondi
        gray_bg = '#F5F5F5'             # Grigio chiaro per background
        dark_gray = '#424242'           # Grigio scuro per testo
        white = '#FFFFFF'

        # Configura colori di sfondo
        self.root.configure(bg=gray_bg)

        # Stile per Notebook (tabs)
        style.configure('TNotebook', background=gray_bg, borderwidth=0)
        style.configure('TNotebook.Tab',
                       padding=[20, 10],
                       font=('Segoe UI', 11, 'bold'),
                       background=gray_bg,
                       foreground=dark_gray)
        style.map('TNotebook.Tab',
                 background=[('selected', heineken_green), ('active', dark_green)],
                 foreground=[('selected', white), ('active', white)])

        # Stile per Frame
        style.configure('TFrame', background=white)
        style.configure('Card.TFrame',
                       background=white,
                       relief='flat',
                       borderwidth=1)

        # Stile per Label
        style.configure('TLabel',
                       background=white,
                       foreground=dark_gray,
                       font=('Segoe UI', 10))
        style.configure('Title.TLabel',
                       font=('Segoe UI', 16, 'bold'),
                       foreground=heineken_green,
                       background=white)
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11),
                       foreground=dark_gray,
                       background=white)

        # Stile per Button
        style.configure('TButton',
                       font=('Segoe UI', 10, 'bold'),
                       borderwidth=0,
                       focuscolor='none',
                       padding=[15, 8])
        style.map('TButton',
                 background=[('active', dark_green), ('!active', heineken_green)],
                 foreground=[('active', white), ('!active', white)])

        # Stile per Button primario (azioni principali)
        style.configure('Primary.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       borderwidth=0,
                       padding=[20, 10])
        style.map('Primary.TButton',
                 background=[('active', dark_green), ('!active', heineken_green)],
                 foreground=[('active', white), ('!active', white)])

        # Stile per LabelFrame
        style.configure('TLabelframe',
                       background=white,
                       borderwidth=2,
                       relief='solid')
        style.configure('TLabelframe.Label',
                       font=('Segoe UI', 11, 'bold'),
                       foreground=heineken_green,
                       background=white)

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

        # Tab 3: Analisi Giornaliera
        self.tab_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analysis, text="🔍 Analisi Giornaliera")
        self.create_analysis_tab()

        # Tab 4: Grafici
        self.tab_charts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_charts, text="📈 Grafici")
        self.create_charts_tab()

        # Tab 5: Report PDF
        self.tab_pdf = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pdf, text="📄 Report PDF")
        self.create_pdf_tab()

        # Tab 6: Impostazioni
        self.tab_settings = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settings, text="⚙️ Impostazioni")
        self.create_settings_tab()

    def create_load_tab(self):
        """Crea il tab per caricare i dati"""
        # Frame principale
        main_frame = ttk.Frame(self.tab_load, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Titolo
        title = ttk.Label(main_frame, text="📊 Caricamento Dati CSV (Triple Mode)",
                         style='Title.TLabel')
        title.pack(pady=10)

        # Sottotitolo esplicativo
        subtitle = ttk.Label(main_frame,
                            text="Carica 3 file: Stock (giornaliero) + Packed (orario) + Cisterne (orario)",
                            style='Subtitle.TLabel')
        subtitle.pack(pady=5)

        # Frame selezione file 1 - STOCK ONLY
        file_frame1 = ttk.LabelFrame(main_frame, text="1️⃣ CSV Stock Tanks (giornaliero)", padding="10")
        file_frame1.pack(fill='x', pady=10)

        self.csv_path_var = tk.StringVar(value="Nessun file selezionato")
        path_label1 = ttk.Label(file_frame1, textvariable=self.csv_path_var,
                              foreground='gray')
        path_label1.pack(side='left', padx=5)

        browse_btn1 = ttk.Button(file_frame1, text="Sfoglia...",
                               command=self.browse_csv)
        browse_btn1.pack(side='right', padx=5)

        # Frame selezione file 2 - PACKED (OBBLIGATORIO)
        file_frame2 = ttk.LabelFrame(main_frame, text="2️⃣ CSV Packed (orario) ⚠️ OBBLIGATORIO", padding="10")
        file_frame2.pack(fill='x', pady=10)

        self.packed_csv_path_var = tk.StringVar(value="Nessun file selezionato")
        path_label2 = ttk.Label(file_frame2, textvariable=self.packed_csv_path_var,
                              foreground='gray', wraplength=800)
        path_label2.pack(side='left', padx=5)

        browse_btn2 = ttk.Button(file_frame2, text="Sfoglia...",
                               command=self.browse_packed_csv)
        browse_btn2.pack(side='right', padx=5)

        # Frame selezione file 3 - CISTERNE (OBBLIGATORIO)
        file_frame3 = ttk.LabelFrame(main_frame, text="3️⃣ CSV Cisterne (orario) ⚠️ OBBLIGATORIO", padding="10")
        file_frame3.pack(fill='x', pady=10)

        self.cisterne_csv_path_var = tk.StringVar(value="Nessun file selezionato")
        path_label3 = ttk.Label(file_frame3, textvariable=self.cisterne_csv_path_var,
                              foreground='gray', wraplength=800)
        path_label3.pack(side='left', padx=5)

        browse_btn3 = ttk.Button(file_frame3, text="Sfoglia...",
                               command=self.browse_cisterne_csv)
        browse_btn3.pack(side='right', padx=5)

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

        load_btn = ttk.Button(action_frame, text="✨ Carica e Analizza",
                             command=self.load_and_analyze,
                             style='Primary.TButton')
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

        # Frame warning (inizialmente nascosto)
        self.warning_frame = ttk.LabelFrame(main_frame, text="⚠️ AVVISO DATI", padding="10")
        self.warning_label = ttk.Label(self.warning_frame, text="",
                                       foreground='red', font=('Arial', 9),
                                       wraplength=1000, justify='left')
        self.warning_label.pack(fill='x')
        # Non pack il frame ancora - sarà mostrato solo se c'è warning

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

    def create_analysis_tab(self):
        """Crea il tab per l'analisi giornaliera dettagliata"""
        # Frame principale
        main_frame = ttk.Frame(self.tab_analysis, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Titolo
        title = ttk.Label(main_frame, text="Analisi Giornaliera Dettagliata",
                         font=('Arial', 16, 'bold'))
        title.pack(pady=10)

        # Sottotitolo
        subtitle = ttk.Label(main_frame,
                            text="Report completo giorno per giorno: componenti, variazioni e trend",
                            font=('Arial', 9, 'italic'),
                            foreground='gray')
        subtitle.pack(pady=5)

        # Frame controlli
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill='x', pady=5)

        ttk.Button(controls_frame, text="🔄 Aggiorna Analisi",
                  command=self.update_daily_analysis).pack(side='left', padx=5)

        ttk.Button(controls_frame, text="💾 Esporta Report TXT",
                  command=self.export_daily_analysis).pack(side='left', padx=5)

        # Area testo con scrollbar
        text_frame = ttk.LabelFrame(main_frame, text="Report Giornaliero", padding="10")
        text_frame.pack(fill='both', expand=True, pady=5)

        # Scrollbar verticale
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        # Text widget
        self.analysis_text = tk.Text(text_frame, wrap='word',
                                     font=('Courier', 9),
                                     yscrollcommand=scrollbar.set,
                                     height=30)
        self.analysis_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.analysis_text.yview)

        # Tag per colori
        self.analysis_text.tag_configure('header', font=('Courier', 10, 'bold'),
                                        foreground='#2c3e50')
        self.analysis_text.tag_configure('date', font=('Courier', 9, 'bold'),
                                        foreground='#16a085')
        self.analysis_text.tag_configure('increase', foreground='#27ae60')
        self.analysis_text.tag_configure('decrease', foreground='#e74c3c')
        self.analysis_text.tag_configure('neutral', foreground='#95a5a6')
        self.analysis_text.tag_configure('section', font=('Courier', 9, 'bold'))

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
            ('Dettaglio Produced', 'produced_detail'),
            ('Dettaglio Packed', 'packed_detail'),
            ('Dettaglio Truck', 'truck_detail'),
            ('Evoluzione Stock', 'stock_evolution')
        ]

        for text, value in chart_types:
            ttk.Radiobutton(chart_select_frame, text=text,
                           variable=self.chart_var, value=value,
                           command=self.update_chart).pack(side='left', padx=10)

        # Frame per il grafico matplotlib
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_frame.pack(fill='both', expand=True, pady=10)

        # Inizializza canvas matplotlib (vuoto)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Toolbar navigazione matplotlib
        self.toolbar_frame = ttk.Frame(self.chart_frame)
        self.toolbar_frame.pack(fill='x')
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        # Messaggio iniziale
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Carica dati per visualizzare i grafici',
               ha='center', va='center', fontsize=14, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()

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
        generate_btn = ttk.Button(main_frame, text="📄 Genera Report PDF",
                                 command=self.generate_pdf,
                                 style='Primary.TButton')
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
        """Apre dialog per selezionare CSV Stock/Cisterne"""
        filename = filedialog.askopenfilename(
            title="Seleziona CSV Stock/Cisterne (giornaliero)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_path = filename
            self.csv_path_var.set(filename)

    def browse_packed_csv(self):
        """Apre dialog per selezionare CSV Packed orario"""
        filename = filedialog.askopenfilename(
            title="Seleziona CSV Packed (orario)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.packed_csv_path = filename
            self.packed_csv_path_var.set(filename)

    def browse_cisterne_csv(self):
        """Apre dialog per selezionare CSV Cisterne orario"""
        filename = filedialog.askopenfilename(
            title="Seleziona CSV Cisterne (orario)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.cisterne_csv_path = filename
            self.cisterne_csv_path_var.set(filename)

    def load_csv(self):
        """Carica CSV dal menu"""
        self.browse_csv()
        if self.csv_path:
            self.load_and_analyze()

    def load_and_analyze(self):
        """Carica i CSV e analizza i dati"""
        # Verifica che TUTTI i file siano selezionati
        if not self.csv_path:
            messagebox.showwarning("Attenzione", "Seleziona il file CSV Stock (giornaliero)")
            return

        if not self.packed_csv_path:
            messagebox.showwarning("Attenzione",
                                 "Seleziona il file CSV Packed (orario)\n\n"
                                 "Il file Packed è OBBLIGATORIO per calcolare il Produced!")
            return

        if not self.cisterne_csv_path:
            messagebox.showwarning("Attenzione",
                                 "Seleziona il file CSV Cisterne (orario)\n\n"
                                 "Il file Cisterne è OBBLIGATORIO per calcolare il Produced!")
            return

        try:
            self.set_status("Caricamento CSV in corso...", show_progress=True)

            # === CARICA CSV 1: STOCK TANKS (giornaliero) ===
            self.df = pd.read_csv(self.csv_path)

            # === CARICA CSV 2: PACKED (orario) ===
            self.df_packed = pd.read_csv(self.packed_csv_path)

            # === CARICA CSV 3: CISTERNE (orario) ===
            self.df_cisterne = pd.read_csv(self.cisterne_csv_path)

            # === AGGREGA PACKED ORARIO → GIORNALIERO ===
            self.set_status("Aggregazione dati Packed orari...", show_progress=True)
            packed_daily = self._aggregate_packed_hourly()

            # === AGGREGA CISTERNE ORARIO → GIORNALIERO ===
            self.set_status("Aggregazione dati Cisterne orari...", show_progress=True)
            cisterne_daily = self._aggregate_cisterne_hourly()

            # === MERGE DEI TRE DATAFRAME ===
            self.set_status("Unione dati Stock, Packed e Cisterne...", show_progress=True)
            self.df = self._merge_stock_packed_cisterne(self.df, packed_daily, cisterne_daily)

            # Analizza NaN (su DataFrame unito)
            handler = NaNHandler(self.df)
            missing_report = handler.detect_missing_values()

            # Mostra info
            info = f"✅ CSV Stock Tanks: {os.path.basename(self.csv_path)}\n"
            info += f"   Righe: {len(self.df)}\n\n"
            info += f"✅ CSV Packed (orario): {os.path.basename(self.packed_csv_path)}\n"
            info += f"   Righe orarie: {len(self.df_packed)}\n"
            info += f"   Giorni aggregati: {len(packed_daily)}\n\n"
            info += f"✅ CSV Cisterne (orario): {os.path.basename(self.cisterne_csv_path)}\n"
            info += f"   Righe orarie: {len(self.df_cisterne)}\n"
            info += f"   Giorni aggregati: {len(cisterne_daily)}\n\n"

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

    def _aggregate_packed_hourly(self):
        """Aggrega i dati Packed orari in dati giornalieri"""
        # Trova la colonna temporale (può chiamarsi Timestamp, Time, DateTime, etc.)
        time_col = None
        possible_time_cols = ['Timestamp', 'Time', 'DateTime', 'Date', 'timestamp', 'time', 'datetime']

        for col in possible_time_cols:
            if col in self.df_packed.columns:
                time_col = col
                break

        if time_col is None:
            # Usa la prima colonna se non trova nulla
            time_col = self.df_packed.columns[0]
            messagebox.showwarning(
                "Attenzione",
                f"Colonna temporale non trovata nel CSV Packed.\n"
                f"Uso prima colonna: {time_col}\n\n"
                f"Colonne trovate: {', '.join(self.df_packed.columns)}"
            )

        # Converti timestamp a datetime
        try:
            self.df_packed[time_col] = pd.to_datetime(self.df_packed[time_col])
        except Exception as e:
            raise ValueError(
                f"❌ Errore conversione timestamp nella colonna '{time_col}'!\n\n"
                f"Formato richiesto: YYYY-MM-DD HH:MM:SS\n"
                f"Esempio: 2025-10-01 08:00:00\n\n"
                f"Errore: {str(e)}"
            )

        # Estrai solo la data (senza ora)
        self.df_packed['Date'] = self.df_packed[time_col].dt.date

        # Trova colonne Packed (possono avere nomi diversi)
        packed_cols_map = {}
        for orig_name, target_name in [
            ('Packed_OW1', 'Packed OW1'),
            ('Packed_RGB', 'Packed RGB'),
            ('Packed_OW2', 'Packed OW2'),
            ('Packed_KEG', 'Packed KEG'),
            ('OW1', 'Packed OW1'),  # Fallback senza prefisso
            ('RGB', 'Packed RGB'),
            ('OW2', 'Packed OW2'),
            ('KEG', 'Packed KEG')
        ]:
            if orig_name in self.df_packed.columns:
                packed_cols_map[orig_name] = target_name

        if not packed_cols_map:
            raise ValueError(
                f"❌ Colonne Packed non trovate nel CSV!\n\n"
                f"Colonne richieste: Packed_OW1, Packed_RGB, Packed_OW2, Packed_KEG\n"
                f"(oppure: OW1, RGB, OW2, KEG)\n\n"
                f"Colonne trovate nel CSV: {', '.join(self.df_packed.columns)}\n\n"
                f"Verifica il formato del CSV Packed."
            )

        # Aggrega per giorno (somma di tutte le ore)
        agg_dict = {col: 'sum' for col in packed_cols_map.keys()}
        packed_daily = self.df_packed.groupby('Date').agg(agg_dict).reset_index()

        # Rinomina colonne per compatibilità
        packed_daily = packed_daily.rename(columns=packed_cols_map)

        return packed_daily

    def _aggregate_cisterne_hourly(self):
        """Aggrega i dati Cisterne orari in dati giornalieri"""
        # Trova la colonna temporale
        time_col = None
        possible_time_cols = ['Timestamp', 'Time', 'DateTime', 'Date', 'timestamp', 'time', 'datetime']

        for col in possible_time_cols:
            if col in self.df_cisterne.columns:
                time_col = col
                break

        if time_col is None:
            time_col = self.df_cisterne.columns[0]
            messagebox.showwarning(
                "Attenzione",
                f"Colonna temporale non trovata nel CSV Cisterne.\n"
                f"Uso prima colonna: {time_col}\n\n"
                f"Colonne trovate: {', '.join(self.df_cisterne.columns)}"
            )

        # Converti timestamp a datetime
        try:
            self.df_cisterne[time_col] = pd.to_datetime(self.df_cisterne[time_col])
        except Exception as e:
            raise ValueError(
                f"❌ Errore conversione timestamp nella colonna '{time_col}'!\n\n"
                f"Formato richiesto: YYYY-MM-DD HH:MM:SS\n"
                f"Esempio: 2025-10-01 08:00:00\n\n"
                f"Errore: {str(e)}"
            )

        # Estrai solo la data (senza ora)
        self.df_cisterne['Date'] = self.df_cisterne[time_col].dt.date

        # Trova colonne Cisterne (Truck1 e Truck2 con Level e Plato)
        cisterne_cols_map = {}
        for orig_name, target_name in [
            ('Truck1_Level', 'Truck1 Level'),
            ('Truck1Level', 'Truck1 Level'),
            ('Truck1 Level', 'Truck1 Level'),
            ('Truck1_Plato', 'Truck1 Average Plato'),
            ('Truck1Plato', 'Truck1 Average Plato'),
            ('Truck1 Plato', 'Truck1 Average Plato'),
            ('Truck1 Average Plato', 'Truck1 Average Plato'),
            ('Truck2_Level', 'Truck2 Level'),
            ('Truck2Level', 'Truck2 Level'),
            ('Truck2 Level', 'Truck2 Level'),
            ('Truck2_Plato', 'Truck2 Average Plato'),
            ('Truck2Plato', 'Truck2 Average Plato'),
            ('Truck2 Plato', 'Truck2 Average Plato'),
            ('Truck2 Average Plato', 'Truck2 Average Plato'),
        ]:
            if orig_name in self.df_cisterne.columns:
                cisterne_cols_map[orig_name] = target_name

        if not cisterne_cols_map:
            raise ValueError(
                f"❌ Colonne Cisterne non trovate nel CSV!\n\n"
                f"Colonne richieste: Truck1_Level, Truck1_Plato, Truck2_Level, Truck2_Plato\n"
                f"Colonne trovate nel CSV: {', '.join(self.df_cisterne.columns)}\n\n"
                f"Verifica il formato del CSV Cisterne."
            )

        # Aggrega per giorno: SOMMA per Level (volume in hl), MEDIA per Plato (concentrazione)
        # I dati truck CSV sono in hl e devono essere sommati per ottenere il totale giornaliero
        agg_dict = {}
        for col in cisterne_cols_map.keys():
            if 'Level' in col:
                agg_dict[col] = 'sum'  # SOMMA dei volumi
            else:
                agg_dict[col] = 'mean'  # MEDIA del Plato
        cisterne_daily = self.df_cisterne.groupby('Date').agg(agg_dict).reset_index()

        # Rinomina colonne per compatibilità
        cisterne_daily = cisterne_daily.rename(columns=cisterne_cols_map)

        return cisterne_daily

    def _merge_stock_packed_cisterne(self, df_stock, df_packed, df_cisterne):
        """Unisce i 3 DataFrame (Stock, Packed, Cisterne) per data"""
        # Converti Time del DataFrame stock a date
        df_stock['Date'] = pd.to_datetime(df_stock['Time']).dt.date

        # Merge 1: Stock + Packed
        df_merged = df_stock.merge(df_packed, on='Date', how='left')

        # Riempi NaN con 0 per i Packed
        packed_cols = ['Packed OW1', 'Packed RGB', 'Packed OW2', 'Packed KEG']
        for col in packed_cols:
            if col in df_merged.columns:
                df_merged[col] = df_merged[col].fillna(0)

        # Merge 2: (Stock + Packed) + Cisterne
        df_merged = df_merged.merge(df_cisterne, on='Date', how='left')

        # Riempi NaN con 0 per le Cisterne
        cisterne_cols = ['Truck1 Level', 'Truck1 Average Plato', 'Truck2 Level', 'Truck2 Average Plato']
        for col in cisterne_cols:
            if col in df_merged.columns:
                df_merged[col] = df_merged[col].fillna(0)

        # Rimuovi colonna Date temporanea
        df_merged = df_merged.drop('Date', axis=1)

        return df_merged

    def _merge_stock_and_packed(self, df_stock, df_packed):
        """Unisce i DataFrame Stock/Cisterne e Packed per data"""
        # Converti Time del DataFrame stock a date
        df_stock['Date'] = pd.to_datetime(df_stock['Time']).dt.date

        # Merge left join (mantiene tutte le date di Stock, anche se Packed manca)
        df_merged = df_stock.merge(df_packed, on='Date', how='left')

        # Riempi NaN con 0 per i Packed (se una data non ha dati Packed)
        packed_cols = ['Packed OW1', 'Packed RGB', 'Packed OW2', 'Packed KEG']
        for col in packed_cols:
            if col in df_merged.columns:
                df_merged[col] = df_merged[col].fillna(0)

        # Rimuovi colonna Date temporanea
        df_merged = df_merged.drop('Date', axis=1)

        return df_merged

    def manage_nan(self):
        """Gestisce i valori NaN interattivamente"""
        if self.df is None:
            messagebox.showwarning("Attenzione", "Carica prima i file CSV")
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
                    # Packed breakdown
                    'Packed OW1': packed_ow1,
                    'Packed RGB': packed_rgb,
                    'Packed OW2': packed_ow2,
                    'Packed KEG': packed_keg,
                    'Packed': packed_total,
                    # Cisterne breakdown
                    'Truck1 hl_std': truck1_hl_std,
                    'Truck2 hl_std': truck2_hl_std,
                    'Cisterne': cisterne_total,
                    # Stock
                    'Stock_Iniziale': stock_iniziale,
                    'Stock_Finale': stock_finale,
                    'Delta_Stock': delta_stock
                })

            # Salva risultati
            self.results_df = pd.DataFrame(results)

            # Controlla completezza dati
            self._check_data_completeness()

            # Aggiorna dashboard
            self.update_dashboard()

            # Aggiorna grafico
            self.update_chart()

            # Aggiorna analisi giornaliera (automatico, silenzioso)
            if hasattr(self, 'analysis_text'):
                try:
                    report_text = self.generate_daily_analysis_report()
                    self.analysis_text.delete('1.0', tk.END)
                    self.analysis_text.insert('1.0', report_text)
                except Exception as e:
                    print(f"⚠️ Errore aggiornamento analisi: {e}")

            self.set_status(f"Calcolo completato: {len(results)} giorni elaborati")

            # Messaggio successo con eventuale warning
            success_msg = f"Calcolo completato!\n{len(results)} giorni elaborati"
            if self.data_warning:
                success_msg += f"\n\n⚠️ ATTENZIONE:\n{self.data_warning}"
                messagebox.showwarning("Completato con avvisi", success_msg)
            else:
                messagebox.showinfo("Successo", success_msg)

        except Exception as e:
            self.set_status("Errore durante il calcolo")
            messagebox.showerror("Errore", f"Errore durante il calcolo:\n{str(e)}")

    def _check_data_completeness(self):
        """Controlla se i dati sono completi o se manca lo stock iniziale del primo giorno"""
        self.data_warning = None

        if self.results_df is None or len(self.results_df) == 0:
            return

        # Controlla primo giorno
        first_day = self.results_df.iloc[0]

        # Se Stock Iniziale = 0 ma Stock Finale > 0, significa che manca il giorno precedente
        if first_day['Stock_Iniziale'] == 0 and first_day['Stock_Finale'] > 0:
            first_date = pd.to_datetime(first_day['Data']).strftime('%d-%m-%Y')

            # Calcola quale settimana è affetta
            first_week = pd.to_datetime(first_day['Data']).isocalendar().week
            first_year = pd.to_datetime(first_day['Data']).isocalendar().year
            week_label = f"{first_year}-W{str(first_week).zfill(2)}"

            self.data_warning = (
                f"Il primo giorno ({first_date}) ha Stock Iniziale = 0.\n"
                f"Questo indica che il CSV non parte dal giorno 0.\n\n"
                f"⚠️ Il Produced del primo giorno è IMPRECISO.\n"
                f"⚠️ I dati della settimana {week_label} potrebbero essere IMPRECISI.\n\n"
                f"Soluzione: Estrai i dati dal giorno precedente\n"
                f"o ignora il primo giorno/prima settimana nell'analisi."
            )

    def update_dashboard(self):
        """Aggiorna il dashboard con i risultati"""
        if self.results_df is None:
            return

        # Mostra/nascondi warning
        if self.data_warning:
            self.warning_label.config(text=self.data_warning)
            self.warning_frame.pack(fill='x', pady=5, before=self.warning_frame.master.winfo_children()[2])
        else:
            self.warning_frame.pack_forget()

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

        # Configura tag per primo giorno con warning
        self.results_tree.tag_configure('warning', background='#ffcccc')

        # Popola tabella
        for idx, row in self.results_df.iterrows():
            # Marca primo giorno se c'è warning
            tags = ()
            if idx == 0 and self.data_warning:
                tags = ('warning',)

            self.results_tree.insert('', 'end', values=(
                f"⚠️ {row['Data']}" if (idx == 0 and self.data_warning) else row['Data'],
                f"{row['Produced']:.2f}",
                f"{row['Packed']:.2f}",
                f"{row['Cisterne']:.2f}",
                f"{row['Stock_Iniziale']:.2f}",
                f"{row['Stock_Finale']:.2f}",
                f"{row['Delta_Stock']:.2f}"
            ), tags=tags)

    def update_daily_analysis(self):
        """Aggiorna l'analisi giornaliera nel tab (chiamata manuale dal pulsante)"""
        if self.results_df is None or self.df is None:
            messagebox.showwarning("Attenzione", "Carica prima i dati e calcola Produced")
            return

        try:
            # Genera il report
            report_text = self.generate_daily_analysis_report()

            # Mostra nel text widget
            self.analysis_text.delete('1.0', tk.END)
            self.analysis_text.insert('1.0', report_text)

            messagebox.showinfo("Completato", f"Analisi generata per {len(self.results_df)} giorni")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione dell'analisi:\n{str(e)}")

    def generate_daily_analysis_report(self):
        """Genera il testo del report di analisi giornaliera"""
        lines = []
        lines.append("="*100)
        lines.append(" " * 30 + "ANALISI GIORNALIERA DETTAGLIATA - PRODUCED")
        lines.append("="*100)
        lines.append("")

        # Per ogni giorno
        for idx, row in self.results_df.iterrows():
            date_str = pd.to_datetime(row['Data']).strftime('%d/%m/%Y (%A)')

            lines.append("-" * 100)
            lines.append(f"📅 {date_str}")
            lines.append("-" * 100)

            # Produced totale
            produced = row['Produced']
            lines.append(f"")
            lines.append(f"🍺 PRODUCED TOTALE: {produced:,.2f} hl")
            lines.append(f"")

            # Helper per calcolare percentuali (evita divisione per zero)
            def calc_perc(value, total):
                return (value / total * 100) if total != 0 else 0.0

            # === BREAKDOWN COMPONENTI ===
            lines.append("┌─ BREAKDOWN COMPONENTI ─────────────────────────────────────────────────────┐")
            lines.append("│")

            # PACKED
            packed_ow1 = row.get('Packed OW1', 0)
            packed_rgb = row.get('Packed RGB', 0)
            packed_ow2 = row.get('Packed OW2', 0)
            packed_keg = row.get('Packed KEG', 0)
            packed_total = row['Packed']

            lines.append(f"│ 📦 PACKED (imbottigliato/confezionato)")
            lines.append(f"│    OW1:     {packed_ow1:10,.2f} hl  ({calc_perc(packed_ow1, packed_total):5.1f}%)")
            lines.append(f"│    RGB:     {packed_rgb:10,.2f} hl  ({calc_perc(packed_rgb, packed_total):5.1f}%)")
            lines.append(f"│    OW2:     {packed_ow2:10,.2f} hl  ({calc_perc(packed_ow2, packed_total):5.1f}%)")
            lines.append(f"│    KEG:     {packed_keg:10,.2f} hl  ({calc_perc(packed_keg, packed_total):5.1f}%)")
            lines.append(f"│    ────────────────────────────────────")
            lines.append(f"│    TOTALE:  {packed_total:10,.2f} hl  ({calc_perc(packed_total, produced):5.1f}% sul Produced)")
            lines.append(f"│")

            # CISTERNE
            truck1_hl = row.get('Truck1 hl_std', 0)
            truck2_hl = row.get('Truck2 hl_std', 0)
            cisterne_total = row['Cisterne']
            cisterne_contrib = cisterne_total / 2

            lines.append(f"│ 🚛 CISTERNE / 2  (contributo al Produced)")
            lines.append(f"│    Truck1:    {truck1_hl:10,.2f} hl std  ({calc_perc(truck1_hl, cisterne_total):5.1f}%)")
            lines.append(f"│    Truck2:    {truck2_hl:10,.2f} hl std  ({calc_perc(truck2_hl, cisterne_total):5.1f}%)")
            lines.append(f"│    ────────────────────────────────────")
            lines.append(f"│    Totale:    {cisterne_total:10,.2f} hl std")
            lines.append(f"│    /2:        {cisterne_contrib:10,.2f} hl  ({calc_perc(cisterne_contrib, produced):5.1f}% sul Produced)")
            lines.append(f"│")

            # DELTA STOCK
            stock_iniz = row['Stock_Iniziale']
            stock_fin = row['Stock_Finale']
            delta_stock = row['Delta_Stock']
            delta_contrib = delta_stock / 2

            stock_trend = "↗️ AUMENTATO" if delta_stock > 0 else ("↘️ DIMINUITO" if delta_stock < 0 else "➡️ INVARIATO")

            lines.append(f"│ 📊 DELTA STOCK / 2  (variazione magazzino)")
            lines.append(f"│    Stock Iniziale:  {stock_iniz:10,.2f} hl std")
            lines.append(f"│    Stock Finale:    {stock_fin:10,.2f} hl std")
            lines.append(f"│    ────────────────────────")
            lines.append(f"│    Delta:           {delta_stock:10,.2f} hl std  {stock_trend}")
            lines.append(f"│    /2:              {delta_contrib:10,.2f} hl  ({calc_perc(abs(delta_contrib), produced):5.1f}%)")
            lines.append(f"│")
            lines.append(f"└────────────────────────────────────────────────────────────────────────────┘")
            lines.append(f"")

            # === VARIAZIONI RISPETTO AL GIORNO PRECEDENTE ===
            if idx > 0:
                prev_row = self.results_df.iloc[idx - 1]
                prev_produced = prev_row['Produced']
                var_produced = produced - prev_produced
                var_perc = (var_produced / prev_produced * 100) if prev_produced != 0 else 0

                var_trend = "📈 AUMENTO" if var_produced > 0 else ("📉 DIMINUZIONE" if var_produced < 0 else "➡️ STABILE")

                lines.append("┌─ VARIAZIONE vs GIORNO PRECEDENTE ──────────────────────────────────────────┐")
                lines.append("│")
                lines.append(f"│ {var_trend}")
                lines.append(f"│")
                lines.append(f"│ Produced oggi:      {produced:10,.2f} hl")
                lines.append(f"│ Produced ieri:      {prev_produced:10,.2f} hl")
                lines.append(f"│ Variazione:         {var_produced:+10,.2f} hl  ({var_perc:+.1f}%)")
                lines.append(f"│")

                # Variazioni componenti
                var_packed = row['Packed'] - prev_row['Packed']
                var_cisterne = row['Cisterne'] - prev_row['Cisterne']
                var_delta_stock = row['Delta_Stock'] - prev_row['Delta_Stock']

                lines.append(f"│ Dettaglio variazioni:")
                lines.append(f"│   Packed:           {var_packed:+10,.2f} hl")
                lines.append(f"│   Cisterne:         {var_cisterne:+10,.2f} hl")
                lines.append(f"│   Delta Stock:      {var_delta_stock:+10,.2f} hl")
                lines.append(f"│")
                lines.append(f"└────────────────────────────────────────────────────────────────────────────┘")
                lines.append(f"")

            lines.append("")

        # RIEPILOGO FINALE
        lines.append("="*100)
        lines.append(" " * 35 + "RIEPILOGO PERIODO")
        lines.append("="*100)
        lines.append(f"")
        lines.append(f"Giorni analizzati:         {len(self.results_df)}")
        lines.append(f"Produced TOTALE:           {self.results_df['Produced'].sum():,.2f} hl")
        lines.append(f"Produced MEDIO:            {self.results_df['Produced'].mean():,.2f} hl/giorno")
        lines.append(f"Produced MIN:              {self.results_df['Produced'].min():,.2f} hl  ({pd.to_datetime(self.results_df.loc[self.results_df['Produced'].idxmin(), 'Data']).strftime('%d/%m/%Y')})")
        lines.append(f"Produced MAX:              {self.results_df['Produced'].max():,.2f} hl  ({pd.to_datetime(self.results_df.loc[self.results_df['Produced'].idxmax(), 'Data']).strftime('%d/%m/%Y')})")
        lines.append(f"")
        lines.append(f"Packed TOTALE:             {self.results_df['Packed'].sum():,.2f} hl")
        lines.append(f"Cisterne TOTALE:           {self.results_df['Cisterne'].sum():,.2f} hl")
        lines.append(f"Stock Iniziale (1° gg):    {self.results_df.iloc[0]['Stock_Iniziale']:,.2f} hl")
        lines.append(f"Stock Finale (ultimo gg):  {self.results_df.iloc[-1]['Stock_Finale']:,.2f} hl")
        lines.append(f"")
        lines.append("="*100)

        return "\n".join(lines)

    def export_daily_analysis(self):
        """Esporta l'analisi giornaliera in un file TXT"""
        if self.results_df is None:
            messagebox.showwarning("Attenzione", "Carica prima i dati e calcola Produced")
            return

        # Genera report
        report_text = self.generate_daily_analysis_report()

        # Dialog salvataggio
        from tkinter import filedialog
        import os

        # Nome file suggerito
        today = datetime.now().strftime('%Y-%m-%d')
        default_filename = f"analisi_giornaliera_{today}.txt"

        # Determina cartella report
        report_dir = os.path.join(os.getcwd(), 'report')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        filepath = filedialog.asksaveasfilename(
            title="Salva Analisi Giornaliera",
            initialdir=report_dir,
            initialfile=default_filename,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_text)

                messagebox.showinfo("Completato",
                                  f"Analisi esportata con successo!\n\n{filepath}")
            except Exception as e:
                messagebox.showerror("Errore",
                                   f"Errore durante l'esportazione:\n{str(e)}")

    def clear_data(self):
        """Pulisce i dati caricati"""
        self.df = None
        self.df_packed = None
        self.df_cisterne = None
        self.results_df = None
        self.csv_path = None
        self.packed_csv_path = None
        self.cisterne_csv_path = None
        self.csv_path_var.set("Nessun file selezionato")
        self.packed_csv_path_var.set("Nessun file selezionato")
        self.cisterne_csv_path_var.set("Nessun file selezionato")
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
        if self.results_df is None:
            return

        # Pulisci figura
        self.figure.clear()

        chart_type = self.chart_var.get()

        try:
            if chart_type == 'produced_daily':
                self._plot_produced_daily()
            elif chart_type == 'produced_weekly':
                self._plot_produced_weekly()
            elif chart_type == 'components_stacked':
                self._plot_components_stacked()
            elif chart_type == 'produced_detail':
                self._plot_produced_detail()
            elif chart_type == 'packed_detail':
                self._plot_packed_detail()
            elif chart_type == 'truck_detail':
                self._plot_truck_detail()
            elif chart_type == 'stock_evolution':
                self._plot_stock_evolution()

            self.canvas.draw()

        except Exception as e:
            # In caso di errore, mostra messaggio
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Errore nella generazione del grafico:\n{str(e)}',
                   ha='center', va='center', fontsize=12, color='red')
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()

    def _plot_produced_daily(self):
        """Grafico Produced giornaliero con tooltip interattivi"""
        ax = self.figure.add_subplot(111)

        # Converti date per matplotlib
        dates = pd.to_datetime(self.results_df['Data'])

        # Grafico a barre
        bars = ax.bar(dates, self.results_df['Produced'], color='steelblue', alpha=0.7, edgecolor='navy')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('Produced (hl)', fontweight='bold', fontsize=11)
        ax.set_title('Produced Giornaliero (passa il mouse per valori)', fontweight='bold', fontsize=13, pad=15)
        ax.grid(True, alpha=0.3, axis='y')

        # Formattazione date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//15)))
        self.figure.autofmt_xdate(rotation=45)

        # Aggiungi tooltip interattivi
        self._add_bar_tooltips(ax, bars, dates, self.results_df['Produced'])

        # Aggiungi nota se c'è warning sui dati
        if self.data_warning:
            first_week = pd.to_datetime(self.results_df.iloc[0]['Data']).isocalendar().week
            first_year = pd.to_datetime(self.results_df.iloc[0]['Data']).isocalendar().year
            week_label = f"{first_year}-W{str(first_week).zfill(2)}"
            ax.text(0.98, 0.02, f'⚠️ ATTENZIONE: Primo giorno/settimana {week_label} imprecisi (Stock Iniziale = 0)',
                   transform=ax.transAxes, fontsize=8, color='red',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                   ha='right', va='bottom')

        self.figure.tight_layout()

    def _plot_produced_weekly(self):
        """Grafico Produced settimanale con tooltip"""
        ax = self.figure.add_subplot(111)

        # Aggiungi colonna settimana
        df_temp = self.results_df.copy()
        df_temp['Data'] = pd.to_datetime(df_temp['Data'])
        df_temp['Week'] = df_temp['Data'].dt.isocalendar().week
        df_temp['Year'] = df_temp['Data'].dt.isocalendar().year
        df_temp['Week_Year'] = df_temp['Year'].astype(str) + '-W' + df_temp['Week'].astype(str).str.zfill(2)

        # Aggrega per settimana e conta giorni
        weekly_data = df_temp.groupby('Week_Year').agg({
            'Produced': ['sum', 'mean', 'count']
        }).reset_index()
        weekly_data.columns = ['Week_Year', 'Total', 'Mean', 'Days']

        # Grafico a barre
        x = range(len(weekly_data))
        bars = ax.bar(x, weekly_data['Total'], color='darkgreen', alpha=0.7, edgecolor='darkgreen')

        # Aggiungi valori sopra le barre
        for i, val in enumerate(weekly_data['Total']):
            ax.text(i, val, f'{val:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_xlabel('Settimana', fontweight='bold', fontsize=11)
        ax.set_ylabel('Produced (hl)', fontweight='bold', fontsize=11)
        ax.set_title('Produced Settimanale - Hover per media giornaliera', fontweight='bold', fontsize=13, pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(weekly_data['Week_Year'], rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')

        # Tooltip con dettagli (media e giorni)
        self._add_weekly_tooltips(ax, bars, weekly_data)

        # Aggiungi nota se prima settimana è affetta
        if self.data_warning:
            first_week_label = weekly_data.iloc[0]['Week_Year']
            ax.text(0.98, 0.02, f'⚠️ ATTENZIONE: Settimana {first_week_label} potrebbe essere imprecisa (dati incompleti)',
                   transform=ax.transAxes, fontsize=8, color='red',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
                   ha='right', va='bottom')

        self.figure.tight_layout()

    def _plot_components_stacked(self):
        """Grafico componenti stacked con tooltip dettagliati"""
        ax = self.figure.add_subplot(111)

        # Converti date
        dates = pd.to_datetime(self.results_df['Data'])

        # Grafico stacked
        bars1 = ax.bar(dates, self.results_df['Packed'], label='Packed', alpha=0.8, color='#2E86AB')
        bars2 = ax.bar(dates, self.results_df['Cisterne']/2,
               bottom=self.results_df['Packed'],
               label='Cisterne/2', alpha=0.8, color='#A23B72')
        bars3 = ax.bar(dates, self.results_df['Delta_Stock']/2,
               bottom=self.results_df['Packed'] + self.results_df['Cisterne']/2,
               label='Delta Stock/2', alpha=0.8, color='#F18F01')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('Valore (hl)', fontweight='bold', fontsize=11)
        ax.set_title('Componenti del Produced (Stacked) - Hover per dettagli', fontweight='bold', fontsize=13, pad=15)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Formattazione date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//15)))
        self.figure.autofmt_xdate(rotation=45)

        # Aggiungi tooltip dettagliato con breakdown componenti
        self._add_components_tooltips(ax, bars1, dates)

        self.figure.tight_layout()

    def _plot_stock_evolution(self):
        """Grafico evoluzione stock"""
        ax = self.figure.add_subplot(111)

        # Converti date
        dates = pd.to_datetime(self.results_df['Data'])

        # Plot linee
        line1 = ax.plot(dates, self.results_df['Stock_Iniziale'],
                       marker='o', label='Stock Iniziale', linewidth=2,
                       color='#E63946', markersize=4)
        line2 = ax.plot(dates, self.results_df['Stock_Finale'],
                       marker='s', label='Stock Finale', linewidth=2,
                       color='#06A77D', markersize=4)

        # Fill between
        ax.fill_between(dates,
                       self.results_df['Stock_Iniziale'],
                       self.results_df['Stock_Finale'],
                       alpha=0.2, color='gray')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('Stock (hl std)', fontweight='bold', fontsize=11)
        ax.set_title('Evoluzione Stock', fontweight='bold', fontsize=13, pad=15)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Formattazione date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//15)))
        self.figure.autofmt_xdate(rotation=45)

        self.figure.tight_layout()

    def generate_pdf(self):
        """Genera il report PDF"""
        if self.results_df is None:
            messagebox.showwarning("Attenzione", "Calcola prima i risultati")
            return

        try:
            # Log inizio
            self._pdf_log("Inizio generazione report PDF...")
            self.set_status("Generazione PDF in corso...", show_progress=True)

            # Importa modulo PDF
            from produced_pdf_report import ReportPDFProduced

            # Crea report con i dati già caricati (passa DataFrame direttamente)
            self._pdf_log("Inizializzazione report...")
            report = ReportPDFProduced(csv_path=self.csv_path, df=self.df.copy())

            # Calcola produced (usa i risultati già calcolati)
            self._pdf_log("Preparazione dati per PDF...")
            report.results = self.results_df.to_dict('records')
            report.df_results = self.results_df.copy()
            report.data_warning = self.data_warning  # Passa warning al PDF

            # Aggiungi colonne settimana se mancano
            if 'Week' not in report.df_results.columns:
                report.df_results['Data'] = pd.to_datetime(report.df_results['Data'])
                report.df_results['Week'] = report.df_results['Data'].dt.isocalendar().week
                report.df_results['Year'] = report.df_results['Data'].dt.isocalendar().year
                report.df_results['Week_Year'] = (report.df_results['Year'].astype(str) + '-W' +
                                                   report.df_results['Week'].astype(str).str.zfill(2))

            # Genera PDF
            self._pdf_log("Generazione pagine PDF...")
            self._pdf_log("  - Pagina titolo")
            self._pdf_log("  - Grafici principali")

            if self.pdf_include_weekly.get():
                self._pdf_log("  - Analisi settimanali")

            if self.pdf_include_tanks.get():
                self._pdf_log("  - Dettagli tank BBT")
                self._pdf_log("  - Dettagli tank FST")
                self._pdf_log("  - Dettagli truck")

            report.genera_pdf_report()

            # Determina il percorso del file generato
            from datetime import datetime
            data_generazione = datetime.now().strftime('%Y-%m-%d')
            filename = f'report_produced_{data_generazione}_PA.pdf'

            # Usa la cartella corrente dello script come base (portabile)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(script_dir, 'output')

            report_dir = os.path.join(base_dir, 'report')
            pdf_path = os.path.join(report_dir, filename)

            # Se non esiste, cerca nella cartella del CSV Stock
            if not os.path.exists(pdf_path) and self.stock_csv_path:
                report_dir = os.path.join(os.path.dirname(self.stock_csv_path), 'report')
                pdf_path = os.path.join(report_dir, filename)

            self._pdf_log(f"\n✓ Report PDF generato con successo!")
            self._pdf_log(f"  Nome file: {filename}")
            self._pdf_log(f"  Cartella: {report_dir}")

            self.set_status("Report PDF generato")
            messagebox.showinfo("Successo",
                               f"Report PDF generato con successo!\n\n"
                               f"File: {filename}\n"
                               f"Cartella: report/\n"
                               f"Percorso completo:\n{pdf_path}")

        except ImportError as e:
            self._pdf_log(f"\n✗ ERRORE: Modulo non trovato")
            self._pdf_log(f"  {str(e)}")
            self.set_status("Errore: modulo mancante")
            messagebox.showerror("Errore",
                               "Modulo produced_pdf_report.py non trovato!\n"
                               "Assicurati che sia nella stessa cartella.")
        except Exception as e:
            self._pdf_log(f"\n✗ ERRORE durante la generazione:")
            self._pdf_log(f"  {str(e)}")
            self.set_status("Errore generazione PDF")
            messagebox.showerror("Errore", f"Errore durante la generazione PDF:\n{str(e)}")

    def _pdf_log(self, message):
        """Aggiunge messaggio al log PDF"""
        self.pdf_log.config(state='normal')
        self.pdf_log.insert('end', message + '\n')
        self.pdf_log.see('end')
        self.pdf_log.config(state='disabled')
        self.root.update_idletasks()

    def _add_bar_tooltips(self, ax, bars, dates, values, label='Produced'):
        """Aggiunge tooltip interattivi alle barre del grafico"""
        # Crea annotazione (inizialmente invisibile)
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.9),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=9, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            """Gestisce evento hover del mouse"""
            if event.inaxes == ax:
                # Trova la barra sotto il cursore
                for i, (bar, date, val) in enumerate(zip(bars, dates, values)):
                    if bar.contains(event)[0]:
                        # Aggiorna posizione e testo dell'annotazione
                        x = bar.get_x() + bar.get_width() / 2
                        y = bar.get_height()
                        annot.xy = (x, y)

                        # Formatta data
                        date_str = pd.to_datetime(date).strftime('%d-%m-%Y')
                        text = f"{date_str}\n{label}: {val:.2f} hl"
                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                # Se non c'è nessuna barra sotto il cursore, nascondi tooltip
                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        # Collega evento
        self.canvas.mpl_connect("motion_notify_event", hover)

    def _add_weekly_tooltips(self, ax, bars, weekly_data):
        """Aggiunge tooltip dettagliati per grafico settimanale"""
        # Crea annotazione
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="lightgreen", alpha=0.9),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=9, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            """Gestisce evento hover del mouse"""
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2
                        y = bar.get_height()
                        annot.xy = (x, y)

                        # Dati settimana
                        week = weekly_data.iloc[i]
                        text = f"{week['Week_Year']}\n"
                        text += f"Totale: {week['Total']:.2f} hl\n"
                        text += f"Media: {week['Mean']:.2f} hl/giorno\n"
                        text += f"Giorni: {int(week['Days'])}"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)

    def _add_components_tooltips(self, ax, bars, dates):
        """Tooltip dettagliato con breakdown di tutte le componenti"""
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="lightblue", alpha=0.95),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=8, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2
                        y = self.results_df.iloc[i]['Produced']  # Top della barra totale
                        annot.xy = (x, y)

                        # Dati componenti
                        row = self.results_df.iloc[i]
                        date_str = pd.to_datetime(row['Data']).strftime('%d-%m-%Y')

                        packed = row['Packed']
                        cisterne = row['Cisterne'] / 2
                        delta_stock = row['Delta_Stock'] / 2
                        produced = row['Produced']

                        # Helper per percentuali
                        def perc(val):
                            return (val / produced * 100) if produced != 0 else 0.0

                        text = f"{date_str}\n"
                        text += f"━━━━━━━━━━━━━━━━━━━\n"
                        text += f"PRODUCED: {produced:.2f} hl\n"
                        text += f"━━━━━━━━━━━━━━━━━━━\n"
                        text += f"Packed:       {packed:8.2f} hl ({perc(packed):5.1f}%)\n"
                        text += f"Cisterne/2:   {cisterne:8.2f} hl ({perc(cisterne):5.1f}%)\n"
                        text += f"ΔStock/2:     {delta_stock:8.2f} hl ({perc(delta_stock):5.1f}%)"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)

    def _plot_packed_detail(self):
        """Grafico dettagliato componenti Packed (OW1, RGB, OW2, KEG)"""
        ax = self.figure.add_subplot(111)

        # Converti date
        dates = pd.to_datetime(self.results_df['Data'])

        # Estrai componenti Packed
        packed_ow1 = self.results_df['Packed OW1']
        packed_rgb = self.results_df['Packed RGB']
        packed_ow2 = self.results_df['Packed OW2']
        packed_keg = self.results_df['Packed KEG']

        # Grafico stacked
        bars1 = ax.bar(dates, packed_ow1, label='OW1', alpha=0.9, color='#FF6B6B')
        bars2 = ax.bar(dates, packed_rgb, bottom=packed_ow1,
                      label='RGB', alpha=0.9, color='#4ECDC4')
        bars3 = ax.bar(dates, packed_ow2, bottom=packed_ow1 + packed_rgb,
                      label='OW2', alpha=0.9, color='#45B7D1')
        bars4 = ax.bar(dates, packed_keg,
                      bottom=packed_ow1 + packed_rgb + packed_ow2,
                      label='KEG', alpha=0.9, color='#FFA07A')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('Packed (hl)', fontweight='bold', fontsize=11)
        ax.set_title('Dettaglio Packed per Tipologia - Hover per valori', fontweight='bold', fontsize=13, pad=15)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Formattazione date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//15)))
        self.figure.autofmt_xdate(rotation=45)

        # Tooltip dettagliato
        self._add_packed_detail_tooltips(ax, bars1, dates, packed_ow1, packed_rgb, packed_ow2, packed_keg)

        self.figure.tight_layout()

    def _add_packed_detail_tooltips(self, ax, bars, dates, ow1, rgb, ow2, keg):
        """Tooltip per grafico dettaglio Packed"""
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.95),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=8, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2
                        y = ow1.iloc[i] + rgb.iloc[i] + ow2.iloc[i] + keg.iloc[i]
                        annot.xy = (x, y)

                        date_str = pd.to_datetime(dates.iloc[i]).strftime('%d-%m-%Y')

                        v_ow1 = ow1.iloc[i]
                        v_rgb = rgb.iloc[i]
                        v_ow2 = ow2.iloc[i]
                        v_keg = keg.iloc[i]
                        total = v_ow1 + v_rgb + v_ow2 + v_keg

                        def perc(val):
                            return (val / total * 100) if total != 0 else 0.0

                        text = f"{date_str}\n"
                        text += f"━━━━━━━━━━━━━━━━━━━\n"
                        text += f"PACKED TOT: {total:.2f} hl\n"
                        text += f"━━━━━━━━━━━━━━━━━━━\n"
                        text += f"OW1:  {v_ow1:8.2f} hl ({perc(v_ow1):5.1f}%)\n"
                        text += f"RGB:  {v_rgb:8.2f} hl ({perc(v_rgb):5.1f}%)\n"
                        text += f"OW2:  {v_ow2:8.2f} hl ({perc(v_ow2):5.1f}%)\n"
                        text += f"KEG:  {v_keg:8.2f} hl ({perc(v_keg):5.1f}%)"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)

    def _plot_produced_detail(self):
        """Grafico dettagliato breakdown Produced (Packed + Cisterne/2 + ΔStock/2)"""
        ax = self.figure.add_subplot(111)

        # Converti date
        dates = pd.to_datetime(self.results_df['Data'])

        # Estrai componenti
        packed = self.results_df['Packed']
        cisterne_half = self.results_df['Cisterne'] / 2
        delta_stock_half = self.results_df['Delta_Stock'] / 2

        # Per gestire ΔStock negativi, separiamo i positivi dai negativi
        delta_positive = delta_stock_half.clip(lower=0)
        delta_negative = delta_stock_half.clip(upper=0)

        # Grafico stacked per componenti positivi
        bars1 = ax.bar(dates, packed, label='Packed', alpha=0.9, color='#4A90E2')
        bars2 = ax.bar(dates, cisterne_half, bottom=packed,
                      label='Cisterne/2', alpha=0.9, color='#F5A623')
        bars3 = ax.bar(dates, delta_positive, bottom=packed + cisterne_half,
                      label='ΔStock/2 (positivo)', alpha=0.9, color='#7ED321')

        # Barre separate per ΔStock negativi (partono da Packed + Cisterne/2)
        bars4 = ax.bar(dates, delta_negative, bottom=packed + cisterne_half,
                      label='ΔStock/2 (negativo)', alpha=0.9, color='#D0021B')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('Produced (hl)', fontweight='bold', fontsize=11)
        ax.set_title('Breakdown Produced - Hover per dettagli', fontweight='bold', fontsize=13, pad=15)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Formattazione date
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//15)))
        self.figure.autofmt_xdate(rotation=45)

        # Tooltip dettagliato
        self._add_produced_detail_tooltips(ax, bars1, dates, packed, cisterne_half, delta_stock_half)

        self.figure.tight_layout()

    def _add_produced_detail_tooltips(self, ax, bars, dates, packed, cisterne_half, delta_stock_half):
        """Tooltip per grafico breakdown Produced"""
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.95),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=9, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2

                        date_str = pd.to_datetime(dates.iloc[i]).strftime('%d-%m-%Y')

                        v_packed = packed.iloc[i]
                        v_cisterne = cisterne_half.iloc[i]
                        v_delta = delta_stock_half.iloc[i]
                        produced = v_packed + v_cisterne + v_delta
                        y = produced

                        annot.xy = (x, y)

                        def perc(val):
                            return (val / produced * 100) if produced != 0 else 0.0

                        text = f"{date_str}\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"PRODUCED:      {produced:8.2f} hl\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"Packed:        {v_packed:8.2f} hl ({perc(v_packed):5.1f}%)\n"
                        text += f"Cisterne/2:    {v_cisterne:8.2f} hl ({perc(v_cisterne):5.1f}%)\n"
                        text += f"ΔStock/2:      {v_delta:+8.2f} hl ({perc(abs(v_delta)):5.1f}%)"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)

    def _plot_truck_detail(self):
        """Grafico dettagliato confronto Truck1 vs Truck2"""
        ax = self.figure.add_subplot(111)

        # Converti date
        dates = pd.to_datetime(self.results_df['Data'])

        # Estrai valori Truck
        truck1 = self.results_df['Truck1 hl_std']
        truck2 = self.results_df['Truck2 hl_std']

        # Larghezza barre
        width = 0.35
        x = range(len(dates))

        # Barre affiancate
        bars1 = ax.bar([i - width/2 for i in x], truck1, width,
                       label='Truck 1', alpha=0.9, color='#3498DB')
        bars2 = ax.bar([i + width/2 for i in x], truck2, width,
                       label='Truck 2', alpha=0.9, color='#2ECC71')

        ax.set_xlabel('Data', fontweight='bold', fontsize=11)
        ax.set_ylabel('hl standard', fontweight='bold', fontsize=11)
        ax.set_title('Dettaglio Cisterne: Truck1 vs Truck2 - Hover per valori', fontweight='bold', fontsize=13, pad=15)
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')

        # Formattazione date
        ax.set_xticks(x)
        date_labels = [d.strftime('%d-%m') for d in dates]
        ax.set_xticklabels(date_labels, rotation=45, ha='right')

        # Salta etichette se troppe
        if len(dates) > 15:
            for i, label in enumerate(ax.xaxis.get_ticklabels()):
                if i % (len(dates) // 15 + 1) != 0:
                    label.set_visible(False)

        # Tooltip dettagliato
        self._add_truck_detail_tooltips(ax, bars1, bars2, dates, truck1, truck2)

        self.figure.tight_layout()

    def _add_truck_detail_tooltips(self, ax, bars1, bars2, dates, truck1, truck2):
        """Tooltip per grafico Truck detail"""
        annot = ax.annotate("", xy=(0, 0), xytext=(10, 10),
                           textcoords="offset points",
                           bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.95),
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
                           fontsize=9, fontweight='bold')
        annot.set_visible(False)

        def hover(event):
            if event.inaxes == ax:
                # Controlla Truck1
                for i, bar in enumerate(bars1):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2
                        y = truck1.iloc[i]
                        annot.xy = (x, y)

                        date_str = pd.to_datetime(dates.iloc[i]).strftime('%d-%m-%Y')
                        v_t1 = truck1.iloc[i]
                        v_t2 = truck2.iloc[i]
                        total = v_t1 + v_t2

                        def perc(val):
                            return (val / total * 100) if total != 0 else 0.0

                        text = f"{date_str}\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"🚛 TRUCK 1\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"{v_t1:8.2f} hl std\n"
                        text += f"({perc(v_t1):5.1f}% del totale)\n"
                        text += f"\n"
                        text += f"Totale Cisterne: {total:8.2f} hl"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                # Controlla Truck2
                for i, bar in enumerate(bars2):
                    if bar.contains(event)[0]:
                        x = bar.get_x() + bar.get_width() / 2
                        y = truck2.iloc[i]
                        annot.xy = (x, y)

                        date_str = pd.to_datetime(dates.iloc[i]).strftime('%d-%m-%Y')
                        v_t1 = truck1.iloc[i]
                        v_t2 = truck2.iloc[i]
                        total = v_t1 + v_t2

                        def perc(val):
                            return (val / total * 100) if total != 0 else 0.0

                        text = f"{date_str}\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"🚛 TRUCK 2\n"
                        text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                        text += f"{v_t2:8.2f} hl std\n"
                        text += f"({perc(v_t2):5.1f}% del totale)\n"
                        text += f"\n"
                        text += f"Totale Cisterne: {total:8.2f} hl"

                        annot.set_text(text)
                        annot.set_visible(True)
                        self.canvas.draw_idle()
                        return

                if annot.get_visible():
                    annot.set_visible(False)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect("motion_notify_event", hover)

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
