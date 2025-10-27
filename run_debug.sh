#!/bin/bash
# Script wrapper per debug senza pandas in ambiente

cd /home/user/producedDayli

# Legge il CSV e analizza manualmente
analyze_date() {
    local target=$1
    echo "=========================================="
    echo "ANALISI PRODUCED - Giorno $target"
    echo "=========================================="
    echo ""

    # Estrai la riga (target + 1 per header)
    local line_num=$((target + 1))
    local data=$(awk -F',' -v row=$line_num 'NR==row {print $1}' produced.csv)
    echo "📅 Data: $data"
    echo ""

    # Packed
    local packed_ow1=$(awk -F',' -v row=$line_num 'NR==row {print $110}' produced.csv)
    local packed_rgb=$(awk -F',' -v row=$line_num 'NR==row {print $111}' produced.csv)
    local packed_ow2=$(awk -F',' -v row=$line_num 'NR==row {print $112}' produced.csv)
    local packed_keg=$(awk -F',' -v row=$line_num 'NR==row {print $113}' produced.csv)

    echo "📦 PACKED:"
    echo "  - OW1: $packed_ow1 hl"
    echo "  - RGB: $packed_rgb hl"
    echo "  - OW2: $packed_ow2 hl"
    echo "  - KEG: $packed_keg hl"
    echo ""

    packed_total=$(echo "$packed_ow1 + $packed_rgb + $packed_ow2 + $packed_keg" | bc)
    echo "  TOTALE PACKED: $packed_total hl"
    echo ""

    echo "Usa la GUI per vedere tutti i dettagli!"
    echo ""
    echo "Comando GUI:"
    echo "  python3 produced_gui.py"
    echo ""
}

if [ -z "$1" ]; then
    echo "Uso: ./run_debug.sh <numero_giorno>"
    echo ""
    echo "Date disponibili:"
    awk -F',' 'NR>1 {print "  " NR-1 ". " $1}' produced.csv | sed 's/ 00:00:00//' | head -10
    echo ""
    exit 1
fi

analyze_date $1
