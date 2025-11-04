#!/usr/bin/env python3
"""
Configuración CORRECTA de panorama

CLAVE: Los puntos 5 y 6 (medio campo y centro) son COMUNES a ambas imágenes
       - Son la zona de SOLAPAMIENTO donde las dos cámaras ven lo mismo

Enfoque:
1. Definir posiciones del campo en el panorama (sistema de coordenadas común)
2. Transformar AMBAS imágenes a ese espacio del panorama
3. Fusionarlas con solapamiento en la zona central
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
    print("  CONFIGURACIÓN CORRECTA DE PANORAMA")
    print("="*70)

    print("\n📖 CONCEPTO CLAVE:")
    print("   - Cámara IZQUIERDA ve: lado izquierdo + zona central")
    print("   - Cámara DERECHA ve: zona central + lado derecho")
    print("   - ZONA DE SOLAPAMIENTO: centro del campo (puntos 5 y 6)")
    print("   - Debemos ALINEAR ambas imágenes en esa zona central")

    input("\nPresiona ENTER para continuar...")

    # Buscar videos
    video_izq = encontrar_primer_video(INPUT_LEFT)
    video_der = encontrar_primer_video(INPUT_RIGHT)

    if not video_izq or not video_der:
        print("\n❌ ERROR: No se encontraron videos")
        print(f"  Izquierda: {INPUT_LEFT}")
        print(f"  Derecha: {INPUT_RIGHT}")
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

    # Definir qué puntos marcar en cada imagen
    print("\n" + "="*70)
    print("  INSTRUCCIONES IMPORTANTES")
    print("="*70)
    print("\n🎯 IMAGEN IZQUIERDA - Marca estos 4 puntos:")
    print("   1. Esquina área pequeña izquierda (línea de fondo)")
    print("   2. Esquina área grande izquierda (línea de fondo)")
    print("   3. Línea medio campo en banda IZQUIERDA (donde empieza tu vista)")
    print("   4. Centro del campo")

    print("\n🎯 IMAGEN DERECHA - Marca estos 4 puntos:")
    print("   1. Línea medio campo en banda DERECHA (donde empieza tu vista)")
    print("   2. Centro del campo (MISMO que en izquierda)")
    print("   3. Esquina área grande derecha (línea de fondo)")
    print("   4. Esquina área pequeña derecha (línea de fondo)")

    print("\n⚠️  MUY IMPORTANTE:")
    print("   - Punto 4 de IZQUIERDA = Punto 2 de DERECHA (centro del campo)")
    print("   - Estos dos puntos DEBEN ser exactamente el mismo lugar")
    print("   - Es donde las imágenes se van a solapar")

    input("\nPresiona ENTER para marcar puntos en imagen IZQUIERDA...")

    # Marcar puntos IZQUIERDA (4 puntos)
    desc_izq = [
        "Esquina área pequeña izq (fondo)",
        "Esquina área grande izq (fondo)",
        "Medio campo banda IZQ",
        "CENTRO del campo ⭐"
    ]

    points_left = marcar_puntos_manual(img_left, "IMAGEN IZQUIERDA", desc_izq)

    if len(points_left) != 4:
        print(f"❌ ERROR: Debes marcar 4 puntos (marcaste {len(points_left)})")
        return

    print("\n✓ Puntos izquierda marcados")
    print(f"   Centro del campo en izquierda: {points_left[3]}")

    input("\nPresiona ENTER para marcar puntos en imagen DERECHA...")

    # Marcar puntos DERECHA (4 puntos)
    desc_der = [
        "Medio campo banda DER",
        "CENTRO del campo ⭐ (mismo que izq)",
        "Esquina área grande der (fondo)",
        "Esquina área pequeña der (fondo)"
    ]

    points_right = marcar_puntos_manual(img_right, "IMAGEN DERECHA", desc_der)

    if len(points_right) != 4:
        print(f"❌ ERROR: Debes marcar 4 puntos (marcaste {len(points_right)})")
        return

    print("\n✓ Puntos derecha marcados")
    print(f"   Centro del campo en derecha: {points_right[1]}")

    # Crear sistema de coordenadas del panorama
    print("\n🔧 Creando panorama...")

    # Ancho del panorama: aproximadamente imagen izq + imagen der (con solapamiento)
    # Vamos a usar un factor de 1.7x el ancho de una imagen
    panorama_width = int(w * 1.7)
    panorama_height = h

    print(f"📐 Tamaño panorama: {panorama_width}x{panorama_height}")

    # Definir posiciones de los puntos en el panorama
    # Distribuimos los puntos de forma lógica en el panorama

    # Puntos de la imagen izquierda en el panorama
    pano_points_left = np.float32([
        [w * 0.1, h * 0.8],      # 1. Esquina área pequeña izq (fondo) - abajo izquierda
        [w * 0.2, h * 0.8],      # 2. Esquina área grande izq (fondo)
        [w * 0.5, h * 0.1],      # 3. Medio campo banda izq - arriba
        [w * 0.85, h * 0.5]      # 4. Centro del campo - centro-derecha del panorama
    ])

    # Puntos de la imagen derecha en el panorama
    # El punto 2 (centro) debe coincidir con el punto 4 de izquierda
    pano_points_right = np.float32([
        [w * 0.85, h * 0.9],     # 1. Medio campo banda der - arriba
        [w * 0.85, h * 0.5],     # 2. Centro del campo (MISMO que izq[4])
        [w * 1.4, h * 0.8],      # 3. Esquina área grande der (fondo)
        [w * 1.5, h * 0.8]       # 4. Esquina área pequeña der (fondo) - abajo derecha
    ])

    # Calcular homografías
    print("🔄 Calculando homografías...")

    H_left, _ = cv2.findHomography(np.float32(points_left), pano_points_left, cv2.RANSAC, 5.0)
    H_right, _ = cv2.findHomography(np.float32(points_right), pano_points_right, cv2.RANSAC, 5.0)

    print("✓ Homografía izquierda calculada")
    print("✓ Homografía derecha calculada")

    # Crear panorama
    print("\n🎨 Generando panorama...")

    # Transformar ambas imágenes al espacio del panorama
    warped_left = cv2.warpPerspective(img_left, H_left, (panorama_width, panorama_height))
    warped_right = cv2.warpPerspective(img_right, H_right, (panorama_width, panorama_height))

    # Crear máscaras para fusionar
    mask_left = cv2.cvtColor(warped_left, cv2.COLOR_BGR2GRAY)
    mask_left = (mask_left > 0).astype(np.uint8) * 255

    mask_right = cv2.cvtColor(warped_right, cv2.COLOR_BGR2GRAY)
    mask_right = (mask_right > 0).astype(np.uint8) * 255

    # Zona de solapamiento
    overlap = cv2.bitwise_and(mask_left, mask_right)

    # Fusionar con promedio en zona de solapamiento
    panorama = np.zeros((panorama_height, panorama_width, 3), dtype=np.uint8)

    # Píxeles solo de izquierda
    only_left = cv2.bitwise_and(mask_left, cv2.bitwise_not(mask_right))
    panorama[only_left > 0] = warped_left[only_left > 0]

    # Píxeles solo de derecha
    only_right = cv2.bitwise_and(mask_right, cv2.bitwise_not(mask_left))
    panorama[only_right > 0] = warped_right[only_right > 0]

    # Píxeles de solapamiento (promedio)
    overlap_mask = overlap > 0
    panorama[overlap_mask] = (warped_left[overlap_mask].astype(np.float32) +
                              warped_right[overlap_mask].astype(np.float32)) / 2
    panorama[overlap_mask] = panorama[overlap_mask].astype(np.uint8)

    print("✓ Panorama creado")

    # Guardar resultados
    output_pano = temp_folder / "panorama_resultado.jpg"
    output_left_w = temp_folder / "izquierda_transformada.jpg"
    output_right_w = temp_folder / "derecha_transformada.jpg"

    cv2.imwrite(str(output_pano), panorama)
    cv2.imwrite(str(output_left_w), warped_left)
    cv2.imwrite(str(output_right_w), warped_right)

    print(f"\n📁 Archivos guardados:")
    print(f"   {output_pano}")
    print(f"   {output_left_w}")
    print(f"   {output_right_w}")

    # Mostrar panorama
    display_height = 800
    display_width = int(panorama.shape[1] * (display_height / panorama.shape[0]))
    panorama_display = cv2.resize(panorama, (display_width, display_height))

    cv2.imshow("PANORAMA RESULTADO", panorama_display)
    print("\n👁️  Mostrando panorama. Presiona cualquier tecla para cerrar...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Guardar homografías
    np.save(temp_folder / "homografia_izquierda.npy", H_left)
    np.save(temp_folder / "homografia_derecha.npy", H_right)
    np.save(temp_folder / "panorama_config.npy",
            np.array([panorama_width, panorama_height]))

    print("\n✅ CONFIGURACIÓN GUARDADA")
    print(f"   Homografías y configuración en: {temp_folder}")
    print("\n💡 Si el panorama se ve bien, podemos usarlo en el pipeline completo")
    print("="*70)


if __name__ == "__main__":
    main()
