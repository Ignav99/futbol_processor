import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class DriveConfigurator:
    def __init__(self):
        self.config_folder = Path.home() / "futbol_calibracion"
        self.config_folder.mkdir(exist_ok=True)
        self.credentials_file = self.config_folder / "drive_credentials.json"
        self.token_file = self.config_folder / "drive_token.pickle"
    
    def configurar(self):
        print("\n" + "="*60)
        print("CONFIGURACION DE GOOGLE DRIVE")
        print("="*60)
        
        print(f"""
PASOS PREVIOS (en Google Cloud Console):

1. Ve a: https://console.cloud.google.com/
2. Crea un nuevo proyecto (o usa uno existente)
3. Habilita la API de Google Drive:
   - APIs & Services > Library
   - Busca "Google Drive API"
   - Click en "Enable"
4. Crea credenciales OAuth 2.0:
   - APIs & Services > Credentials
   - Create Credentials > OAuth client ID
   - Application type: Desktop app
   - Nombre: "Futbol Video Processor"
5. Descarga el archivo JSON de credenciales
6. Guardalo como: {self.credentials_file}

""")
        
        if not self.credentials_file.exists():
            input(f"Presiona ENTER cuando hayas guardado el archivo en:\n{self.credentials_file}\n")
            
            if not self.credentials_file.exists():
                print(f"Archivo no encontrado: {self.credentials_file}")
                return False
        
        creds = None
        
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refrescando credenciales...")
                creds.refresh(Request())
            else:
                print("\nAbriendo navegador para autenticacion...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        print("\nProbando conexion con Google Drive...")
        try:
            service = build('drive', 'v3', credentials=creds)
            
            folder_name = "Partidos Futbol"
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                print(f"Carpeta '{folder_name}' encontrada")
            else:
                print(f"Creando carpeta '{folder_name}'...")
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')
            
            folder_id_file = self.config_folder / "drive_folder_id.txt"
            with open(folder_id_file, 'w') as f:
                f.write(folder_id)
            
            print(f"Configuracion completada!")
            print(f"\nLos videos se subiran a la carpeta: {folder_name}")
            print(f"(ID: {folder_id})")
            print(f"\nTodo listo! Ya puedes procesar partidos")
            print(f"python ~/futbol_processor/scripts/procesar_partido.py")
            
            return True
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return False

if __name__ == "__main__":
    configurator = DriveConfigurator()
    configurator.configurar()