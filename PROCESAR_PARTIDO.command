#!/bin/bash
# Script de lanzamiento simple
# Hacer doble clic en este archivo para procesar un partido

source ~/futbol_processor_env/bin/activate

cd ~/futbol_processor/scripts

python3 procesar_partido.py

echo ""
echo "Presiona cualquier tecla para cerrar..."
read -n 1