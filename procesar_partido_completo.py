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


def configurar_homografia_partido(video_izq, video_der):
    """
    Configura la homografía para este partido específico.
    Extrae frames y pide al usuario que marque los 6 puntos.
    Devuelve la matriz de homografía.
    """
    print("\n" + "="*70)
    print("  CONFIGURAR HOMOGRAFÍA PARA ESTE PARTIDO")
    print("="*70)
    print("\nCada campo es diferente (altura, posición cámaras).")
    print("Debes marcar 6 puntos correspondientes en ambas imágenes.")
    print("\nLOS 6 PUNTOS (en orden):")
    print("  1. Intersección línea área con línea de fondo (izq)")
    print("  2. Esquina área grande con línea de fondo")
    print("  3. Otra esquina área grande (opuesto)")
    print("  4. Esquina del campo (corner contrario)")
    print("  5. Línea medio campo en línea de banda")
    print("  6. Centro del campo")

    input("\nPresiona ENTER para extraer frames y configurar homografía...")

    # Extraer frames
    print("\n🎞️  Extrayendo frames del segundo 2...")

    temp_folder = Path.home() / "futbol_output"
    temp_folder.mkdir(exist_ok=True)

    frame_izq = temp_folder / "temp_frame_izq.jpg"
    frame_der = temp_folder / "temp_frame_der.jpg"

    # Extraer frame izquierdo
    cmd = ['ffmpeg', '-i', str(video_izq), '-ss', '00:00:02', '-frames:v', '1',
           '-y', str(frame_izq)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Extraer frame derecho
    cmd = ['ffmpeg', '-i', str(video_der), '-ss', '00:00:02', '-frames:v', '1',
           '-y', str(frame_der)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not frame_izq.exists() or not frame_der.exists():
        print("❌ ERROR: No se pudieron extraer frames")
        return None

    print("✓ Frames extraídos")

    # Cargar imágenes
    img_left = cv2.imread(str(frame_izq))
    img_right = cv2.imread(str(frame_der))

    if img_left is None or img_right is None:
        print("❌ ERROR: No se pudieron cargar imágenes")
        return None

    # Pedir al usuario que marque puntos
    print("\n📍 MARCA 6 PUNTOS EN IMAGEN IZQUIERDA")
    print("   Click en cada punto, presiona 'q' cuando termines")

    points_left = marcar_puntos_manual(img_left, "IZQUIERDA - Marca 6 puntos")

    if len(points_left) != 6:
        print(f"❌ ERROR: Debes marcar exactamente 6 puntos (marcaste {len(points_left)})")
        return None

    print("\n📍 MARCA LOS MISMOS 6 PUNTOS EN IMAGEN DERECHA (MISMO ORDEN)")
    print("   Click en cada punto, presiona 'q' cuando termines")

    points_right = marcar_puntos_manual(img_right, "DERECHA - Marca 6 puntos (mismo orden)")

    if len(points_right) != 6:
        print(f"❌ ERROR: Debes marcar exactamente 6 puntos (marcaste {len(points_right)})")
        return None

    # Calcular homografía
    print("\n🔄 Calculando homografía...")
    pts_left = np.float32(points_left)
    pts_right = np.float32(points_right)

    H, status = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, 5.0)

    print(f"✓ Homografía calculada con {len(points_left)} puntos")

    # Limpiar archivos temporales
    frame_izq.unlink()
    frame_der.unlink()

    return H


def marcar_puntos_manual(imagen, titulo):
    """
    Permite al usuario marcar puntos clickeando en la imagen.
    Devuelve lista de puntos (x, y).
    """
    points = []
    display_img = imagen.copy()

    h_original, w_original = imagen.shape[:2]

    # Escalar para ventana grande
    target_width = 2400
    target_height = 1350
    scale = min(target_width / w_original, target_height / h_original)
    scaled_w = int(w_original * scale)
    scaled_h = int(h_original * scale)

    display_img = cv2.resize(imagen, (scaled_w, scaled_h))

    # Letterbox
    letterbox = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    offset_x = (target_width - scaled_w) // 2
    offset_y = (target_height - scaled_h) // 2
    letterbox[offset_y:offset_y+scaled_h, offset_x:offset_x+scaled_w] = display_img

    current_img = letterbox.copy()

    def mouse_callback(event, x, y, flags, param):
        nonlocal current_img, points

        if event == cv2.EVENT_LBUTTONDOWN:
            # Convertir a coordenadas originales
            x_scaled = x - offset_x
            y_scaled = y - offset_y

            if x_scaled < 0 or y_scaled < 0 or x_scaled >= scaled_w or y_scaled >= scaled_h:
                return

            x_original = int(x_scaled / scale)
            y_original = int(y_scaled / scale)

            points.append((x_original, y_original))

            # Dibujar punto
            cv2.circle(current_img, (x, y), 5, (0, 255, 0), -1)
            cv2.circle(current_img, (x, y), 6, (0, 0, 0), 1)
            cv2.circle(current_img, (x, y), 1, (255, 255, 255), -1)
            cv2.putText(current_img, str(len(points)), (x + 20, y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(titulo, current_img)

            print(f"  Punto {len(points)}/6 marcado")

    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(titulo, mouse_callback)
    cv2.imshow(titulo, current_img)

    print(f"\nMarcando puntos en {titulo}...")
    print("  - Click izquierdo: Marcar punto")
    print("  - 'q': Terminar")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()

    return points


def procesar_partido(nombre_equipo):
    """
    Pipeline completo:
    1. Concatena videos
    2. Sincroniza
    3. CONFIGURA HOMOGRAFÍA (marca 6 puntos)
    4. Genera panorama
    5. Crea video táctico y seguimiento
    6. Guarda en Drive
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

    # 3. CONFIGURAR HOMOGRAFÍA PARA ESTE PARTIDO
    homografia = configurar_homografia_partido(video_izq, video_der)

    if homografia is None:
        print("\n❌ ERROR: No se pudo configurar homografía")
        return

    print("✓ Homografía configurada para este partido")

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
