#!/usr/bin/env python3
"""
Pipeline Completo de Procesamiento de Partidos
Hace TODO automáticamente en un solo comando
"""

import cv2
import numpy as np
from pathlib import Path
import subprocess
import tempfile
import os
import glob
from scipy.io import wavfile
from scipy.signal import correlate
import time
from datetime import datetime

# ==================== CONFIGURACIÓN FIJA ====================
# Estas rutas SIEMPRE son las mismas
INPUT_LEFT = Path.home() / "Desktop" / "raw_video_left"
INPUT_RIGHT = Path.home() / "Desktop" / "raw_video_right"
OUTPUT_BASE = Path("/Users/User/Library/CloudStorage/GoogleDrive-ignaciovct99@gmail.com/Mi unidad/Documentos/PROYECTOS/CAC SENIOR B /Analisis de video")
CONFIG_FOLDER = Path(__file__).parent / "futbol_calibracion"

# Configuración de video
VIEW_WIDTH = 2560
VIEW_HEIGHT = 1440
FPS = 30

# ==================== FUNCIONES ====================

def concatenar_videos(carpeta_videos):
    """Concatena múltiples archivos de video en orden cronológico"""
    print(f"\n📁 Buscando videos en: {carpeta_videos}")

    extensiones = ['*.MP4', '*.mp4', '*.MOV', '*.mov']
    archivos = []
    for ext in extensiones:
        archivos.extend(glob.glob(os.path.join(carpeta_videos, ext)))

    if not archivos:
        print(f"❌ ERROR: No se encontraron videos")
        return None

    archivos.sort(key=os.path.getmtime)

    print(f"✓ Encontrados {len(archivos)} archivo(s)")
    for i, archivo in enumerate(archivos, 1):
        print(f"  {i}. {os.path.basename(archivo)}")

    if len(archivos) == 1:
        print("✓ Un solo archivo, no es necesario concatenar")
        return archivos[0]

    print(f"\n🔄 Concatenando {len(archivos)} archivos...")

    output_dir = Path.home() / "futbol_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    carpeta_nombre = os.path.basename(carpeta_videos)
    output_file = output_dir / f"concat_{carpeta_nombre}_{timestamp}.mp4"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for archivo in archivos:
            ruta_escapada = archivo.replace("'", "'\\''")
            f.write(f"file '{ruta_escapada}'\n")
        lista_path = f.name

    try:
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', lista_path,
               '-c', 'copy', str(output_file), '-y']

        resultado = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if resultado.returncode != 0:
            print(f"❌ ERROR en concatenación")
            return None

        print(f"✓ Videos concatenados")
        return str(output_file)
    finally:
        if os.path.exists(lista_path):
            os.remove(lista_path)


def sincronizar_videos(video1_path, video2_path):
    """Sincroniza dos videos usando correlación de audio (palmada)"""
    print("\n🎵 Sincronizando videos por audio (buscando palmada)...")

    with tempfile.TemporaryDirectory() as tmpdir:
        audio1 = Path(tmpdir) / "audio1.wav"
        audio2 = Path(tmpdir) / "audio2.wav"

        subprocess.run(['ffmpeg', '-i', str(video1_path), '-vn', '-acodec', 'pcm_s16le',
                       '-ar', '44100', '-ac', '1', str(audio1), '-y'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run(['ffmpeg', '-i', str(video2_path), '-vn', '-acodec', 'pcm_s16le',
                       '-ar', '44100', '-ac', '1', str(audio2), '-y'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        rate1, data1 = wavfile.read(audio1)
        rate2, data2 = wavfile.read(audio2)

        if len(data1.shape) > 1:
            data1 = data1.mean(axis=1)
        if len(data2.shape) > 1:
            data2 = data2.mean(axis=1)

        data1 = data1.astype(np.float64)
        data2 = data2.astype(np.float64)

        max_samples = min(len(data1), len(data2), rate1 * 60)
        data1_short = data1[:max_samples]
        data2_short = data2[:max_samples]

        correlation = correlate(data1_short, data2_short, mode='full')
        lag = np.argmax(correlation) - len(data2_short) + 1

        offset_frames = int(lag * FPS / rate1)
        offset_seconds = lag / rate1

        print(f"✓ Sincronización detectada: {offset_frames} frames ({offset_seconds:.2f}s)")
        return offset_frames


def detectar_balon(frame):
    """Detecta el balón en un frame (blanco + circular)"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                               param1=50, param2=30, minRadius=5, maxRadius=50)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        largest_circle = max(circles[0], key=lambda c: c[2])
        return (int(largest_circle[0]), int(largest_circle[1]))

    return None


def procesar_partido(nombre_equipo):
    """
    Procesa un partido completo:
    1. Concatena videos
    2. Sincroniza
    3. Genera panorama
    4. Crea video táctico y seguimiento
    5. Guarda en Drive
    """
    print("\n" + "="*70)
    print(f"  PROCESANDO PARTIDO: {nombre_equipo}")
    print("="*70)

    inicio = time.time()

    # 1. Concatenar videos
    print("\n--- CÁMARA IZQUIERDA ---")
    video_izq = concatenar_videos(INPUT_LEFT)
    if not video_izq:
        return

    print("\n--- CÁMARA DERECHA ---")
    video_der = concatenar_videos(INPUT_RIGHT)
    if not video_der:
        return

    # 2. Sincronizar
    offset = sincronizar_videos(video_izq, video_der)

    # 3. Cargar configuración
    print("\n⚙️  Cargando configuración...")
    homografia = np.load(CONFIG_FOLDER / "matriz_homografia.npy")
    print("✓ Homografía cargada")

    # 4. Abrir videos
    print("\n🎬 Abriendo videos...")
    cap_left = cv2.VideoCapture(str(video_izq))
    cap_right = cv2.VideoCapture(str(video_der))

    # Aplicar offset de sincronización
    if offset > 0:
        for _ in range(abs(offset)):
            cap_right.read()
    elif offset < 0:
        for _ in range(abs(offset)):
            cap_left.read()

    total_frames = int(cap_left.get(cv2.CAP_PROP_FRAME_COUNT))

    # 5. Crear carpeta de output
    output_folder = OUTPUT_BASE / nombre_equipo
    output_folder.mkdir(exist_ok=True, parents=True)
    print(f"✓ Carpeta creada: {output_folder}")

    output_tactico = output_folder / f"{nombre_equipo}_tactico.mp4"
    output_seguimiento = output_folder / f"{nombre_equipo}_seguimiento.mp4"

    # 6. Configurar escritores de video
    ret, frame_left = cap_left.read()
    ret, frame_right = cap_right.read()

    if not ret:
        print("❌ ERROR: No se pudieron leer frames")
        return

    h, w = frame_left.shape[:2]
    frame_right_warped = cv2.warpPerspective(frame_right, homografia, (w * 2, h))
    panorama_test = frame_right_warped.copy()
    panorama_test[0:h, 0:w] = frame_left

    tactico_height = 1440
    tactico_width = int(panorama_test.shape[1] * (tactico_height / panorama_test.shape[0]))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer_tactico = cv2.VideoWriter(str(output_tactico), fourcc, FPS,
                                     (tactico_width, tactico_height))
    writer_seguimiento = cv2.VideoWriter(str(output_seguimiento), fourcc, FPS,
                                        (VIEW_WIDTH, VIEW_HEIGHT))

    cap_left.set(cv2.CAP_PROP_POS_FRAMES, max(0, offset) if offset > 0 else 0)
    cap_right.set(cv2.CAP_PROP_POS_FRAMES, max(0, -offset) if offset < 0 else 0)

    print(f"\n📹 Configuración:")
    print(f"  Resolución táctica: {tactico_width}x{tactico_height}")
    print(f"  Resolución seguimiento: {VIEW_WIDTH}x{VIEW_HEIGHT}")
    print(f"  FPS: {FPS}")
    print(f"  Total frames: {total_frames}")

    # 7. Procesar frames
    print(f"\n🎥 Procesando frames...")

    frame_count = 0
    last_ball_pos = None
    ball_pos_smoothed = None
    smoothing_factor = 0.15

    while True:
        ret_left, frame_left = cap_left.read()
        ret_right, frame_right = cap_right.read()

        if not ret_left or not ret_right:
            break

        frame_count += 1

        if frame_count % 30 == 0:
            progress = (frame_count / total_frames) * 100
            elapsed = time.time() - inicio
            eta = (elapsed / frame_count) * (total_frames - frame_count)
            print(f"  Frame {frame_count}/{total_frames} ({progress:.1f}%) - "
                  f"ETA: {int(eta/60)}:{int(eta%60):02d}")

        # Crear panorama
        frame_right_warped = cv2.warpPerspective(frame_right, homografia, (w * 2, h))
        panorama = frame_right_warped.copy()
        panorama[0:h, 0:w] = frame_left

        # Detectar balón
        ball_pos = detectar_balon(panorama)

        if ball_pos is None:
            ball_pos = last_ball_pos if last_ball_pos else (panorama.shape[1]//2, panorama.shape[0]//2)
        else:
            last_ball_pos = ball_pos

        # Suavizar posición del balón
        if ball_pos_smoothed is None:
            ball_pos_smoothed = ball_pos
        else:
            ball_pos_smoothed = (
                int(ball_pos_smoothed[0] * (1 - smoothing_factor) + ball_pos[0] * smoothing_factor),
                int(ball_pos_smoothed[1] * (1 - smoothing_factor) + ball_pos[1] * smoothing_factor)
            )

        # Video táctico (panorama escalado)
        frame_tactico = cv2.resize(panorama, (tactico_width, tactico_height))

        # Video seguimiento (zoom al balón)
        x_center, y_center = ball_pos_smoothed
        x1 = max(0, x_center - VIEW_WIDTH // 2)
        y1 = max(0, y_center - VIEW_HEIGHT // 2)
        x2 = min(panorama.shape[1], x1 + VIEW_WIDTH)
        y2 = min(panorama.shape[0], y1 + VIEW_HEIGHT)

        if x2 - x1 < VIEW_WIDTH:
            x1 = max(0, x2 - VIEW_WIDTH)
        if y2 - y1 < VIEW_HEIGHT:
            y1 = max(0, y2 - VIEW_HEIGHT)

        frame_seguimiento = panorama[y1:y2, x1:x2]

        if frame_seguimiento.shape[:2] != (VIEW_HEIGHT, VIEW_WIDTH):
            frame_seguimiento = cv2.resize(frame_seguimiento, (VIEW_WIDTH, VIEW_HEIGHT))

        writer_tactico.write(frame_tactico)
        writer_seguimiento.write(frame_seguimiento)

    # 8. Limpiar
    cap_left.release()
    cap_right.release()
    writer_tactico.release()
    writer_seguimiento.release()

    tiempo_total = time.time() - inicio

    print(f"\n✅ PROCESAMIENTO COMPLETADO")
    print(f"  Tiempo total: {int(tiempo_total/60)}:{int(tiempo_total%60):02d}")
    print(f"\n📁 Archivos generados:")
    print(f"  {output_tactico}")
    print(f"  {output_seguimiento}")
    print("\n" + "="*70)


# ==================== MAIN ====================

def main():
    print("\n" + "="*70)
    print("  PROCESADOR DE PARTIDOS - PIPELINE COMPLETO")
    print("="*70)

    # Verificar carpetas de input
    if not INPUT_LEFT.exists() or not INPUT_RIGHT.exists():
        print("\n❌ ERROR: Carpetas de video no encontradas")
        print(f"  Izquierda: {INPUT_LEFT}")
        print(f"  Derecha: {INPUT_RIGHT}")
        print("\nCopia los videos de las tarjetas SD a estas carpetas.")
        return

    # Verificar configuración
    if not (CONFIG_FOLDER / "matriz_homografia.npy").exists():
        print("\n❌ ERROR: Falta configuración de homografía")
        print("Ejecuta primero: python3 scripts/configurar_homografia.py")
        return

    # Preguntar nombre del equipo
    print("\n📝 Información del partido:")
    nombre_equipo = input("Nombre del equipo rival: ").strip()

    if not nombre_equipo:
        print("❌ ERROR: Debes introducir un nombre")
        return

    confirmar = input(f"\n¿Procesar partido contra {nombre_equipo}? (s/n): ").strip().lower()

    if confirmar == 's':
        procesar_partido(nombre_equipo)
    else:
        print("❌ Operación cancelada")


if __name__ == "__main__":
    main()
