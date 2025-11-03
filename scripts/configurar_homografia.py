import cv2
import numpy as np
from pathlib import Path
import os
import glob
import subprocess
import tempfile
from config_utils import obtener_carpeta_configuracion

class HomographyConfigurator:
    def __init__(self):
        self.calibration_folder = obtener_carpeta_configuracion()
        self.points_left = []
        self.points_right = []
        self.current_image = None
        self.window_name = ""
        self.display_scale = 1.0  # Escala de visualización
        self.original_size = (0, 0)  # Tamaño original de la imagen
        self.offset_x = 0  # Offset X del letterbox
        self.offset_y = 0  # Offset Y del letterbox
        self.scaled_image_backup = None  # Backup para reset

    def extraer_frame_de_video(self, video_path, output_path):
        """
        Extrae un frame del video usando ffmpeg
        """
        print(f"  Extrayendo frame de: {os.path.basename(video_path)}...")

        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-ss', '00:00:02',  # Segundo 2
            '-frames:v', '1',
            '-y',  # Sobrescribir
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode == 0:
            print(f"  Frame extraído: {output_path}")
            return True
        else:
            print(f"  ERROR: No se pudo extraer frame")
            return False

    def obtener_imagen_o_extraer(self, ruta_input, nombre_camara):
        """
        Si es una imagen, la devuelve.
        Si es una carpeta, busca el primer video y extrae un frame.
        Si es un video, extrae un frame.
        """
        ruta = Path(ruta_input)

        # Si es una imagen directamente
        if ruta.is_file() and ruta.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
            print(f"  Usando imagen: {ruta.name}")
            return str(ruta)

        # Si es una carpeta, buscar primer video
        if ruta.is_dir():
            print(f"\n  Detectada carpeta: {ruta.name}")
            print(f"  Buscando primer video...")

            extensiones = ['*.MP4', '*.mp4', '*.MOV', '*.mov', '*.AVI', '*.avi']
            videos = []
            for ext in extensiones:
                videos.extend(glob.glob(os.path.join(ruta, ext)))

            if not videos:
                print(f"  ERROR: No se encontraron videos en {ruta}")
                return None

            # Ordenar por fecha y tomar el primero
            videos.sort(key=os.path.getmtime)
            video_path = videos[0]
            print(f"  Primer video encontrado: {os.path.basename(video_path)}")

            # Extraer frame a carpeta temporal
            output_frame = self.calibration_folder / f"temp_frame_{nombre_camara}.jpg"
            if self.extraer_frame_de_video(video_path, output_frame):
                return str(output_frame)
            else:
                return None

        # Si es un archivo de video directamente
        if ruta.is_file() and ruta.suffix.lower() in ['.mp4', '.mov', '.avi']:
            print(f"\n  Detectado video: {ruta.name}")
            output_frame = self.calibration_folder / f"temp_frame_{nombre_camara}.jpg"
            if self.extraer_frame_de_video(str(ruta), output_frame):
                return str(output_frame)
            else:
                return None

        print(f"  ERROR: No se reconoce el tipo de archivo/carpeta")
        return None
        
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Restar offset del letterbox
            x_scaled = x - self.offset_x
            y_scaled = y - self.offset_y

            # Verificar que el click esté dentro de la imagen (no en bordes negros)
            if x_scaled < 0 or y_scaled < 0:
                print(f"  ⚠ Click fuera de la imagen (en borde negro). Inténtalo de nuevo.")
                return

            # Convertir coordenadas escaladas a originales
            x_original = int(x_scaled / self.display_scale)
            y_original = int(y_scaled / self.display_scale)

            # Verificar límites
            w_original, h_original = self.original_size
            if x_original >= w_original or y_original >= h_original:
                print(f"  ⚠ Click fuera de la imagen. Inténtalo de nuevo.")
                return

            if param == "left":
                self.points_left.append((x_original, y_original))
                num_punto = len(self.points_left)
                print(f"✓ Punto {num_punto} marcado en coordenadas originales: ({x_original}, {y_original})")
            else:
                self.points_right.append((x_original, y_original))
                num_punto = len(self.points_right)
                print(f"✓ Punto {num_punto} marcado en coordenadas originales: ({x_original}, {y_original})")

            # Dibujar círculos pequeños para más precisión
            cv2.circle(self.current_image, (x, y), 5, (0, 255, 0), -1)  # Círculo verde pequeño
            cv2.circle(self.current_image, (x, y), 6, (0, 0, 0), 1)     # Borde negro fino
            cv2.circle(self.current_image, (x, y), 1, (255, 255, 255), -1)  # Punto blanco central
            # Número más lejos para no tapar
            cv2.putText(self.current_image, str(len(self.points_left if param == "left" else self.points_right)),
                       (x + 20, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(self.window_name, self.current_image)
    
    def seleccionar_puntos(self, image, title, side, instrucciones_puntos):
        """
        Muestra la imagen COMPLETA con letterbox (barras negras) para forzar
        que OpenCV muestre TODO sin recortar.
        """
        # Obtener tamaño de la imagen original
        h_original, w_original = image.shape[:2]

        print(f"\n  Resolución original del video: {w_original}x{h_original}")

        # Tamaño objetivo (casi pantalla completa para máxima precisión)
        target_width = 2400   # Más grande para mejor precisión
        target_height = 1350

        # Calcular escala para que quepa COMPLETA manteniendo aspecto
        scale = min(target_width / w_original, target_height / h_original)

        # Dimensiones escaladas de la imagen
        scaled_w = int(w_original * scale)
        scaled_h = int(h_original * scale)

        print(f"  Imagen escalada a: {scaled_w}x{scaled_h} (escala: {scale:.3f})")

        # Redimensionar la imagen proporcionalmente
        scaled_image = cv2.resize(image, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)

        # Crear imagen negra del tamaño objetivo (letterbox)
        letterbox_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)

        # Calcular posición para centrar la imagen escalada
        offset_x = (target_width - scaled_w) // 2
        offset_y = (target_height - scaled_h) // 2

        print(f"  Canvas final: {target_width}x{target_height} (ventana grande)")
        print(f"  Offset: x={offset_x}, y={offset_y}")
        print(f"  ✓ Ventana grande para máxima precisión\n")

        # Colocar la imagen escalada en el centro del letterbox
        letterbox_image[offset_y:offset_y+scaled_h, offset_x:offset_x+scaled_w] = scaled_image

        # Guardar parámetros para convertir clicks
        self.display_scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.original_size = (w_original, h_original)

        self.current_image = letterbox_image.copy()
        self.scaled_image_backup = scaled_image.copy()  # Para reset
        self.window_name = title

        # Crear ventana AUTOSIZE (no permite redimensionar, muestra TODO)
        cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)

        cv2.setMouseCallback(title, self.mouse_callback, side)
        cv2.imshow(title, self.current_image)

        print(f"\n{'='*60}")
        print(f"SELECCIONANDO PUNTOS: {title}")
        print(f"{'='*60}")
        print("\nSELECCIONA LOS SIGUIENTES 6 PUNTOS EN ESTE ORDEN:")
        for i, punto in enumerate(instrucciones_puntos, 1):
            print(f"  {i}. {punto}")
        print(f"\n{'='*60}")
        print("CONTROLES:")
        print("  - Click izquierdo: Marcar punto")
        print("  - 'r': Reiniciar (borrar todos los puntos)")
        print("  - 'q': Continuar (cuando tengas los 6 puntos)")
        print(f"{'='*60}\n")

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                if side == "left":
                    self.points_left = []
                else:
                    self.points_right = []
                # Recrear letterbox limpio
                letterbox_clean = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                letterbox_clean[offset_y:offset_y+scaled_h, offset_x:offset_x+scaled_w] = self.scaled_image_backup
                self.current_image = letterbox_clean.copy()
                cv2.imshow(title, self.current_image)
                print("\n✗ Puntos reiniciados. Empieza de nuevo desde el punto 1.\n")

        cv2.destroyAllWindows()
    
    def configurar_homografia_interactiva(self):
        print("\n" + "="*60)
        print("CONFIGURACION DE HOMOGRAFIA")
        print("="*60)
        
        print("""
INSTRUCCIONES DE LA HOMOGRAFÍA:

La homografía permite unir perfectamente las dos imágenes de las cámaras.

¿QUÉ VAS A HACER?
- Verás dos imágenes: izquierda y derecha
- Debes marcar EXACTAMENTE 6 PUNTOS CORRESPONDIENTES en ambas imágenes
- Los puntos deben marcarse EN EL MISMO ORDEN en ambas imágenes

LOS 6 PUNTOS A MARCAR (en este orden exacto):
  1. Intersección línea del área con línea de fondo (lado izquierdo)
  2. Esquina del área con línea de fondo (esquina área grande)
  3. Otra esquina del área grande (lado opuesto)
  4. Esquina del campo (corner más alejado/contrario)
  5. Línea de medio campo donde intercepta línea de banda
  6. Centro del campo (punto central)

ENTRADA ACEPTADA:
  - Una imagen (.jpg, .png)
  - Un video (.mp4, .mov) → Se extraerá un frame automáticamente
  - Una carpeta con videos → Se usará el primer video

IMPORTANTE: Las cámaras deben estar en su POSICIÓN FINAL (como en partidos).
""")

        input("Presiona ENTER para continuar...")

        print("\n" + "-"*60)
        print("CAMARA IZQUIERDA:")
        ruta_izq_input = input("Ruta (imagen/video/carpeta): ").strip()
        frame_izq_path = self.obtener_imagen_o_extraer(ruta_izq_input, "izq")

        if not frame_izq_path:
            print("\nERROR: No se pudo obtener imagen de cámara izquierda")
            return

        print("\n" + "-"*60)
        print("CAMARA DERECHA:")
        ruta_der_input = input("Ruta (imagen/video/carpeta): ").strip()
        frame_der_path = self.obtener_imagen_o_extraer(ruta_der_input, "der")

        if not frame_der_path:
            print("\nERROR: No se pudo obtener imagen de cámara derecha")
            return

        print("\n" + "-"*60)
        print("Cargando imágenes...")
        img_left = cv2.imread(frame_izq_path)
        img_right = cv2.imread(frame_der_path)

        if img_left is None or img_right is None:
            print("ERROR: No se pudieron cargar las imágenes")
            print(f"  Izquierda: {frame_izq_path}")
            print(f"  Derecha: {frame_der_path}")
            return

        print(f"\n  DEBUG - Tamaño ORIGINAL extraído del video:")
        print(f"    Izquierda: {img_left.shape[1]}x{img_left.shape[0]}")
        print(f"    Derecha: {img_right.shape[1]}x{img_right.shape[0]}")

        # Preguntar si quiere usar undistort o imagen RAW
        print("\n" + "="*60)
        print("CORRECCIÓN DE DISTORSIÓN")
        print("="*60)
        print("\nLas action cameras tienen distorsión de lente.")
        print("Opciones:")
        print("  1. CON corrección (undistort) - Recomendado si calibración correcta")
        print("  2. SIN corrección (RAW) - Usar si calibración tiene problemas")
        print("\nNOTA: Si ves imagen casi toda negra, la calibración está mal.")
        print("      En ese caso, elige opción 2 (SIN corrección) o re-calibra.\n")

        usar_undistort = input("¿Aplicar corrección de distorsión? (s/n): ").strip().lower()

        if usar_undistort == 's':
            cal_left = np.load(self.calibration_folder / "calibracion_cam_izq.npz")
            cal_right = np.load(self.calibration_folder / "calibracion_cam_der.npz")

            # Obtener nuevo tamaño óptimo que NO recorta nada
            h_left, w_left = img_left.shape[:2]
            h_right, w_right = img_right.shape[:2]

            new_camera_matrix_left, roi_left = cv2.getOptimalNewCameraMatrix(
                cal_left['camera_matrix'], cal_left['dist_coeffs'],
                (w_left, h_left), alpha=1.0, newImgSize=(w_left, h_left)
            )
            new_camera_matrix_right, roi_right = cv2.getOptimalNewCameraMatrix(
                cal_right['camera_matrix'], cal_right['dist_coeffs'],
                (w_right, h_right), alpha=1.0, newImgSize=(w_right, h_right)
            )

            print(f"\n  Aplicando corrección de distorsión (alpha=1.0 = SIN recortar)...")

            # Undistort con nueva matriz que NO recorta
            img_left = cv2.undistort(img_left, cal_left['camera_matrix'],
                                     cal_left['dist_coeffs'], None, new_camera_matrix_left)
            img_right = cv2.undistort(img_right, cal_right['camera_matrix'],
                                       cal_right['dist_coeffs'], None, new_camera_matrix_right)

            print(f"  DEBUG - Tamaño DESPUÉS de undistort:")
            print(f"    Izquierda: {img_left.shape[1]}x{img_left.shape[0]}")
            print(f"    Derecha: {img_right.shape[1]}x{img_right.shape[0]}")
            print(f"  ✓ Imagen COMPLETA mantenida (alpha=1.0)\n")
        else:
            print(f"\n  ⚠ Usando imágenes RAW SIN corrección de distorsión")
            print(f"  Las imágenes tendrán la curvatura original de la lente")
            print(f"  Esto puede funcionar si ambas cámaras tienen distorsión similar\n")

        # Instrucciones específicas de los 6 puntos a marcar
        instrucciones_puntos = [
            "Intersección línea del área con línea de fondo (lado izquierdo)",
            "Esquina del área con línea de fondo (esquina del área grande)",
            "Otra esquina del área grande (lado opuesto)",
            "Esquina del campo (corner más alejado/contrario)",
            "Línea de medio campo donde intercepta línea de banda",
            "Centro del campo (punto central)"
        ]

        print("\n" + "="*60)
        print("PASO 1: IMAGEN IZQUIERDA")
        print("="*60)
        print("\n¡IMPORTANTE! Marca EXACTAMENTE estos 6 puntos en este orden.")
        print("Los tendrás que marcar EN EL MISMO ORDEN en la imagen derecha.\n")
        self.seleccionar_puntos(img_left, "Imagen IZQUIERDA", "left", instrucciones_puntos)

        print("\n" + "="*60)
        print("PASO 2: IMAGEN DERECHA")
        print("="*60)
        print("\n¡IMPORTANTE! Marca los MISMOS puntos EN EL MISMO ORDEN.\n")
        self.seleccionar_puntos(img_right, "Imagen DERECHA", "right", instrucciones_puntos)
        
        if len(self.points_left) != len(self.points_right):
            print(f"\n{'='*60}")
            print("ERROR: DIFERENTE NÚMERO DE PUNTOS")
            print(f"{'='*60}")
            print(f"  Izquierda: {len(self.points_left)} puntos")
            print(f"  Derecha: {len(self.points_right)} puntos")
            print("\nDebes marcar el MISMO número de puntos en ambas imágenes.")
            print(f"{'='*60}\n")
            return

        if len(self.points_left) < 4:
            print(f"\n{'='*60}")
            print("ERROR: PUNTOS INSUFICIENTES")
            print(f"{'='*60}")
            print(f"  Puntos marcados: {len(self.points_left)}")
            print(f"  Mínimo requerido: 4 puntos")
            print(f"  Recomendado: 6 puntos")
            print(f"{'='*60}\n")
            return

        if len(self.points_left) != 6:
            print(f"\n{'='*60}")
            print("ADVERTENCIA: NO SON 6 PUNTOS")
            print(f"{'='*60}")
            print(f"  Puntos marcados: {len(self.points_left)}")
            print(f"  Recomendado: 6 puntos")
            print("\nPara mejor precisión, se recomienda usar exactamente 6 puntos.")
            continuar = input("¿Continuar de todos modos? (s/n): ").strip().lower()
            if continuar != 's':
                print("Operación cancelada. Vuelve a ejecutar el script.\n")
                return
        
        print(f"\nCalculando homografia con {len(self.points_left)} puntos...")
        pts_left = np.float32(self.points_left)
        pts_right = np.float32(self.points_right)
        
        H, status = cv2.findHomography(pts_right, pts_left, cv2.RANSAC, 5.0)
        
        homography_file = self.calibration_folder / "matriz_homografia.npy"
        np.save(str(homography_file), H)
        
        print(f"\nHomografia calculada y guardada!")
        print(f"Archivo: {homography_file}")
        
        print(f"\nGenerando vista previa del resultado...")
        
        h, w = img_left.shape[:2]
        img_right_warped = cv2.warpPerspective(img_right, H, (w * 2, h))
        
        panorama = img_right_warped.copy()
        panorama[0:h, 0:w] = img_left
        
        preview_path = self.calibration_folder / "preview_panorama.jpg"
        cv2.imwrite(str(preview_path), panorama)
        
        print(f"Vista previa guardada en: {preview_path}")
        print(f"\nCONFIGURACION COMPLETADA!")
        print(f"\nSiguiente paso: Configurar Google Drive")
        print(f"python ~/futbol_processor/scripts/configurar_drive.py")

if __name__ == "__main__":
    configurator = HomographyConfigurator()
    configurator.configurar_homografia_interactiva()