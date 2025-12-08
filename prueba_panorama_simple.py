#!/usr/bin/env python3
"""
PRUEBA SIMPLE DE PANORAMA

Concepto básico:
- Cámara IZQ ve mitad izquierda del campo
- Cámara DER ve mitad derecha del campo
- Solapan en el CENTRO
- Marcar 3-4 puntos del CENTRO que ambas cámaras ven
- Unir y ya
"""

import cv2
import numpy as np
from pathlib import Path
import subprocess
import glob
import os

INPUT_LEFT = Path.home() / "Desktop" / "raw_video_left"
INPUT_RIGHT = Path.home() / "Desktop" / "raw_video_right"
OUTPUT_BASE = Path("/Users/User/Library/CloudStorage/GoogleDrive-ignaciovct99@gmail.com/Mi unidad/Documentos/PROYECTOS/CAC SENIOR B /Analisis de video/partidos_propios/futbol_processor")

def encontrar_primer_video(carpeta):
    extensiones = ['*.MP4', '*.mp4', '*.MOV', '*.mov']
    archivos = []
    for ext in extensiones:
        archivos.extend(glob.glob(os.path.join(carpeta, ext)))
    if not archivos:
        return None
    archivos.sort(key=os.path.getmtime)
    return archivos[0]

def marcar_puntos(imagen, titulo, num_puntos):
    """Marca puntos clickeando - SIMPLE"""
    points = []
    h, w = imagen.shape[:2]

    # Ventana grande
    scale = min(2400/w, 1350/h)
    scaled_w = int(w * scale)
    scaled_h = int(h * scale)
    display = cv2.resize(imagen, (scaled_w, scaled_h))

    # Letterbox
    canvas = np.zeros((1350, 2400, 3), dtype=np.uint8)
    offset_x = (2400 - scaled_w) // 2
    offset_y = (1350 - scaled_h) // 2
    canvas[offset_y:offset_y+scaled_h, offset_x:offset_x+scaled_w] = display

    current = canvas.copy()

    def mouse(event, x, y, flags, param):
        nonlocal current, points
        if event == cv2.EVENT_LBUTTONDOWN:
            x_img = int((x - offset_x) / scale)
            y_img = int((y - offset_y) / scale)
            if 0 <= x_img < w and 0 <= y_img < h:
                points.append((x_img, y_img))
                current = canvas.copy()
                for i, (px, py) in enumerate(points, 1):
                    px_d = int(px * scale) + offset_x
                    py_d = int(py * scale) + offset_y
                    cv2.circle(current, (px_d, py_d), 8, (0, 255, 0), -1)
                    cv2.putText(current, str(i), (px_d+15, py_d-15),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                cv2.imshow(titulo, current)
                print(f"  ✓ Punto {len(points)}/{num_puntos}")

    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(titulo, mouse)
    cv2.imshow(titulo, current)

    print(f"\n{titulo}: Click en {num_puntos} puntos, luego 'q'")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and len(points) == num_puntos:
            break

    cv2.destroyAllWindows()
    return points

def main():
    print("\n" + "="*70)
    print("  PRUEBA SIMPLE DE PANORAMA")
    print("="*70)
    print("\nVamos a marcar 4 puntos del CENTRO del campo que ambas cámaras ven:")
    print("  1. Centro del campo (círculo)")
    print("  2. Medio campo con banda contraria (arriba)")
    print("  3. Esquina superior izq área penalti")
    print("  4. Esquina superior der área penalti")

    input("\nPresiona ENTER...")

    # Buscar videos
    video_izq = encontrar_primer_video(INPUT_LEFT)
    video_der = encontrar_primer_video(INPUT_RIGHT)

    if not video_izq or not video_der:
        print("❌ No hay videos")
        return

    print(f"\n✓ Video izq: {os.path.basename(video_izq)}")
    print(f"✓ Video der: {os.path.basename(video_der)}")

    # Extraer frames
    OUTPUT_BASE.mkdir(exist_ok=True, parents=True)

    frame_izq = OUTPUT_BASE / "frame_izq.jpg"
    frame_der = OUTPUT_BASE / "frame_der.jpg"

    subprocess.run(['ffmpeg', '-i', str(video_izq), '-ss', '00:00:02',
                   '-frames:v', '1', '-y', str(frame_izq)],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run(['ffmpeg', '-i', str(video_der), '-ss', '00:00:02',
                   '-frames:v', '1', '-y', str(frame_der)],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    img_left = cv2.imread(str(frame_izq))
    img_right = cv2.imread(str(frame_der))

    if img_left is None or img_right is None:
        print("❌ Error cargando imágenes")
        return

    h, w = img_left.shape[:2]
    print(f"✓ Dimensiones: {w}x{h}")

    # Marcar 4 puntos en cada imagen (LOS MISMOS 4)
    print("\n📍 IMAGEN IZQUIERDA - Marca 4 puntos:")
    points_left = marcar_puntos(img_left, "IZQUIERDA", 4)

    print("\n📍 IMAGEN DERECHA - Marca LOS MISMOS 4 puntos:")
    points_right = marcar_puntos(img_right, "DERECHA", 4)

    # Calcular homografía
    print("\n🔄 Calculando homografía...")
    H, _ = cv2.findHomography(np.float32(points_right), np.float32(points_left))

    # Calcular tamaño panorama
    corners = np.float32([[0,0], [w,0], [w,h], [0,h]]).reshape(-1,1,2)
    corners_w = cv2.perspectiveTransform(corners, H)
    all_corners = np.concatenate([corners_w, corners])

    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    translation = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]], dtype=np.float64)
    H_final = translation @ H

    pano_w = x_max - x_min
    pano_h = y_max - y_min

    print(f"📐 Panorama: {pano_w}x{pano_h}")

    # Crear panorama
    warped_right = cv2.warpPerspective(img_right, H_final, (pano_w, pano_h))
    panorama = warped_right.copy()
    panorama[-y_min:h-y_min, -x_min:w-x_min] = img_left

    # Guardar
    output_pano = OUTPUT_BASE / "prueba_panorama.jpg"
    cv2.imwrite(str(output_pano), panorama)

    print(f"\n✅ Guardado: {output_pano}")

    # Mostrar
    display_h = 800
    display_w = int(pano_w * (display_h / pano_h))
    pano_display = cv2.resize(panorama, (display_w, display_h))

    cv2.imshow("PANORAMA - presiona cualquier tecla", pano_display)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\n💡 Revisa la imagen. ¿Se ve todo el campo?")
    print("="*70)

if __name__ == "__main__":
    main()
