#!/usr/bin/env python3
"""
SUPERPONER DOS CÁMARAS - Alineando rectas

1. Marca 2 puntos en IZQUIERDA (forman una recta, ej: línea medio campo)
2. Marca LOS MISMOS 2 puntos en DERECHA (misma recta)
3. Rota/escala imagen DERECHA para que su recta coincida con la de IZQUIERDA
4. Fusiona ambas imágenes con alpha blending en zona de solapamiento
5. Resultado: panorama con rectas alineadas y todo visible
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
    """Marca puntos clickeando"""
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
                    cv2.circle(current, (px_d, py_d), 10, (0, 255, 0), -1)
                    cv2.circle(current, (px_d, py_d), 2, (255, 255, 255), -1)
                    cv2.putText(current, str(i), (px_d+15, py_d-15),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                # Dibujar línea si hay 2 puntos
                if len(points) == 2:
                    p1 = (int(points[0][0] * scale) + offset_x,
                          int(points[0][1] * scale) + offset_y)
                    p2 = (int(points[1][0] * scale) + offset_x,
                          int(points[1][1] * scale) + offset_y)
                    cv2.line(current, p1, p2, (0, 255, 255), 3)

                cv2.imshow(titulo, current)
                print(f"  ✓ Punto {len(points)}/{num_puntos}: ({x_img}, {y_img})")

    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(titulo, mouse)
    cv2.imshow(titulo, current)

    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")
    print(f"  Marca {num_puntos} puntos, luego presiona 'q'")
    print(f"  (Se dibujará la RECTA entre los 2 puntos)")
    print(f"{'='*70}\n")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') and len(points) == num_puntos:
            break
        elif key == ord('q'):
            print(f"⚠️  Faltan {num_puntos - len(points)} puntos")

    cv2.destroyAllWindows()
    return points

def main():
    print("\n" + "="*70)
    print("  SUPERPONER CÁMARAS - Alineando Rectas")
    print("="*70)
    print("\n📖 CONCEPTO:")
    print("   • Los 2 puntos forman una RECTA (ej: línea medio campo)")
    print("   • Esa RECTA debe ser la MISMA en ambas imágenes")
    print("   • Alineamos la recta de DERECHA con la de IZQUIERDA")
    print("   • Fusionamos donde se solapan")
    print("   • Todo queda visible, sin recortar")

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

    h_l, w_l = img_left.shape[:2]
    h_r, w_r = img_right.shape[:2]
    print(f"✓ Dimensiones izq: {w_l}x{h_l}")
    print(f"✓ Dimensiones der: {w_r}x{h_r}")

    # Marcar 2 puntos que forman la RECTA
    print("\n" + "="*70)
    print("  IMAGEN IZQUIERDA")
    print("  Marca 2 puntos que formen una RECTA clara")
    print("  (Ej: línea medio campo de extremo a extremo)")
    print("="*70)
    points_left = marcar_puntos(img_left, "IZQUIERDA - 2 puntos (forman recta)", 2)

    print("\n" + "="*70)
    print("  IMAGEN DERECHA")
    print("  Marca LOS MISMOS 2 puntos (misma recta física)")
    print("="*70)
    points_right = marcar_puntos(img_right, "DERECHA - MISMOS 2 puntos", 2)

    # Convertir a numpy
    pts_l = np.float32(points_left)
    pts_r = np.float32(points_right)

    print("\n🔄 Calculando transformación para alinear rectas...")
    print(f"   Puntos izq: {points_left}")
    print(f"   Puntos der: {points_right}")

    # Calcular homografía con solo 2 puntos correspondientes
    # Necesitamos al menos 4 puntos para homografía completa
    # Pero para alinear una recta, podemos usar transformación afín

    # Añadir puntos perpendiculares para tener 4 puntos
    # Vector de la recta izquierda
    v_l = pts_l[1] - pts_l[0]
    perp_l = np.array([-v_l[1], v_l[0]])  # Vector perpendicular
    perp_l = perp_l / np.linalg.norm(perp_l) * 100  # Normalizar y escalar

    # Crear 2 puntos adicionales perpendiculares al punto medio
    mid_l = (pts_l[0] + pts_l[1]) / 2
    pts_l_extra = np.array([
        pts_l[0],
        pts_l[1],
        mid_l + perp_l,
        mid_l - perp_l
    ], dtype=np.float32)

    # Lo mismo para derecha
    v_r = pts_r[1] - pts_r[0]
    perp_r = np.array([-v_r[1], v_r[0]])
    perp_r = perp_r / np.linalg.norm(perp_r) * 100

    mid_r = (pts_r[0] + pts_r[1]) / 2
    pts_r_extra = np.array([
        pts_r[0],
        pts_r[1],
        mid_r + perp_r,
        mid_r - perp_r
    ], dtype=np.float32)

    # Calcular homografía
    H, status = cv2.findHomography(pts_r_extra, pts_l_extra, cv2.RANSAC, 5.0)

    if H is None:
        print("❌ No se pudo calcular transformación")
        return

    print("✓ Transformación calculada")

    # Calcular tamaño del canvas necesario
    print("\n📐 Calculando tamaño del panorama...")

    # Esquinas de ambas imágenes
    corners_left = np.float32([[0, 0], [w_l, 0], [w_l, h_l], [0, h_l]]).reshape(-1, 1, 2)
    corners_right = np.float32([[0, 0], [w_r, 0], [w_r, h_r], [0, h_r]]).reshape(-1, 1, 2)

    # Transformar esquinas de derecha
    corners_right_warped = cv2.perspectiveTransform(corners_right, H)

    # Todos los puntos
    all_corners = np.concatenate([corners_left, corners_right_warped])

    # Límites
    [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)

    # Traslación para que todo sea visible
    translation = np.array([
        [1, 0, -x_min],
        [0, 1, -y_min],
        [0, 0, 1]
    ], dtype=np.float64)

    H_final = translation @ H

    pano_w = x_max - x_min
    pano_h = y_max - y_min

    print(f"   Canvas: {pano_w}x{pano_h}")

    # Transformar imagen derecha
    print("\n🎨 Creando panorama...")
    img_right_warped = cv2.warpPerspective(img_right, H_final, (pano_w, pano_h))

    # Crear panorama
    panorama = np.zeros((pano_h, pano_w, 3), dtype=np.uint8)

    # Copiar imagen izquierda en su posición
    panorama[-y_min:h_l-y_min, -x_min:w_l-x_min] = img_left

    # Máscaras
    mask_left = np.zeros((pano_h, pano_w), dtype=np.uint8)
    mask_left[-y_min:h_l-y_min, -x_min:w_l-x_min] = 255

    mask_right = cv2.cvtColor(img_right_warped, cv2.COLOR_BGR2GRAY)
    mask_right = (mask_right > 0).astype(np.uint8) * 255

    # Zona de solapamiento
    overlap = cv2.bitwise_and(mask_left, mask_right)

    # Fusionar con alpha blending en solapamiento
    for y in range(pano_h):
        for x in range(pano_w):
            if overlap[y, x] > 0:
                # Alpha blending 50/50 en solapamiento
                panorama[y, x] = (panorama[y, x].astype(np.float32) * 0.5 +
                                  img_right_warped[y, x].astype(np.float32) * 0.5).astype(np.uint8)
            elif mask_right[y, x] > 0 and mask_left[y, x] == 0:
                # Solo derecha
                panorama[y, x] = img_right_warped[y, x]

    print("✓ Panorama creado")

    # Guardar
    output_pano = OUTPUT_BASE / "panorama_superpuesto.jpg"
    cv2.imwrite(str(output_pano), panorama)

    print(f"\n📁 Guardado: {output_pano}")

    # Mostrar
    display_h = 800
    display_w = int(pano_w * (display_h / pano_h))
    pano_display = cv2.resize(panorama, (display_w, display_h))

    cv2.putText(pano_display, "PANORAMA - presiona cualquier tecla", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("PANORAMA CON RECTAS SUPERPUESTAS", pano_display)
    print("\n👁️  Mostrando panorama...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Guardar configuración
    np.save(OUTPUT_BASE / "homografia_superponer.npy", H_final)

    print("\n✅ COMPLETADO")
    print("   Las rectas están alineadas")
    print("   Las imágenes se fusionan donde se solapan")
    print("\n💡 ¿Se ve todo el campo completo y alineado?")
    print("="*70)

if __name__ == "__main__":
    main()
