#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from config_utils import obtener_carpeta_configuracion

def main():
    print("\n" + "="*60)
    print("VERIFICACION DE INSTALACION")
    print("="*60)
    
    # Verificar Python
    version = sys.version_info
    print(f"\nPython: {version.major}.{version.minor}.{version.micro}")
    
    # Verificar librerías
    print("\nLibrerias instaladas:")
    
    try:
        import cv2
        print(f"  OK: OpenCV")
    except ImportError:
        print(f"  FALTA: OpenCV")
    
    try:
        import numpy
        print(f"  OK: NumPy")
    except ImportError:
        print(f"  FALTA: NumPy")
    
    try:
        import scipy
        print(f"  OK: SciPy")
    except ImportError:
        print(f"  FALTA: SciPy")
    
    try:
        import moviepy
        print(f"  OK: MoviePy")
    except ImportError:
        print(f"  FALTA: MoviePy")
    
    try:
        import googleapiclient
        print(f"  OK: Google API Client")
    except ImportError:
        print(f"  FALTA: Google API Client")
    
    # Verificar archivos de configuración
    config_folder = obtener_carpeta_configuracion()
    print(f"\nArchivos de configuracion en: {config_folder}")
    
    archivos = [
        "calibracion_cam_izq.npz",
        "calibracion_cam_der.npz",
        "matriz_homografia.npy",
        "drive_credentials.json",
        "drive_token.pickle",
        "drive_folder_id.txt"
    ]
    
    for archivo in archivos:
        ruta = config_folder / archivo
        if ruta.exists():
            print(f"  OK: {archivo}")
        else:
            print(f"  FALTA: {archivo}")
    
    print("\n" + "="*60)
    print("Verificacion completada")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()