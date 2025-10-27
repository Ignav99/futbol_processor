import cv2
import numpy as np
from pathlib import Path

class HomographyConfigurator:
    def __init__(self):
        self.calibration_folder = Path.home() / "futbol_calibracion"
        self.points_left = []
        self.points_right = []
        self.current_image = None
        self.window_name = ""
        
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
""")
        
        input("Presiona ENTER para continuar...")
        
        print("\n" + "-"*60)
        frame_izq_path = input("Ruta de un FRAME de la camara IZQUIERDA: ").strip()
        frame_der_path = input("Ruta de un FRAME de la camara DERECHA: ").strip()
        
        img_left = cv2.imread(frame_izq_path)
        img_right = cv2.imread(frame_der_path)
        
        if img_left is None or img_right is None:
            print("Error al cargar las imagenes")
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