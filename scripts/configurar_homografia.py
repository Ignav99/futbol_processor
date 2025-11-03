import cv2
import numpy as np
from pathlib import Path
import os
import glob
import subprocess
import tempfile

class HomographyConfigurator:
    def __init__(self):
        self.calibration_folder = Path.home() / "futbol_calibracion"
        self.points_left = []
        self.points_right = []
        self.current_image = None
        self.window_name = ""

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
            if param == "left":
                self.points_left.append((x, y))
                print(f"Punto {len(self.points_left)} en imagen IZQUIERDA: ({x}, {y})")
            else:
                self.points_right.append((x, y))
                print(f"Punto {len(self.points_right)} en imagen DERECHA: ({x}, {y})")
            
            cv2.circle(self.current_image, (x, y), 8, (0, 255, 0), -1)
            cv2.circle(self.current_image, (x, y), 9, (0, 0, 0), 2)
            cv2.putText(self.current_image, str(len(self.points_left if param == "left" else self.points_right)),
                       (x + 15, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow(self.window_name, self.current_image)
    
    def seleccionar_puntos(self, image, title, side):
        self.current_image = image.copy()
        self.window_name = title
        
        cv2.namedWindow(title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(title, 1280, 720)
        cv2.setMouseCallback(title, self.mouse_callback, side)
        cv2.imshow(title, self.current_image)
        
        print(f"\nHaz clic en {title}")
        print("Presiona 'q' cuando hayas seleccionado todos los puntos")
        print("Presiona 'r' para reiniciar")
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                if side == "left":
                    self.points_left = []
                else:
                    self.points_right = []
                self.current_image = image.copy()
                cv2.imshow(title, self.current_image)
                print("Puntos reiniciados")
        
        cv2.destroyAllWindows()
    
    def configurar_homografia_interactiva(self):
        print("\n" + "="*60)
        print("CONFIGURACION DE HOMOGRAFIA")
        print("="*60)
        
        print("""
INSTRUCCIONES:
1. Vas a ver dos imagenes: izquierda y derecha
2. Debes hacer clic en 4-6 PUNTOS CORRESPONDIENTES en ambas imagenes
3. Buenos puntos de referencia:
   - Esquinas del area
   - Punto de penalti
   - Esquinas del campo
   - Lineas de esquina
4. IMPORTANTE: Haz clic en los puntos EN EL MISMO ORDEN en ambas imagenes

NOTA: Puedes pasar:
  - Una imagen (.jpg, .png)
  - Un video (.mp4, .mov) - Se extraerá un frame automáticamente
  - Una carpeta con videos - Se usará el primer video
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
        
        cal_left = np.load(self.calibration_folder / "calibracion_cam_izq.npz")
        cal_right = np.load(self.calibration_folder / "calibracion_cam_der.npz")
        
        img_left = cv2.undistort(img_left, cal_left['camera_matrix'], cal_left['dist_coeffs'])
        img_right = cv2.undistort(img_right, cal_right['camera_matrix'], cal_right['dist_coeffs'])
        
        print("\nPASO 1: Selecciona puntos en la imagen IZQUIERDA")
        self.seleccionar_puntos(img_left, "Imagen IZQUIERDA - Selecciona puntos", "left")
        
        print("\nPASO 2: Selecciona los MISMOS puntos en la imagen DERECHA")
        print("(En el mismo orden)")
        self.seleccionar_puntos(img_right, "Imagen DERECHA - Selecciona puntos", "right")
        
        if len(self.points_left) != len(self.points_right):
            print(f"\nERROR: Diferente numero de puntos")
            print(f"Izquierda: {len(self.points_left)}, Derecha: {len(self.points_right)}")
            return
        
        if len(self.points_left) < 4:
            print(f"\nERROR: Necesitas al menos 4 puntos (tienes {len(self.points_left)})")
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