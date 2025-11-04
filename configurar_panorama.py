#!/usr/bin/env python3
"""
Configuración de Panorama - Sistema Correcto

CONCEPTO CLAVE:
- Solo 2 puntos de SOLAPAMIENTO (que ambas cámaras ven lo mismo):
  1. Centro del campo (círculo central)
  2. Intersección línea medio campo con banda CONTRARIA

- Otros 4 puntos definen GEOMETRÍA del campo para cada lado:
  3. Intersección área penalti con línea de fondo
  4. Esquina área penalti con banda contraria
  5. Corner (línea fondo con banda contraria)
  6. Intersección línea lateral área con línea medio campo

El algoritmo solapa por los puntos 1 y 2, y usa 3-6 para corregir geometría.
"""

import cv2
import numpy as np
from pathlib import Path
import subprocess
import glob
import os

# ==================== CONFIGURACIÓN ====================
INPUT_LEFT = Path.home() / "Desktop" / "raw_video_left"
INPUT_RIGHT = Path.home() / "Desktop" / "raw_video_right"
OUTPUT_BASE = Path("/Users/User/Library/CloudStorage/GoogleDrive-ignaciovct99@gmail.com/Mi unidad/Documentos/PROYECTOS/CAC SENIOR B /Analisis de video/partidos_propios/futbol_processor")

# ==================== FUNCIONES ====================

def encontrar_primer_video(carpeta):
    """Encuentra el primer video en la carpeta"""
    extensiones = ['*.MP4', '*.mp4', '*.MOV', '*.mov']
    archivos = []
    for ext in extensiones:
        archivos.extend(glob.glob(os.path.join(carpeta, ext)))

    if not archivos:
        return None

    archivos.sort(key=os.path.getmtime)
    return archivos[0]


def marcar_puntos_manual(imagen, titulo, descripcion_puntos):
    """Permite al usuario marcar puntos clickeando en la imagen"""
    points = []

    h_original, w_original = imagen.shape[:2]

    # Ventana grande para precisión
    target_width = 2400
    target_height = 1350
    scale = min(target_width / w_original, target_height / h_original)
    scaled_w = int(w_original * scale)
    scaled_h = int(h_original * scale)

    display_img = cv2.resize(imagen, (scaled_w, scaled_h))

    # Letterbox (barras negras)
    letterbox = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    offset_x = (target_width - scaled_w) // 2
    offset_y = (target_height - scaled_h) // 2
    letterbox[offset_y:offset_y+scaled_h, offset_x:offset_x+scaled_w] = display_img

    current_img = letterbox.copy()

    # Mostrar lista de puntos
    y_pos = 30
    for i, desc in enumerate(descripcion_puntos, 1):
        color = (0, 255, 0) if len(points) < i else (100, 100, 100)
        cv2.putText(current_img, f"{i}. {desc}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        y_pos += 30

    cv2.imshow(titulo, current_img)

    def mouse_callback(event, x, y, flags, param):
        nonlocal current_img, points

        if event == cv2.EVENT_LBUTTONDOWN:
            x_scaled = x - offset_x
            y_scaled = y - offset_y

            if x_scaled < 0 or y_scaled < 0 or x_scaled >= scaled_w or y_scaled >= scaled_h:
                return

            x_original = int(x_scaled / scale)
            y_original = int(y_scaled / scale)

            points.append((x_original, y_original))

            # Redibujar
            current_img = letterbox.copy()

            # Lista de puntos
            y_pos = 30
            for i, desc in enumerate(descripcion_puntos, 1):
                color = (0, 255, 0) if len(points) < i else (100, 100, 100)
                cv2.putText(current_img, f"{i}. {desc}", (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_pos += 30

            # Puntos marcados
            for i, (px, py) in enumerate(points, 1):
                px_display = int(px * scale) + offset_x
                py_display = int(py * scale) + offset_y

                cv2.circle(current_img, (px_display, py_display), 8, (0, 255, 0), -1)
                cv2.circle(current_img, (px_display, py_display), 9, (0, 0, 0), 2)
                cv2.circle(current_img, (px_display, py_display), 2, (255, 255, 255), -1)
                cv2.putText(current_img, str(i), (px_display + 15, py_display - 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

            cv2.imshow(titulo, current_img)
            print(f"  ✓ Punto {len(points)}/{len(descripcion_puntos)}: {descripcion_puntos[len(points)-1]}")

    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(titulo, mouse_callback)

    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")
    for i, desc in enumerate(descripcion_puntos, 1):
        print(f"  {i}. {desc}")
    print(f"{'='*70}")
    print("  - Click: Marcar punto")
    print("  - 'q': Terminar (cuando hayas marcado todos)")
    print(f"{'='*70}\n")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and len(points) == len(descripcion_puntos):
            break
        elif key == ord('q'):
            print(f"\n⚠️  Faltan puntos: {len(descripcion_puntos) - len(points)}")

    cv2.destroyAllWindows()
    return points


def main():
    print("\n" + "="*70)
    print("  CONFIGURACIÓN DE PANORAMA")
    print("="*70)

    print("\n📖 CONCEPTO:")
    print("   - Solo 2 puntos se SOLAPAN (mismo lugar en ambas imágenes):")
    print("     ① Centro del campo")
    print("     ② Medio campo con banda CONTRARIA")
    print("   - Otros 4 puntos definen GEOMETRÍA de cada lado del campo")

    input("\nPresiona ENTER para continuar...")

    # Buscar videos
    video_izq = encontrar_primer_video(INPUT_LEFT)
    video_der = encontrar_primer_video(INPUT_RIGHT)

    if not video_izq or not video_der:
        print("\n❌ ERROR: No se encontraron videos")
        return

    print(f"\n✓ Video izq: {os.path.basename(video_izq)}")
    print(f"✓ Video der: {os.path.basename(video_der)}")

    # Extraer frames
    print("\n🎞️  Extrayendo frames del segundo 2...")

    OUTPUT_BASE.mkdir(exist_ok=True, parents=True)

    frame_izq_path = OUTPUT_BASE / "frame_izq.jpg"
    frame_der_path = OUTPUT_BASE / "frame_der.jpg"

    cmd = ['ffmpeg', '-i', str(video_izq), '-ss', '00:00:02', '-frames:v', '1',
           '-y', str(frame_izq_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = ['ffmpeg', '-i', str(video_der), '-ss', '00:00:02', '-frames:v', '1',
           '-y', str(frame_der_path)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not frame_izq_path.exists() or not frame_der_path.exists():
        print("❌ ERROR: No se pudieron extraer frames")
        return

    print("✓ Frames extraídos")

    # Cargar imágenes
    img_left = cv2.imread(str(frame_izq_path))
    img_right = cv2.imread(str(frame_der_path))

    if img_left is None or img_right is None:
        print("❌ ERROR: No se pudieron cargar imágenes")
        return

    h, w = img_left.shape[:2]
    print(f"✓ Dimensiones: {w}x{h}")

    # Descripción de puntos para IMAGEN IZQUIERDA
    desc_izq = [
        "Centro del campo (círculo) ⭐",
        "Medio campo con banda CONTRARIA (arriba) ⭐",
        "Área penalti IZQ con línea fondo",
        "Esquina área IZQ con banda contraria",
        "Corner IZQ (fondo con banda contraria)",
        "Línea área IZQ con medio campo"
    ]

    input("\nPresiona ENTER para marcar IMAGEN IZQUIERDA...")
    points_left = marcar_puntos_manual(img_left, "IMAGEN IZQUIERDA", desc_izq)

    if len(points_left) != 6:
        print(f"❌ ERROR: Se necesitan 6 puntos")
        return

    print(f"\n✓ Puntos izquierda marcados")

    # Descripción de puntos para IMAGEN DERECHA
    desc_der = [
        "Centro del campo (MISMO que izq) ⭐",
        "Medio campo con banda CONTRARIA (MISMO que izq) ⭐",
        "Área penalti DER con línea fondo",
        "Esquina área DER con banda contraria",
        "Corner DER (fondo con banda contraria)",
        "Línea área DER con medio campo"
    ]

    input("\n⚠️  IMPORTANTE: Puntos ① y ② deben ser EXACTAMENTE los mismos lugares.\nPresiona ENTER para marcar IMAGEN DERECHA...")
    points_right = marcar_puntos_manual(img_right, "IMAGEN DERECHA", desc_der)

    if len(points_right) != 6:
        print(f"❌ ERROR: Se necesitan 6 puntos")
        return

    print(f"\n✓ Puntos derecha marcados")

    # Calcular homografía
    print("\n🔄 Calculando homografía...")

    pts_left = np.float32(points_left)
    pts_right = np.float32(points_right)

    # Homografía: transforma derecha → izquierda
    H, status = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, 5.0)

    if H is None:
        print("❌ ERROR: No se pudo calcular homografía")
        return

    print("✓ Homografía calculada")

    # Calcular tamaño del panorama
    print("\n🎨 Generando panorama...")

    # Esquinas de imagen derecha
    corners_right = np.float32([
        [0, 0], [w, 0], [w, h], [0, h]
    ]).reshape(-1, 1, 2)

    # Transformar esquinas
    corners_warped = cv2.perspectiveTransform(corners_right, H)

    # Calcular límites del panorama
    all_corners = np.concatenate([
        corners_warped,
        np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    ])

    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    # Traslación para que todo sea visible
    translation = np.array([
        [1, 0, -x_min],
        [0, 1, -y_min],
        [0, 0, 1]
    ], dtype=np.float64)

    H_final = translation @ H

    panorama_width = x_max - x_min
    panorama_height = y_max - y_min

    print(f"📐 Panorama: {panorama_width}x{panorama_height}")

    # Crear panorama
    warped_right = cv2.warpPerspective(img_right, H_final, (panorama_width, panorama_height))
    panorama = warped_right.copy()
    panorama[-y_min:h-y_min, -x_min:w-x_min] = img_left

    print("✓ Panorama creado")

    # Guardar
    output_pano = OUTPUT_BASE / "panorama_resultado.jpg"
    cv2.imwrite(str(output_pano), panorama)

    # Guardar homografía y configuración
    np.save(OUTPUT_BASE / "homografia.npy", H_final)
    np.save(OUTPUT_BASE / "panorama_config.npy",
            np.array([panorama_width, panorama_height, -x_min, -y_min]))

    print(f"\n📁 Guardado: {output_pano}")

    # Mostrar
    display_height = 800
    display_width = int(panorama.shape[1] * (display_height / panorama.shape[0]))
    panorama_display = cv2.resize(panorama, (display_width, display_height))

    cv2.putText(panorama_display, "PANORAMA - Presiona cualquier tecla", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("PANORAMA", panorama_display)
    print("\n👁️  Mostrando panorama. Presiona cualquier tecla...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\n✅ CONFIGURACIÓN COMPLETA")
    print(f"   Archivos en: {OUTPUT_BASE}")
    print("\n💡 Si el panorama muestra TODO el campo completo → ¡Funciona!")
    print("="*70)


if __name__ == "__main__":
    main()
