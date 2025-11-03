import cv2
import numpy as np
import os
from pathlib import Path
from config_utils import obtener_carpeta_configuracion

CHESSBOARD_SIZE = (9, 6)
SQUARE_SIZE = 25

class CameraCalibrator:
    def __init__(self):
        self.calibration_folder = obtener_carpeta_configuracion()
        
    def calibrar_desde_video(self, video_path, nombre_camara):
        print(f"\nCalibrando {nombre_camara}...")
        print(f"Procesando video: {video_path}")
        
        objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
        objp *= SQUARE_SIZE
        
        objpoints = []
        imgpoints = []
        
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        calibration_images_used = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            if frame_count % 30 != 0:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)
            
            if ret:
                objpoints.append(objp)
                
                corners_refined = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )
                imgpoints.append(corners_refined)
                
                calibration_images_used += 1
                print(f"Patron detectado en frame {frame_count} ({calibration_images_used} patrones)")
        
        cap.release()
        
        if calibration_images_used < 10:
            print(f"ERROR: Solo se detectaron {calibration_images_used} patrones.")
            print(f"Necesitas al menos 10. Graba un video mejor del tablero.")
            return False
        
        print(f"\nCalculando parametros de calibracion...")
        img_shape = gray.shape[::-1]
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_shape, None, None
        )
        
        total_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], 
                                              camera_matrix, dist_coeffs)
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            total_error += error
        
        mean_error = total_error / len(objpoints)
        
        calibration_file = self.calibration_folder / f"calibracion_{nombre_camara}.npz"
        np.savez(
            str(calibration_file),
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            image_shape=img_shape,
            reprojection_error=mean_error
        )
        
        print(f"\nCalibracion completada!")
        print(f"Error de reproyeccion: {mean_error:.3f} pixeles")
        print(f"Guardado en: {calibration_file}")
        
        return True
    
    def guia_interactiva(self):
        print("\n" + "="*60)
        print("GUIA DE CALIBRACION DE CAMARAS")
        print("="*60)
        
        print("""
PASOS PREVIOS:
1. Imprime un tablero de ajedrez de 9x6
2. Pegalo en un carton rigido
3. Graba un video de 30-60 segundos con CADA camara:
   - Mueve el tablero despacio
   - Acercalo y alejalo
   - Inclinalo en diferentes angulos
   - Cubre diferentes partes del encuadre
   - Manten buena iluminacion
4. Copia esos videos a tu Mac
""")
        
        input("Presiona ENTER cuando tengas los videos listos...")
        
        print("\n" + "-"*60)
        video_izq = input("Ruta del video de la CAMARA IZQUIERDA: ").strip()
        if os.path.exists(video_izq):
            self.calibrar_desde_video(video_izq, "cam_izq")
        else:
            print("Archivo no encontrado")
            return
        
        print("\n" + "-"*60)
        video_der = input("Ruta del video de la CAMARA DERECHA: ").strip()
        if os.path.exists(video_der):
            self.calibrar_desde_video(video_der, "cam_der")
        else:
            print("Archivo no encontrado")
            return
        
        print("\n" + "="*60)
        print("CALIBRACION COMPLETADA!")
        print("="*60)
        print(f"\nArchivos guardados en: {self.calibration_folder}")
        print("\nSiguiente paso: Configurar la homografia")
        print("python ~/futbol_processor/scripts/configurar_homografia.py")

if __name__ == "__main__":
    calibrator = CameraCalibrator()
    calibrator.guia_interactiva()