#!/usr/bin/env python3
"""
Pipeline de PRUEBA - Solo procesa 1-2 minutos para iteración rápida
Permite verificar homografía y panorama sin esperar 8 horas
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

# ==================== CONFIGURACIÓN ====================
INPUT_LEFT = Path.home() / "Desktop" / "raw_video_left"
INPUT_RIGHT = Path.home() / "Desktop" / "raw_video_right"
OUTPUT_BASE = Path.home() / "futbol_output"  # Carpeta temporal para pruebas
CONFIG_FOLDER = Path(__file__).parent / "futbol_calibracion"

# Configuración de prueba
DURACION_PRUEBA_SEGUNDOS = 60  # Solo procesar 60 segundos
FPS = 30
MAX_FRAMES = DURACION_PRUEBA_SEGUNDOS * FPS  # 1800 frames

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
        print("✓ Un solo archivo")
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


def configurar_homografia_partido(video_izq, video_der):
    """
    Configura la homografía para este partido específico.
    Extrae frames y pide al usuario que marque los 6 puntos.
    Devuelve la matriz de homografía.
    """
    print("\n" + "="*70)
    print("  CONFIGURAR HOMOGRAFÍA PARA PRUEBA")
    print("="*70)
    print("\nMarca 6 puntos correspondientes en ambas imágenes.")
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

    print(f"✓ Homografía calculada")
    print(f"\nMatriz H:")
    print(H)

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

            print(f"  Punto {len(points)}/6 marcado: ({x_original}, {y_original})")

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


def procesar_prueba(nombre_equipo):
    """
    Pipeline de PRUEBA - Solo primeros 60 segundos
    """
    print("\n" + "="*70)
    print(f"  MODO PRUEBA - PROCESANDO {DURACION_PRUEBA_SEGUNDOS}s: {nombre_equipo}")
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

    # 3. CONFIGURAR HOMOGRAFÍA
    homografia = configurar_homografia_partido(video_izq, video_der)

    if homografia is None:
        print("\n❌ ERROR: No se pudo configurar homografía")
        return

    print("✓ Homografía configurada")

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

    # 5. Crear carpeta de output
    output_folder = OUTPUT_BASE / f"PRUEBA_{nombre_equipo}"
    output_folder.mkdir(exist_ok=True, parents=True)
    print(f"✓ Carpeta creada: {output_folder}")

    # 6. Leer primer frame para calcular dimensiones del panorama
    ret, frame_left = cap_left.read()
    ret, frame_right = cap_right.read()

    if not ret:
        print("❌ ERROR: No se pudieron leer frames")
        return

    h, w = frame_left.shape[:2]
    print(f"\n📐 Dimensiones frame original: {w}x{h}")

    # CALCULAR TAMAÑO CORRECTO DEL PANORAMA
    # Probar con canvas más grande para ver toda la transformación
    panorama_width = w * 3  # Más ancho para tener espacio
    panorama_height = h * 2  # Más alto por si acaso

    print(f"📐 Canvas panorama: {panorama_width}x{panorama_height}")

    # Crear matriz de traslación para desplazar la imagen derecha
    # Esto coloca la imagen izquierda en la parte izquierda del canvas
    H_translate = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ], dtype=np.float64)

    # Combinar homografía con traslación
    H_combined = H_translate @ homografia

    # Reset videos
    cap_left.set(cv2.CAP_PROP_POS_FRAMES, max(0, offset) if offset > 0 else 0)
    cap_right.set(cv2.CAP_PROP_POS_FRAMES, max(0, -offset) if offset < 0 else 0)

    print(f"\n🎥 Procesando primeros {DURACION_PRUEBA_SEGUNDOS} segundos ({MAX_FRAMES} frames)...")
    print("Presiona 'q' para salir, SPACE para pausar")

    frame_count = 0
    muestras_guardadas = 0

    while frame_count < MAX_FRAMES:
        ret_left, frame_left = cap_left.read()
        ret_right, frame_right = cap_right.read()

        if not ret_left or not ret_right:
            break

        frame_count += 1

        # Crear panorama
        # Primero transformar imagen derecha
        frame_right_warped = cv2.warpPerspective(frame_right, H_combined,
                                                   (panorama_width, panorama_height))

        # Copiar imagen izquierda en la posición correcta
        panorama = frame_right_warped.copy()
        panorama[0:h, 0:w] = frame_left

        # Mostrar panorama (escalado para caber en pantalla)
        display_height = 800
        display_width = int(panorama.shape[1] * (display_height / panorama.shape[0]))
        panorama_display = cv2.resize(panorama, (display_width, display_height))

        # Info en el frame
        cv2.putText(panorama_display, f"Frame: {frame_count}/{MAX_FRAMES}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(panorama_display, "MODO PRUEBA - Q: salir, SPACE: pausa", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("PRUEBA - Panorama", panorama_display)

        # Guardar muestras cada 10 segundos
        if frame_count % (FPS * 10) == 0:
            muestra_path = output_folder / f"muestra_frame_{frame_count:05d}.jpg"
            cv2.imwrite(str(muestra_path), panorama)
            print(f"  ✓ Guardada muestra: {muestra_path.name}")
            muestras_guardadas += 1

        # Control de teclado
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n⚠️  Prueba cancelada por usuario")
            break
        elif key == ord(' '):
            print("\n⏸️  PAUSADO - Presiona SPACE para continuar")
            while True:
                key = cv2.waitKey(0) & 0xFF
                if key == ord(' '):
                    break
                elif key == ord('q'):
                    break

        if frame_count % FPS == 0:
            print(f"  Procesado: {frame_count}/{MAX_FRAMES} frames ({frame_count//FPS}s)")

    # Limpiar
    cap_left.release()
    cap_right.release()
    cv2.destroyAllWindows()

    tiempo_total = time.time() - inicio

    print(f"\n✅ PRUEBA COMPLETADA")
    print(f"  Tiempo total: {int(tiempo_total)}s")
    print(f"  Frames procesados: {frame_count}")
    print(f"  Muestras guardadas: {muestras_guardadas}")
    print(f"\n📁 Muestras en: {output_folder}")
    print("\n💡 Revisa las muestras. Si se ve bien, ejecuta el pipeline completo.")
    print("="*70)


# ==================== MAIN ====================

def main():
    print("\n" + "="*70)
    print("  PROCESADOR DE PARTIDOS - MODO PRUEBA")
    print(f"  Solo procesa {DURACION_PRUEBA_SEGUNDOS} segundos para verificar rápido")
    print("="*70)

    # Verificar carpetas de input
    if not INPUT_LEFT.exists() or not INPUT_RIGHT.exists():
        print("\n❌ ERROR: Carpetas de video no encontradas")
        print(f"  Izquierda: {INPUT_LEFT}")
        print(f"  Derecha: {INPUT_RIGHT}")
        return

    # Preguntar nombre del equipo
    print("\n📝 Información del partido:")
    nombre_equipo = input("Nombre del equipo rival: ").strip()

    if not nombre_equipo:
        print("❌ ERROR: Debes introducir un nombre")
        return

    procesar_prueba(nombre_equipo)


if __name__ == "__main__":
    main()
