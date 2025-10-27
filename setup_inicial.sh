#!/bin/bash

echo "============================================================"
echo "  INSTALACION INICIAL - PROCESADOR DE PARTIDOS DE FUTBOL"
echo "============================================================"
echo ""

# Verificar que estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "ADVERTENCIA: Este script está diseñado para macOS"
    read -p "¿Continuar de todos modos? (s/n): " respuesta
    if [[ "$respuesta" != "s" ]]; then
        exit 1
    fi
fi

# Verificar Python 3
echo "Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    echo "Instala Python 3 desde: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python $PYTHON_VERSION detectado"

# Verificar ffmpeg
echo ""
echo "Verificando ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "ADVERTENCIA: ffmpeg no está instalado"
    echo "ffmpeg es necesario para procesamiento de video"
    echo ""
    echo "Para instalar ffmpeg:"
    echo "1. Instala Homebrew si no lo tienes: https://brew.sh"
    echo "2. Ejecuta: brew install ffmpeg"
    echo ""
    read -p "¿Continuar sin ffmpeg? (s/n): " respuesta
    if [[ "$respuesta" != "s" ]]; then
        exit 1
    fi
else
    echo "ffmpeg detectado"
fi

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Crear entorno virtual
echo ""
echo "Creando entorno virtual Python..."
cd "$SCRIPT_DIR"

if [ -d "futbol_processor_env" ]; then
    echo "El entorno virtual ya existe. Eliminando..."
    rm -rf futbol_processor_env
fi

python3 -m venv futbol_processor_env

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual"
    exit 1
fi

echo "Entorno virtual creado"

# Activar entorno virtual
echo ""
echo "Activando entorno virtual..."
source futbol_processor_env/bin/activate

# Actualizar pip
echo ""
echo "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo ""
echo "Instalando dependencias Python..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Fallo al instalar dependencias"
    deactivate
    exit 1
fi

echo ""
echo "Dependencias instaladas correctamente"

# Crear carpetas necesarias
echo ""
echo "Creando estructura de carpetas..."
mkdir -p ~/futbol_calibracion
mkdir -p ~/futbol_output
mkdir -p ~/Desktop/raw_video_left
mkdir -p ~/Desktop/raw_video_right

echo "Carpetas creadas:"
echo "  - ~/futbol_calibracion (configuraciones de cámaras)"
echo "  - ~/futbol_output (videos procesados)"
echo "  - ~/Desktop/raw_video_left (videos de cámara izquierda)"
echo "  - ~/Desktop/raw_video_right (videos de cámara derecha)"

# Verificar instalación
echo ""
echo "Verificando instalación..."
python3 scripts/verificar_instalacion.py

echo ""
echo "============================================================"
echo "  INSTALACION COMPLETADA"
echo "============================================================"
echo ""
echo "PROXIMOS PASOS:"
echo ""
echo "1. CALIBRAR CAMARAS (una sola vez):"
echo "   ./PROCESAR_PARTIDO.command"
echo "   Opción 1: Calibrar cámaras"
echo ""
echo "2. CONFIGURAR HOMOGRAFIA (una sola vez):"
echo "   ./PROCESAR_PARTIDO.command"
echo "   Opción 2: Configurar homografía"
echo ""
echo "3. CONFIGURAR GOOGLE DRIVE (una sola vez):"
echo "   ./PROCESAR_PARTIDO.command"
echo "   Opción 3: Configurar Google Drive"
echo ""
echo "4. PROCESAR PARTIDOS:"
echo "   - Copia tus videos a ~/Desktop/raw_video_left y raw_video_right"
echo "   - Ejecuta: ./PROCESAR_PARTIDO.command"
echo "   - Opción 4: Procesar partido"
echo ""
echo "============================================================"

deactivate
