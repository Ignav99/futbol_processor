import cv2
import numpy as np
from pathlib import Path
import pickle
from scipy.io import wavfile
from scipy.signal import correlate
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import time
from datetime import datetime
import subprocess
import tempfile
import os
import glob

class PartidoProcessor:
    def __init__(self):
        self.config_folder = Path.home() / "futbol_calibracion"
        self.output_folder = Path.home() / "futbol_output"
        self.output_folder.mkdir(exist_ok=True)
        
        self.cargar_configuraciones()
        
        self.VIEW_WIDTH = 2560
        self.VIEW_HEIGHT = 1440
        self.ball_pos_smoothed = None
        self.smoothing_factor = 0.15
        
    def verificar_configuracion(self):
        """
        Verifica que todos los archivos de configuración existan
        """
        archivos_necesarios = {
            "calibracion_cam_izq.npz": "Calibración cámara izquierda",
            "calibracion_cam_der.npz": "Calibración cámara derecha",
            "matriz_homografia.npy": "Homografía",
            "drive_token.pickle": "Token Google Drive",
            "drive_folder_id.txt": "ID carpeta Drive"
        }

        faltantes = []
        for archivo, descripcion in archivos_necesarios.items():
            if not (self.config_folder / archivo).exists():
                faltantes.append((archivo, descripcion))

        if faltantes:
            print("\n" + "="*60)
            print("ERROR: CONFIGURACIÓN INCOMPLETA")
            print("="*60)
            print("\nFaltan los siguientes archivos de configuración:\n")
            for archivo, descripcion in faltantes:
                print(f"  ✗ {descripcion} ({archivo})")

            print("\n" + "="*60)
            print("PASOS NECESARIOS:")
            print("="*60)

            if any("calibracion" in f[0] for f in faltantes):
                print("\n1. CALIBRAR CÁMARAS:")
                print("   source futbol_processor_env/bin/activate")
                print("   python3 scripts/calibrar_camaras.py")

            if any("homografia" in f[0] for f in faltantes):
                print("\n2. CONFIGURAR HOMOGRAFÍA:")
                print("   python3 scripts/configurar_homografia.py")

            if any("drive" in f[0] for f in faltantes):
                print("\n3. CONFIGURAR GOOGLE DRIVE:")
                print("   python3 scripts/configurar_drive.py")

            print("\n" + "="*60)
            print("Consulta la documentación: docs/LEEME.md")
            print("="*60 + "\n")
            return False

        return True

    def cargar_configuraciones(self):
        print("Verificando configuración...")

        if not self.verificar_configuracion():
            raise FileNotFoundError("Configuración incompleta. Sigue los pasos indicados arriba.")

        print("Cargando configuraciones...")

        cal_izq = np.load(self.config_folder / "calibracion_cam_izq.npz")
        cal_der = np.load(self.config_folder / "calibracion_cam_der.npz")

        self.camera_matrix_left = cal_izq['camera_matrix']
        self.dist_coeffs_left = cal_izq['dist_coeffs']
        self.camera_matrix_right = cal_der['camera_matrix']
        self.dist_coeffs_right = cal_der['dist_coeffs']

        self.homography = np.load(self.config_folder / "matriz_homografia.npy")

        with open(self.config_folder / "drive_token.pickle", 'rb') as token:
            self.drive_creds = pickle.load(token)

        with open(self.config_folder / "drive_folder_id.txt", 'r') as f:
            self.drive_folder_id = f.read().strip()

        print("Configuraciones cargadas correctamente\n")

    def concatenar_videos(self, carpeta_videos):
        """
        Concatena múltiples archivos de video de una carpeta en orden cronológico
        """
        print(f"\nBuscando videos en: {carpeta_videos}")

        # Buscar todos los archivos de video
        extensiones = ['*.MP4', '*.mp4', '*.MOV', '*.mov']
        archivos = []
        for ext in extensiones:
            archivos.extend(glob.glob(os.path.join(carpeta_videos, ext)))

        if not archivos:
            print(f"ERROR: No se encontraron videos en {carpeta_videos}")
            return None

        # Ordenar por fecha de creación
        archivos.sort(key=os.path.getmtime)

        print(f"Encontrados {len(archivos)} archivo(s):")
        for i, archivo in enumerate(archivos, 1):
            nombre = os.path.basename(archivo)
            print(f"  {i}. {nombre}")

        # Si solo hay un archivo, devolverlo directamente
        if len(archivos) == 1:
            print("Un solo archivo, no es necesario concatenar")
            return archivos[0]

        # Concatenar múltiples archivos
        print(f"\nConcatenando {len(archivos)} archivos...")

        output_dir = Path.home() / "futbol_output"
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        carpeta_nombre = os.path.basename(carpeta_videos)
        output_file = output_dir / f"concatenado_{carpeta_nombre}_{timestamp}.mp4"

        # Crear archivo de lista para ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for archivo in archivos:
                # Escapar comillas simples en la ruta
                ruta_escapada = archivo.replace("'", "'\\''")
                f.write(f"file '{ruta_escapada}'\n")
            lista_path = f.name

        try:
            # Concatenar usando ffmpeg
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', lista_path,
                '-c', 'copy',
                str(output_file), '-y'
            ]

            resultado = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if resultado.returncode != 0:
                print(f"ERROR en concatenación: {resultado.stderr}")
                return None

            print(f"Videos concatenados exitosamente: {output_file}")
            return str(output_file)

        finally:
            # Limpiar archivo temporal
            if os.path.exists(lista_path):
                os.remove(lista_path)
    
    def sincronizar_videos(self, video1_path, video2_path):
        """
        Sincroniza dos videos usando correlación de audio.
        Ideal para detectar palmadas o sonidos fuertes al inicio.
        """
        print("\nSincronizando videos por audio...")
        print("(Buscando palmada u otro sonido de sincronización)")

        with tempfile.TemporaryDirectory() as tmpdir:
            audio1 = Path(tmpdir) / "audio1.wav"
            audio2 = Path(tmpdir) / "audio2.wav"

            print("Extrayendo audio del video izquierdo...")
            subprocess.run(['ffmpeg', '-i', str(video1_path), '-vn', '-acodec', 'pcm_s16le',
                          '-ar', '44100', '-ac', '1', str(audio1), '-y'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print("Extrayendo audio del video derecho...")
            subprocess.run(['ffmpeg', '-i', str(video2_path), '-vn', '-acodec', 'pcm_s16le',
                          '-ar', '44100', '-ac', '1', str(audio2), '-y'],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            rate1, data1 = wavfile.read(audio1)
            rate2, data2 = wavfile.read(audio2)

            # Convertir a mono si es estéreo
            if len(data1.shape) > 1:
                data1 = data1.mean(axis=1)
            if len(data2.shape) > 1:
                data2 = data2.mean(axis=1)

            # Normalizar los datos
            data1 = data1.astype(np.float64)
            data2 = data2.astype(np.float64)

            # Usar solo los primeros 60 segundos para sincronización (más rápido)
            max_samples = min(len(data1), len(data2), rate1 * 60)
            data1_short = data1[:max_samples]
            data2_short = data2[:max_samples]

            print("Calculando correlación cruzada...")
            correlation = correlate(data1_short, data2_short, mode='full')
            lag = np.argmax(correlation) - len(data2_short) + 1

            fps = 30
            offset_frames = int(lag * fps / rate1)
            offset_seconds = lag / rate1

            print(f"Sincronización detectada:")
            print(f"  Offset: {offset_frames} frames ({offset_seconds:.2f} segundos)")

            return offset_frames
    
    def detectar_balon(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        
        mask = cv2.inRange(hsv, lower_white, upper_white)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        circles = cv2.HoughCircles(
            mask, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
            param1=50, param2=30, minRadius=5, maxRadius=50
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            largest_circle = max(circles[0], key=lambda c: c[2])
            return (int(largest_circle[0]), int(largest_circle[1]))
        
        return None
    
    def suavizar_posicion(self, new_pos):
        if self.ball_pos_smoothed is None:
            self.ball_pos_smoothed = new_pos
        else:
            self.ball_pos_smoothed = (
                int(self.ball_pos_smoothed[0] * (1 - self.smoothing_factor) + new_pos[0] * self.smoothing_factor),
                int(self.ball_pos_smoothed[1] * (1 - self.smoothing_factor) + new_pos[1] * self.smoothing_factor)
            )
        return self.ball_pos_smoothed
    
    def crear_vista_seguimiento(self, panorama, ball_pos):
        h, w = panorama.shape[:2]
        
        smooth_pos = self.suavizar_posicion(ball_pos)
        
        x_center, y_center = smooth_pos
        
        x1 = max(0, x_center - self.VIEW_WIDTH // 2)
        y1 = max(0, y_center - self.VIEW_HEIGHT // 2)
        x2 = min(w, x1 + self.VIEW_WIDTH)
        y2 = min(h, y1 + self.VIEW_HEIGHT)
        
        if x2 - x1 < self.VIEW_WIDTH:
            x1 = max(0, x2 - self.VIEW_WIDTH)
        if y2 - y1 < self.VIEW_HEIGHT:
            y1 = max(0, y2 - self.VIEW_HEIGHT)
        
        vista = panorama[y1:y2, x1:x2]
        
        if vista.shape[:2] != (self.VIEW_HEIGHT, self.VIEW_WIDTH):
            vista = cv2.resize(vista, (self.VIEW_WIDTH, self.VIEW_HEIGHT))
        
        return vista
    
    def subir_a_drive(self, file_path, nombre_archivo):
        print(f"\nSubiendo {nombre_archivo} a Google Drive...")
        
        try:
            service = build('drive', 'v3', credentials=self.drive_creds)
            
            file_metadata = {
                'name': nombre_archivo,
                'parents': [self.drive_folder_id]
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='video/mp4',
                resumable=True
            )
            
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,webViewLink'
            )
            
            response = None
            last_progress = 0
            
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress - last_progress >= 10:
                        print(f"   Progreso: {progress}%")
                        last_progress = progress
            
            print(f"Subido exitosamente!")
            print(f"   Link: {response.get('webViewLink')}")
            
            return True
            
        except Exception as e:
            print(f"Error al subir: {str(e)}")
            return False
    
    def procesar_partido(self, carpeta_izq, carpeta_der):
        """
        Procesa un partido completo desde carpetas de videos.
        Concatena automáticamente múltiples archivos si es necesario.
        """
        print("\n" + "="*60)
        print("PROCESANDO PARTIDO")
        print("="*60)

        inicio = time.time()

        # Concatenar videos de cada cámara si hay múltiples archivos
        print("\n--- PROCESANDO CAMARA IZQUIERDA ---")
        video_izq_path = self.concatenar_videos(carpeta_izq)
        if not video_izq_path:
            print("ERROR: No se pudo procesar la cámara izquierda")
            return

        print("\n--- PROCESANDO CAMARA DERECHA ---")
        video_der_path = self.concatenar_videos(carpeta_der)
        if not video_der_path:
            print("ERROR: No se pudo procesar la cámara derecha")
            return

        # Sincronizar videos
        offset = self.sincronizar_videos(video_izq_path, video_der_path)
        
        print("\nAbriendo videos...")
        cap_left = cv2.VideoCapture(str(video_izq_path))
        cap_right = cv2.VideoCapture(str(video_der_path))
        
        if offset > 0:
            for _ in range(abs(offset)):
                cap_right.read()
        elif offset < 0:
            for _ in range(abs(offset)):
                cap_left.read()
        
        fps = int(cap_left.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap_left.get(cv2.CAP_PROP_FRAME_COUNT))
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_tactico = self.output_folder / f"partido_tactico_{timestamp}.mp4"
        output_seguimiento = self.output_folder / f"partido_seguimiento_{timestamp}.mp4"
        
        ret, frame_left = cap_left.read()
        ret, frame_right = cap_right.read()
        
        if not ret:
            print("Error leyendo frames")
            return
        
        frame_left = cv2.undistort(frame_left, self.camera_matrix_left, self.dist_coeffs_left)
        frame_right = cv2.undistort(frame_right, self.camera_matrix_right, self.dist_coeffs_right)
        
        h, w = frame_left.shape[:2]
        frame_right_warped = cv2.warpPerspective(frame_right, self.homography, (w * 2, h))
        panorama_test = frame_right_warped.copy()
        panorama_test[0:h, 0:w] = frame_left
        
        tactico_height = 1440
        tactico_width = int(panorama_test.shape[1] * (tactico_height / panorama_test.shape[0]))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer_tactico = cv2.VideoWriter(
            str(output_tactico), fourcc, fps,
            (tactico_width, tactico_height)
        )
        writer_seguimiento = cv2.VideoWriter(
            str(output_seguimiento), fourcc, fps,
            (self.VIEW_WIDTH, self.VIEW_HEIGHT)
        )
        
        cap_left.set(cv2.CAP_PROP_POS_FRAMES, max(0, offset) if offset > 0 else 0)
        cap_right.set(cv2.CAP_PROP_POS_FRAMES, max(0, -offset) if offset < 0 else 0)
        
        print(f"Configuracion completa")
        print(f"   Resolucion tactica: {tactico_width}x{tactico_height}")
        print(f"   Resolucion seguimiento: {self.VIEW_WIDTH}x{self.VIEW_HEIGHT}")
        print(f"   FPS: {fps}")
        print(f"   Total frames: {total_frames}")
        
        print(f"\nProcesando frames...")
        
        frame_count = 0
        last_ball_pos = None
        
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
                print(f"   Frame {frame_count}/{total_frames} ({progress:.1f}%) - "
                      f"ETA: {int(eta/60)}:{int(eta%60):02d}")
            
            frame_left = cv2.undistort(frame_left, self.camera_matrix_left, self.dist_coeffs_left)
            frame_right = cv2.undistort(frame_right, self.camera_matrix_right, self.dist_coeffs_right)
            
            frame_right_warped = cv2.warpPerspective(frame_right, self.homography, (w * 2, h))
            panorama = frame_right_warped.copy()
            panorama[0:h, 0:w] = frame_left
            
            ball_pos = self.detectar_balon(panorama)
            
            if ball_pos is None:
                ball_pos = last_ball_pos if last_ball_pos else (panorama.shape[1]//2, panorama.shape[0]//2)
            else:
                last_ball_pos = ball_pos
            
            frame_tactico = cv2.resize(panorama, (tactico_width, tactico_height))
            frame_seguimiento = self.crear_vista_seguimiento(panorama, ball_pos)
            
            writer_tactico.write(frame_tactico)
            writer_seguimiento.write(frame_seguimiento)
        
        cap_left.release()
        cap_right.release()
        writer_tactico.release()
        writer_seguimiento.release()
        
        tiempo_total = time.time() - inicio
        
        print(f"\nProcesamiento completado en {int(tiempo_total/60)}:{int(tiempo_total%60):02d}")
        print(f"Archivos generados:")
        print(f"   {output_tactico}")
        print(f"   {output_seguimiento}")
        
        print(f"\nSubiendo a Google Drive...")
        self.subir_a_drive(output_tactico, f"tactico_{timestamp}.mp4")
        self.subir_a_drive(output_seguimiento, f"seguimiento_{timestamp}.mp4")
        
        print(f"\nTODO COMPLETADO!")
        
    def guia_interactiva(self):
        print("\n" + "="*60)
        print("PROCESADOR DE PARTIDOS")
        print("="*60)

        print("\nEste script procesará automáticamente los videos de las carpetas:")
        print("  - Cámara izquierda: ~/Desktop/raw_video_left")
        print("  - Cámara derecha: ~/Desktop/raw_video_right")
        print("\nSi tienes múltiples archivos (partido en partes), se concatenarán automáticamente.")
        print("TIP: Da una palmada al inicio para mejor sincronización\n")

        # Rutas por defecto
        carpeta_izq = str(Path.home() / "Desktop" / "raw_video_left")
        carpeta_der = str(Path.home() / "Desktop" / "raw_video_right")

        # Permitir rutas personalizadas
        usar_default = input("¿Usar carpetas por defecto? (s/n): ").strip().lower()

        if usar_default != 's':
            carpeta_izq = input("Ruta carpeta IZQUIERDA: ").strip()
            carpeta_der = input("Ruta carpeta DERECHA: ").strip()

        # Verificar que las carpetas existen
        if not Path(carpeta_izq).exists():
            print(f"ERROR: Carpeta no existe: {carpeta_izq}")
            return

        if not Path(carpeta_der).exists():
            print(f"ERROR: Carpeta no existe: {carpeta_der}")
            return

        # Mostrar resumen
        print(f"\nCarpetas a procesar:")
        print(f"  Izquierda: {carpeta_izq}")
        print(f"  Derecha: {carpeta_der}")

        confirmar = input(f"\n¿Procesar partido? (s/n): ").strip().lower()

        if confirmar == 's':
            self.procesar_partido(carpeta_izq, carpeta_der)
        else:
            print("Operación cancelada")

if __name__ == "__main__":
    processor = PartidoProcessor()
    processor.guia_interactiva()