# Sistema de Grabación Panorámica de Partidos de Fútbol

Sistema automatizado para procesar partidos grabados con dos action cameras Wolfgang GA120, generando videos panorámicos y con seguimiento automático del balón.

## 🎥 Descripción del Sistema

Este proyecto procesa videos grabados con dos cámaras action camera (Wolfgang GA120) montadas en un trípode, cada una apuntando a una mitad del campo de fútbol.

### Características Principales

**Fase 1 (Actual):**
- ✓ Fusión automática de dos cámaras en panorama completo
- ✓ Sincronización automática por audio (detección de palmada)
- ✓ Concatenación automática de múltiples archivos (las cámaras graban en partes de ~18 min)
- ✓ Generación de dos videos de salida:
  - **Video Táctico**: Vista panorámica completa del campo
  - **Video de Seguimiento**: Zoom automático siguiendo el balón
- ✓ Subida automática a Google Drive

**Fase 2 (Futuro):**
- Análisis automático del partido
- Cortes automáticos de jugadas
- Estadísticas: ocasiones, tiros, pases, etc.

---

## 📋 Requisitos del Sistema

### Hardware
- Mac (macOS)
- 2x Wolfgang GA120 Action Cameras
- Trípode
- Espacio en disco: ~20GB libres por partido procesado

### Especificaciones de Grabación
- **Resolución**: 2.7K
- **FPS**: 30
- **Formato**: MP4/MOV
- **Audio**: Necesario para sincronización

---

## 🚀 Instalación (Una Sola Vez)

### 1. Clonar el Repositorio

```bash
cd ~
git clone https://github.com/tu-usuario/futbol_processor.git
cd futbol_processor
```

### 2. Ejecutar Instalación Automática

```bash
bash setup_inicial.sh
```

Este script:
- Verifica Python 3 y ffmpeg
- Crea un entorno virtual Python
- Instala todas las dependencias
- Crea las carpetas necesarias

### 3. Verificar Instalación

```bash
source ~/futbol_processor_env/bin/activate
python3 scripts/verificar_instalacion.py
```

---

## ⚙️ Configuración Inicial (Una Sola Vez)

### Paso 1: Calibrar Cámaras

Las cámaras tienen distorsión de lente que debe corregirse.

**Materiales necesarios:**
- Tablero de ajedrez 9x6 impreso en A4
- Cartón rígido para pegar el tablero

**Proceso:**
1. Pega el tablero en el cartón para que quede rígido
2. Graba un video de 30-60 segundos con CADA cámara:
   - Mueve el tablero lentamente
   - Acércalo y aléjalo
   - Inclínalo en diferentes ángulos
   - Cubre diferentes partes del encuadre
   - Mantén buena iluminación
3. Copia los videos a tu Mac
4. Ejecuta:
   ```bash
   source ~/futbol_processor_env/bin/activate
   python3 ~/futbol_processor/scripts/calibrar_camaras.py
   ```

### Paso 2: Configurar Homografía

La homografía permite unir las dos imágenes perfectamente.

**Proceso:**
1. Coloca las cámaras en el trípode EN SU POSICIÓN FINAL
2. Graba 5 segundos con ambas cámaras
3. Extrae un frame (imagen) de cada video
4. Ejecuta:
   ```bash
   python3 ~/futbol_processor/scripts/configurar_homografia.py
   ```
5. Selecciona 4-6 puntos correspondientes en ambas imágenes:
   - Esquinas del área
   - Punto de penalti
   - Esquinas del campo
   - Líneas de esquina
   - **IMPORTANTE**: Selecciona los puntos EN EL MISMO ORDEN en ambas imágenes

### Paso 3: Configurar Google Drive

Los videos procesados se suben automáticamente a Google Drive.

**Proceso:**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita la API de Google Drive:
   - APIs & Services → Library
   - Busca "Google Drive API"
   - Click en "Enable"
4. Crea credenciales OAuth 2.0:
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Nombre: "Futbol Video Processor"
5. Descarga el archivo JSON de credenciales
6. Guárdalo como: `~/futbol_calibracion/drive_credentials.json`
7. Ejecuta:
   ```bash
   python3 ~/futbol_processor/scripts/configurar_drive.py
   ```

---

## 🎬 Uso - Procesar un Partido

### 1. Preparar las Grabaciones

**Antes del partido:**
1. Coloca las cámaras en el trípode (misma posición que en la calibración)
2. Enciende ambas cámaras
3. **Da una palmada fuerte** cerca de las cámaras (para sincronización)
4. Graba el partido normalmente
5. Las cámaras cortarán automáticamente cada ~18 minutos (no te preocupes)

**Descanso:**
- Puedes pausar las grabaciones
- Al reanudar, da otra palmada

### 2. Copiar Videos al Mac

```bash
# Copia los archivos de las tarjetas SD a estas carpetas:
# - Cámara IZQUIERDA → ~/Desktop/raw_video_left/
# - Cámara DERECHA → ~/Desktop/raw_video_right/
```

Estructura de carpetas:
```
~/Desktop/
├── raw_video_left/
│   ├── GOPR0001.MP4
│   ├── GOPR0002.MP4
│   └── GOPR0003.MP4
└── raw_video_right/
    ├── GOPR0001.MP4
    ├── GOPR0002.MP4
    └── GOPR0003.MP4
```

### 3. Procesar el Partido

**Opción 1: Doble clic** (más fácil)
```bash
# Haz doble clic en:
PROCESAR_PARTIDO.command
```

**Opción 2: Terminal**
```bash
cd ~/futbol_processor
source futbol_processor_env/bin/activate
python3 scripts/procesar_partido.py
```

### 4. ¿Qué Hace el Procesamiento?

1. **Concatena** automáticamente todos los archivos de cada cámara
2. **Sincroniza** los videos usando la palmada
3. **Corrige** la distorsión de las lentes
4. **Fusiona** las dos cámaras en panorama
5. **Detecta** el balón en cada frame
6. **Genera** dos videos:
   - `partido_tactico_YYYYMMDD_HHMMSS.mp4` - Vista completa del campo
   - `partido_seguimiento_YYYYMMDD_HHMMSS.mp4` - Zoom siguiendo el balón
7. **Sube** los videos a Google Drive automáticamente

### 5. Resultados

Los videos se guardan en:
```
~/futbol_output/
```

Y se suben automáticamente a tu carpeta "Partidos Futbol" en Google Drive.

---

## 📁 Estructura del Proyecto

```
futbol_processor/
├── scripts/
│   ├── calibrar_camaras.py        # Calibración de lentes
│   ├── configurar_homografia.py   # Unión de cámaras
│   ├── configurar_drive.py        # Setup Google Drive
│   ├── procesar_partido.py        # Script principal
│   └── verificar_instalacion.py   # Verificar dependencias
├── docs/
│   └── LEEME.md                   # Esta documentación
├── setup_inicial.sh               # Instalación automática
├── requirements.txt               # Dependencias Python
├── .gitignore                     # Archivos ignorados
└── PROCESAR_PARTIDO.command       # Launcher macOS

Carpetas de usuario:
~/futbol_calibracion/              # Configuraciones (NO subir a git)
~/futbol_output/                   # Videos procesados
~/Desktop/raw_video_left/          # Videos cámara izquierda
~/Desktop/raw_video_right/         # Videos cámara derecha
```

---

## 🔧 Solución de Problemas

### "ffmpeg no encontrado"
```bash
# Instala Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instala ffmpeg
brew install ffmpeg
```

### "No se detecta el balón"
- Verifica que el balón sea blanco
- Mejora la iluminación del campo
- Ajusta los parámetros en `detectar_balon()` en `procesar_partido.py`

### "Sincronización incorrecta"
- Asegúrate de dar una palmada FUERTE al inicio
- La palmada debe ser audible en AMBAS cámaras
- Verifica que el audio esté habilitado en las cámaras

### "Videos no se fusionan bien"
- Asegúrate de usar las cámaras EN LA MISMA POSICIÓN que en la calibración
- Re-haz la configuración de homografía

### "Error al subir a Google Drive"
- Verifica tu conexión a internet
- Re-configura Google Drive: `python3 scripts/configurar_drive.py`

---

## 📝 Tips y Mejores Prácticas

1. **Posición de las cámaras:**
   - Altura: 2-4 metros
   - Ángulo: Ligeramente inclinado hacia abajo
   - Overlap: 10-20% de solapamiento entre cámaras

2. **Grabación:**
   - Siempre da palmada al inicio
   - Verifica que ambas cámaras estén grabando
   - Usa baterías cargadas o alimentación externa

3. **Almacenamiento:**
   - Un partido de 90 min genera ~40GB en bruto
   - Videos procesados: ~10-15GB
   - Limpia `~/futbol_output/` regularmente

4. **Rendimiento:**
   - Procesamiento tarda ~2-3x la duración del partido
   - No uses el Mac para otras tareas mientras procesa
   - Cierra aplicaciones pesadas

---

## 🚀 Próximas Funcionalidades (Fase 2)

- [ ] Detección automática de eventos (goles, tiros, ocasiones)
- [ ] Generación de highlights automáticos
- [ ] Estadísticas del partido
- [ ] Mapa de calor de jugadores
- [ ] Detección de fuera de juego
- [ ] Timeline interactivo

---

## 🤝 Contribuir

Este es un proyecto personal, pero si quieres contribuir:
1. Fork del repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de uso personal. Si quieres usarlo, contacta al autor.

---

## 👤 Autor

**Ignacio Navarro**
- GitHub: [@Ignav99](https://github.com/Ignav99)

---

## 📞 Soporte

Para problemas o preguntas:
1. Revisa la sección "Solución de Problemas"
2. Abre un Issue en GitHub
3. Contacta al autor

---

**¡Disfruta analizando tus partidos!** ⚽
