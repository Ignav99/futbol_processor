#!/bin/bash
# PIPELINE COMPLETO - Procesar Partido
# Hacer doble clic para procesar un partido automáticamente

source ~/futbol_processor_env/bin/activate

cd "$(dirname "$0")"

python3 procesar_partido_completo.py

echo ""
echo "Presiona cualquier tecla para cerrar..."
read -n 1