#!/usr/bin/env python3
"""
Configuración CORRECTA de panorama - PUNTOS CORRECTOS

PUNTOS A MARCAR (que AMBAS cámaras ven en la zona de solapamiento):

1. Centro del campo (círculo central)
2. Intersección línea medio campo con BANDA CONTRARIA (lejos, arriba)
3. Esquina área grande IZQUIERDA con línea medio campo
4. Esquina área grande DERECHA con línea medio campo
5. Intersección BANDA CONTRARIA con línea lateral área grande (lado izq)
6. Intersección BANDA CONTRARIA con línea lateral área grande (lado der)

Estos 6 puntos están en la ZONA CENTRAL del campo y AMBAS cámaras los ven.
"""

import cv2
import numpy as np
from pathlib import Path
import subprocess
import tempfile
import glob
import os

# ==================== CONFIGURACIÓN ====================
INPUT_LEFT = Path.home() / "Desktop" / "raw_video_left"
INPUT_RIGHT = Path.home() / "Desktop" / "raw_video_right"
OUTPUT_BASE = Path.home() / "futbol_output"

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

    # Mostrar descripción de puntos en la imagen
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
            # Convertir a coordenadas originales
            x_scaled = x - offset_x
            y_scaled = y - offset_y

            if x_scaled < 0 or y_scaled < 0 or x_scaled >= scaled_w or y_scaled >= scaled_h:
                return

            x_original = int(x_scaled / scale)
            y_original = int(y_scaled / scale)

            points.append((x_original, y_original))

            # Redibujar todo
            current_img = letterbox.copy()

            # Redibujar lista de puntos
            y_pos = 30
            for i, desc in enumerate(descripcion_puntos, 1):
                color = (0, 255, 0) if len(points) < i else (100, 100, 100)
                cv2.putText(current_img, f"{i}. {desc}", (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y_pos += 30

            # Dibujar todos los puntos marcados
            for i, (px, py) in enumerate(points, 1):
                # Convertir a coordenadas de pantalla
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
    print("  - Click izquierdo: Marcar punto")
    print("  - 'q': Terminar cuando hayas marcado todos")
    print(f"{'='*70}\n")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and len(points) == len(descripcion_puntos):
            break
        elif key == ord('q'):
            print(f"\n⚠️  Debes marcar {len(descripcion_puntos)} puntos (tienes {len(points)})")

    cv2.destroyAllWindows()

    return points


def main():
    print("\n" + "="*70)
    print("  CONFIGURACIÓN PANORAMA - PUNTOS CORRECTOS")
    print("="*70)

    print("\n📖 CONCEPTO:")
    print("   - Cámaras en UN lado del campo (ej: banda SUR)")
    print("   - Ven la BANDA CONTRARIA (NORTE) claramente (lejos, arriba)")
    print("   - Zona de solapamiento = CENTRO DEL CAMPO")
    print("   - Ambas cámaras ven el centro → marcar MISMOS puntos")

    print("\n🎯 LOS 6 PUNTOS (que AMBAS cámaras ven):")
    print("   1. Centro del campo (círculo central)")
    print("   2. Medio campo con BANDA CONTRARIA (arriba)")
    print("   3. Área grande IZQ con medio campo")
    print("   4. Área grande DER con medio campo")
    print("   5. BANDA CONTRARIA con línea área IZQ")
    print("   6. BANDA CONTRARIA con línea área DER")

    print("\n⚠️  IMPORTANTE:")
    print("   - Todos estos puntos están en la ZONA CENTRAL")
    print("   - AMBAS cámaras los ven")
    print("   - Marca EXACTAMENTE los mismos lugares en ambas imágenes")

    input("\nPresiona ENTER para continuar...")

    # Buscar videos
    video_izq = encontrar_primer_video(INPUT_LEFT)
    video_der = encontrar_primer_video(INPUT_RIGHT)

    if not video_izq or not video_der:
        print("\n❌ ERROR: No se encontraron videos")
        return

    print(f"\n✓ Video izquierda: {os.path.basename(video_izq)}")
    print(f"✓ Video derecha: {os.path.basename(video_der)}")

    # Extraer frames
    print("\n🎞️  Extrayendo frames del segundo 2...")

    temp_folder = OUTPUT_BASE
    temp_folder.mkdir(exist_ok=True)

    frame_izq_path = temp_folder / "frame_izq.jpg"
    frame_der_path = temp_folder / "frame_der.jpg"

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
    print(f"✓ Dimensiones imagen: {w}x{h}")

    # Descripción de los 6 puntos (IGUALES para ambas imágenes)
    descripcion = [
        "Centro del campo (círculo)",
        "Medio campo con BANDA CONTRARIA (arriba)",
        "Área grande IZQ con medio campo",
        "Área grande DER con medio campo",
        "BANDA CONTRARIA con línea área IZQ",
        "BANDA CONTRARIA con línea área DER"
    ]

    input("\nPresiona ENTER para marcar puntos en imagen IZQUIERDA...")

    # Marcar puntos IZQUIERDA
    points_left = marcar_puntos_manual(img_left, "IMAGEN IZQUIERDA - 6 puntos", descripcion)

    if len(points_left) != 6:
        print(f"❌ ERROR: Debes marcar 6 puntos (marcaste {len(points_left)})")
        return

    print("\n✓ Puntos izquierda marcados")

    input("\nPresiona ENTER para marcar LOS MISMOS puntos en imagen DERECHA...")

    # Marcar puntos DERECHA (MISMOS puntos)
    points_right = marcar_puntos_manual(img_right, "IMAGEN DERECHA - MISMOS 6 puntos", descripcion)

    if len(points_right) != 6:
        print(f"❌ ERROR: Debes marcar 6 puntos (marcaste {len(points_right)})")
        return

    print("\n✓ Puntos derecha marcados")

    # Calcular homografía
    print("\n🔄 Calculando homografía...")

    pts_left = np.float32(points_left)
    pts_right = np.float32(points_right)

    # Homografía que transforma derecha → izquierda
    H, status = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, 5.0)

    if H is None:
        print("❌ ERROR: No se pudo calcular homografía")
        return

    print("✓ Homografía calculada")

    # Crear panorama
    print("\n🎨 Generando panorama...")

    # Calcular tamaño del panorama necesario
    # Necesitamos transformar la imagen derecha y ver cuánto espacio ocupa
    corners_right = np.float32([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ]).reshape(-1, 1, 2)

    # Transformar esquinas de imagen derecha
    corners_warped = cv2.perspectiveTransform(corners_right, H)

    # Calcular límites
    all_corners = np.concatenate([
        corners_warped,
        np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    ])

    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    # Matriz de traslación para que todo sea visible
    translation = np.array([
        [1, 0, -x_min],
        [0, 1, -y_min],
        [0, 0, 1]
    ], dtype=np.float64)

    # Homografía final con traslación
    H_final = translation @ H

    panorama_width = x_max - x_min
    panorama_height = y_max - y_min

    print(f"📐 Tamaño panorama: {panorama_width}x{panorama_height}")

    # Transformar imagen derecha
    warped_right = cv2.warpPerspective(img_right, H_final, (panorama_width, panorama_height))

    # Copiar imagen izquierda en su posición
    panorama = warped_right.copy()
    panorama[-y_min:h-y_min, -x_min:w-x_min] = img_left

    print("✓ Panorama creado")

    # Guardar resultados
    output_pano = temp_folder / "panorama_resultado.jpg"
    output_left_orig = temp_folder / "izquierda_original.jpg"
    output_right_orig = temp_folder / "derecha_original.jpg"
    output_right_w = temp_folder / "derecha_transformada.jpg"

    cv2.imwrite(str(output_pano), panorama)
    cv2.imwrite(str(output_left_orig), img_left)
    cv2.imwrite(str(output_right_orig), img_right)
    cv2.imwrite(str(output_right_w), warped_right)

    print(f"\n📁 Archivos guardados:")
    print(f"   {output_pano}")
    print(f"   {output_left_orig}")
    print(f"   {output_right_orig}")
    print(f"   {output_right_w}")

    # Mostrar panorama
    display_height = 800
    display_width = int(panorama.shape[1] * (display_height / panorama.shape[0]))
    panorama_display = cv2.resize(panorama, (display_width, display_height))

    cv2.putText(panorama_display, "PANORAMA - Presiona cualquier tecla", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("PANORAMA RESULTADO", panorama_display)
    print("\n👁️  Mostrando panorama. Presiona cualquier tecla para cerrar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Guardar homografía
    np.save(temp_folder / "homografia_der_a_izq.npy", H_final)
    np.save(temp_folder / "panorama_size.npy", np.array([panorama_width, panorama_height]))
    np.save(temp_folder / "translation.npy", np.array([-x_min, -y_min]))

    print("\n✅ CONFIGURACIÓN GUARDADA")
    print(f"   Homografía en: {temp_folder}")
    print("\n💡 Revisa el panorama:")
    print(f"   {output_pano}")
    print("\n✅ Si se ve TODO el campo completo, funcionó")
    print("❌ Si aún hay problemas, dime qué ves")
    print("="*70)


if __name__ == "__main__":
    main()
