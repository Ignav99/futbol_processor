#!/usr/bin/env python3
"""
UNIR DOS CÁMARAS - MÉTODO CORRECTO

1. Marca 2 puntos en imagen IZQUIERDA (centro del campo)
2. Marca LOS MISMOS 2 puntos en imagen DERECHA
3. Alinea verticalmente basándose en esos 2 puntos
4. Recorta y une las imágenes en el centro
5. Resultado: imagen panorámica (más ancha que alta)
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
                cv2.imshow(titulo, current)
                print(f"  ✓ Punto {len(points)}/{num_puntos}")

    cv2.namedWindow(titulo, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(titulo, mouse)
    cv2.imshow(titulo, current)

    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")
    print(f"  Marca {num_puntos} puntos, luego presiona 'q'")
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
    print("  UNIR DOS CÁMARAS - MÉTODO CORRECTO")
    print("="*70)
    print("\n📖 CONCEPTO:")
    print("   1. Marca 2 puntos en IZQUIERDA (centro del campo)")
    print("   2. Marca LOS MISMOS 2 puntos en DERECHA")
    print("   3. Se recorta y une en el centro")
    print("   4. Resultado: panorama (más ancho que alto)")
    print("\n💡 LOS 2 PUNTOS sugeridos:")
    print("   • Centro del campo (círculo central)")
    print("   • Medio campo con banda contraria (arriba)")

    input("\nPresiona ENTER para empezar...")

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

    # Marcar 2 puntos en cada imagen (LOS MISMOS)
    print("\n" + "="*70)
    print("  IMAGEN IZQUIERDA - Marca 2 puntos del CENTRO")
    print("="*70)
    points_left = marcar_puntos(img_left, "IZQUIERDA - 2 puntos", 2)

    print("\n" + "="*70)
    print("  IMAGEN DERECHA - Marca LOS MISMOS 2 puntos")
    print("="*70)
    points_right = marcar_puntos(img_right, "DERECHA - MISMOS 2 puntos", 2)

    # Convertir a numpy arrays
    pts_l = np.float32(points_left)
    pts_r = np.float32(points_right)

    print("\n🔄 Procesando...")
    print(f"   Puntos izq: {points_left}")
    print(f"   Puntos der: {points_right}")

    # Calcular transformación afín (2 puntos = rotación + escala + traslación)
    # Necesitamos alinear verticalmente

    # Calcular ángulo y escala entre los dos puntos
    # Vector en imagen izquierda
    v_l = pts_l[1] - pts_l[0]
    angle_l = np.arctan2(v_l[1], v_l[0])
    len_l = np.linalg.norm(v_l)

    # Vector en imagen derecha
    v_r = pts_r[1] - pts_r[0]
    angle_r = np.arctan2(v_r[1], v_r[0])
    len_r = np.linalg.norm(v_r)

    # Diferencia de ángulo y escala
    angle_diff = angle_l - angle_r
    scale = len_l / len_r if len_r > 0 else 1.0

    print(f"   Rotación: {np.degrees(angle_diff):.2f}°")
    print(f"   Escala: {scale:.3f}")

    # Centro de rotación (primer punto de imagen derecha)
    center = (float(pts_r[0][0]), float(pts_r[0][1]))

    # Matriz de rotación + escala
    M = cv2.getRotationMatrix2D(center, np.degrees(angle_diff), scale)

    # Ajustar traslación para alinear el primer punto
    M[0, 2] += pts_l[0][0] - pts_r[0][0]
    M[1, 2] += pts_l[0][1] - pts_r[0][1]

    # Transformar imagen derecha
    print("   Transformando imagen derecha...")
    img_right_aligned = cv2.warpAffine(img_right, M, (w_r, h_r))

    # Calcular dónde está el punto de unión (promedio de x de los dos puntos en imagen izq)
    union_x = int((pts_l[0][0] + pts_l[1][0]) / 2)

    print(f"   Punto de unión: x = {union_x}")

    # Recortar imagen izquierda (solo hasta union_x)
    img_left_crop = img_left[:, :union_x]

    # Recortar imagen derecha (desde union_x hasta el final)
    img_right_crop = img_right_aligned[:, union_x:]

    # Unir horizontalmente
    panorama = np.hstack([img_left_crop, img_right_crop])

    print(f"✓ Panorama creado: {panorama.shape[1]}x{panorama.shape[0]}")

    # Guardar
    output_pano = OUTPUT_BASE / "panorama_union.jpg"
    cv2.imwrite(str(output_pano), panorama)

    # También guardar las transformadas para debug
    cv2.imwrite(str(OUTPUT_BASE / "derecha_alineada.jpg"), img_right_aligned)

    print(f"\n📁 Guardado:")
    print(f"   {output_pano}")
    print(f"   {OUTPUT_BASE / 'derecha_alineada.jpg'}")

    # Mostrar
    display_h = 800
    display_w = int(panorama.shape[1] * (display_h / panorama.shape[0]))
    pano_display = cv2.resize(panorama, (display_w, display_h))

    cv2.putText(pano_display, "PANORAMA - presiona cualquier tecla", (20, 40),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("PANORAMA UNIDO", pano_display)
    print("\n👁️  Mostrando panorama...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Guardar configuración
    config = {
        'angle_diff': angle_diff,
        'scale': scale,
        'union_x': union_x,
        'M': M
    }
    np.save(OUTPUT_BASE / "transformacion_config.npy", config)

    print("\n✅ COMPLETADO")
    print(f"   Configuración guardada en: {OUTPUT_BASE}")
    print("\n💡 ¿Se ve todo el campo completo?")
    print("="*70)

if __name__ == "__main__":
    main()
