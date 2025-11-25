"""
Modern UI Theme Configuration for Produced Calculator
Provides color schemes, fonts, and styling for a professional UX
"""

# Color Palette - Modern & Professional
COLORS = {
    # Primary Colors (Blue scheme)
    'primary': '#2C3E50',           # Dark blue-grey
    'primary_light': '#34495E',     # Lighter blue-grey
    'primary_dark': '#1A252F',      # Darker blue-grey

    # Accent Colors
    'accent': '#3498DB',            # Bright blue
    'accent_hover': '#5DADE2',      # Light blue hover
    'accent_dark': '#2874A6',       # Dark blue

    # Success/Info/Warning/Error
    'success': '#27AE60',           # Green
    'info': '#3498DB',              # Blue
    'warning': '#F39C12',           # Orange
    'error': '#E74C3C',             # Red

    # Neutral Colors
    'background': '#ECF0F1',        # Light grey background
    'surface': '#FFFFFF',           # White surface
    'surface_dark': '#F8F9FA',      # Light surface

    # Text Colors
    'text_primary': '#2C3E50',      # Dark text
    'text_secondary': '#7F8C8D',    # Grey text
    'text_disabled': '#BDC3C7',     # Light grey text
    'text_white': '#FFFFFF',        # White text

    # Border & Dividers
    'border': '#D5DBDB',            # Light border
    'border_dark': '#95A5A6',       # Dark border
    'divider': '#E8E8E8',           # Divider line

    # Data Visualization
    'chart_1': '#3498DB',           # Blue
    'chart_2': '#1ABC9C',           # Turquoise
    'chart_3': '#9B59B6',           # Purple
    'chart_4': '#F39C12',           # Orange
    'chart_5': '#E74C3C',           # Red
    'chart_6': '#16A085',           # Dark turquoise
}

# Typography
FONTS = {
    'family_main': 'Segoe UI',
    'family_mono': 'Consolas',
    'family_title': 'Segoe UI Semibold',

    'size_title': 18,
    'size_subtitle': 14,
    'size_heading': 12,
    'size_body': 10,
    'size_small': 9,
    'size_tiny': 8,
}

# Spacing & Layout
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 12,
    'lg': 16,
    'xl': 24,
    'xxl': 32,
}

# Border Radius
RADIUS = {
    'sm': 4,
    'md': 6,
    'lg': 8,
    'xl': 12,
    'round': 50,
}

# Shadows (for visual depth)
SHADOWS = {
    'light': '0 1px 3px rgba(0,0,0,0.12)',
    'medium': '0 3px 6px rgba(0,0,0,0.16)',
    'heavy': '0 10px 20px rgba(0,0,0,0.19)',
}

# Button Styles
BUTTON_STYLES = {
    'primary': {
        'bg': COLORS['accent'],
        'fg': COLORS['text_white'],
        'hover_bg': COLORS['accent_hover'],
        'active_bg': COLORS['accent_dark'],
        'border_width': 0,
        'relief': 'flat',
    },
    'secondary': {
        'bg': COLORS['surface'],
        'fg': COLORS['text_primary'],
        'hover_bg': COLORS['surface_dark'],
        'active_bg': COLORS['border'],
        'border_width': 1,
        'border_color': COLORS['border_dark'],
        'relief': 'flat',
    },
    'success': {
        'bg': COLORS['success'],
        'fg': COLORS['text_white'],
        'hover_bg': '#2ECC71',
        'active_bg': '#229954',
        'border_width': 0,
        'relief': 'flat',
    },
    'danger': {
        'bg': COLORS['error'],
        'fg': COLORS['text_white'],
        'hover_bg': '#EC7063',
        'active_bg': '#C0392B',
        'border_width': 0,
        'relief': 'flat',
    },
}

# Card/Panel Styles
CARD_STYLE = {
    'bg': COLORS['surface'],
    'border_width': 1,
    'border_color': COLORS['border'],
    'relief': 'flat',
    'padding': SPACING['md'],
}

# Tab Styles
TAB_STYLE = {
    'bg': COLORS['surface'],
    'fg': COLORS['text_primary'],
    'selected_bg': COLORS['accent'],
    'selected_fg': COLORS['text_white'],
    'border_width': 0,
}

# Table/Treeview Styles
TABLE_STYLE = {
    'bg': COLORS['surface'],
    'fg': COLORS['text_primary'],
    'heading_bg': COLORS['primary'],
    'heading_fg': COLORS['text_white'],
    'selected_bg': COLORS['accent'],
    'selected_fg': COLORS['text_white'],
    'alternate_row_bg': COLORS['surface_dark'],
}

# Status Bar Style
STATUS_BAR_STYLE = {
    'bg': COLORS['primary_dark'],
    'fg': COLORS['text_white'],
    'height': 28,
}

# Icons (using Unicode symbols for better visual appeal)
ICONS = {
    'folder': '📁',
    'file': '📄',
    'chart': '📊',
    'settings': '⚙️',
    'info': 'ℹ️',
    'warning': '⚠️',
    'error': '❌',
    'success': '✅',
    'refresh': '🔄',
    'download': '💾',
    'upload': '📤',
    'search': '🔍',
    'filter': '🔎',
    'calendar': '📅',
    'clock': '🕐',
    'tank': '🏭',
    'beer': '🍺',
    'truck': '🚛',
    'package': '📦',
    'analytics': '📈',
    'report': '📋',
    'export': '📤',
    'help': '❓',
    'close': '✖️',
    'check': '✓',
    'arrow_right': '→',
    'arrow_left': '←',
    'arrow_up': '↑',
    'arrow_down': '↓',
}

def configure_ttk_style(style):
    """
    Configure ttk.Style with modern theme

    Args:
        style: ttk.Style() instance
    """
    # Configure Notebook (Tabs)
    style.configure('TNotebook',
                   background=COLORS['background'],
                   borderwidth=0)
    style.configure('TNotebook.Tab',
                   background=COLORS['surface'],
                   foreground=COLORS['text_primary'],
                   padding=[SPACING['md'], SPACING['sm']],
                   font=(FONTS['family_main'], FONTS['size_body'], 'bold'))
    style.map('TNotebook.Tab',
             background=[('selected', COLORS['accent'])],
             foreground=[('selected', COLORS['text_white'])])

    # Configure Buttons
    style.configure('TButton',
                   background=COLORS['surface'],
                   foreground=COLORS['text_primary'],
                   borderwidth=1,
                   relief='flat',
                   font=(FONTS['family_main'], FONTS['size_body']))
    style.map('TButton',
             background=[('active', COLORS['surface_dark']),
                        ('pressed', COLORS['border'])])

    # Accent Button (Primary actions)
    style.configure('Accent.TButton',
                   background=COLORS['accent'],
                   foreground=COLORS['text_white'],
                   borderwidth=0,
                   relief='flat',
                   font=(FONTS['family_main'], FONTS['size_body'], 'bold'))
    style.map('Accent.TButton',
             background=[('active', COLORS['accent_hover']),
                        ('pressed', COLORS['accent_dark'])])

    # Success Button
    style.configure('Success.TButton',
                   background=COLORS['success'],
                   foreground=COLORS['text_white'],
                   borderwidth=0,
                   font=(FONTS['family_main'], FONTS['size_body'], 'bold'))

    # Configure Labels
    style.configure('TLabel',
                   background=COLORS['background'],
                   foreground=COLORS['text_primary'],
                   font=(FONTS['family_main'], FONTS['size_body']))

    style.configure('Title.TLabel',
                   font=(FONTS['family_title'], FONTS['size_title'], 'bold'),
                   foreground=COLORS['primary'])

    style.configure('Subtitle.TLabel',
                   font=(FONTS['family_main'], FONTS['size_subtitle']),
                   foreground=COLORS['text_secondary'])

    # Configure Frames
    style.configure('TFrame',
                   background=COLORS['background'])

    style.configure('Card.TFrame',
                   background=COLORS['surface'],
                   relief='flat',
                   borderwidth=1)

    # Configure LabelFrames
    style.configure('TLabelframe',
                   background=COLORS['surface'],
                   foreground=COLORS['text_primary'],
                   borderwidth=1,
                   relief='flat')
    style.configure('TLabelframe.Label',
                   background=COLORS['surface'],
                   foreground=COLORS['primary'],
                   font=(FONTS['family_main'], FONTS['size_heading'], 'bold'))

    # Configure Entry
    style.configure('TEntry',
                   fieldbackground=COLORS['surface'],
                   foreground=COLORS['text_primary'],
                   borderwidth=1,
                   relief='flat')

    # Configure Treeview
    style.configure('Treeview',
                   background=COLORS['surface'],
                   foreground=COLORS['text_primary'],
                   fieldbackground=COLORS['surface'],
                   borderwidth=0,
                   font=(FONTS['family_main'], FONTS['size_body']))
    style.configure('Treeview.Heading',
                   background=COLORS['primary'],
                   foreground=COLORS['text_white'],
                   relief='flat',
                   font=(FONTS['family_main'], FONTS['size_body'], 'bold'))
    style.map('Treeview',
             background=[('selected', COLORS['accent'])],
             foreground=[('selected', COLORS['text_white'])])

    # Configure Progressbar
    style.configure('TProgressbar',
                   background=COLORS['accent'],
                   troughcolor=COLORS['surface_dark'],
                   borderwidth=0,
                   thickness=6)

    # Configure Checkbutton
    style.configure('TCheckbutton',
                   background=COLORS['background'],
                   foreground=COLORS['text_primary'],
                   font=(FONTS['family_main'], FONTS['size_body']))

    # Configure Radiobutton
    style.configure('TRadiobutton',
                   background=COLORS['background'],
                   foreground=COLORS['text_primary'],
                   font=(FONTS['family_main'], FONTS['size_body']))

def get_icon(name):
    """Get icon by name"""
    return ICONS.get(name, '')

def get_color(name):
    """Get color by name"""
    return COLORS.get(name, '#000000')

def get_font(size='body', weight='normal'):
    """Get font tuple (family, size, weight)"""
    family = FONTS['family_main']
    font_size = FONTS.get(f'size_{size}', FONTS['size_body'])
    return (family, font_size, weight)
