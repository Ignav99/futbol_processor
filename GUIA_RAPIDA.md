# ⚽ Guía Rápida - Procesamiento de Partidos

## 📋 Configuración Inicial (Una Sola Vez)

### 1. Instalar Dependencias
```bash
bash setup_inicial.sh
```

### 2. Configurar Homografía
```bash
source futbol_processor_env/bin/activate
python3 scripts/configurar_homografia.py
```

**Cuando te pregunte:**
- Cámara izquierda: `~/Desktop/raw_video_left`
- Cámara derecha: `~/Desktop/raw_video_right`
- Corrección de distorsión: `n` (sin undistort)
- Marca los 6 puntos en orden

---

## 🎬 Procesar un Partido (Cada Vez)

### Paso 1: Copiar Videos
Copia los videos de las tarjetas SD a:
- `~/Desktop/raw_video_left/` → Videos cámara izquierda
- `~/Desktop/raw_video_right/` → Videos cámara derecha

### Paso 2: Ejecutar Pipeline
**Opción A: Doble clic**
```
PROCESAR_PARTIDO.command
```

**Opción B: Terminal**
```bash
source futbol_processor_env/bin/activate
python3 procesar_partido_completo.py
```

### Paso 3: Introducir Nombre
```
Nombre del equipo rival: CD Alcala
```

### Paso 4: ¡Listo!
Los videos se guardarán en:
```
/Users/User/Library/CloudStorage/GoogleDrive-.../Analisis de video/CD Alcala/
  ├── CD_Alcala_tactico.mp4
  └── CD_Alcala_seguimiento.mp4
```

---

## 📁 Estructura de Carpetas

```
Desktop/
├── raw_video_left/        ← Copiar videos cámara izquierda aquí
│   ├── GOPR0001.MP4
│   ├── GOPR0002.MP4
│   └── ...
└── raw_video_right/       ← Copiar videos cámara derecha aquí
    ├── GOPR0001.MP4
    ├── GOPR0002.MP4
    └── ...

Google Drive (local)/
└── Analisis de video/     ← Output automático
    ├── CD Alcala/
    │   ├── CD_Alcala_tactico.mp4
    │   └── CD_Alcala_seguimiento.mp4
    ├── Getafe B/
    └── ...
```

---

## ⚙️ Qué Hace el Pipeline Automáticamente

1. ✅ Busca videos en `raw_video_left` y `raw_video_right`
2. ✅ Concatena archivos múltiples (si hay varios)
3. ✅ Sincroniza con audio (detecta palmada)
4. ✅ Carga homografía del proyecto
5. ✅ Genera panorama uniendo ambas cámaras
6. ✅ Detecta el balón en cada frame
7. ✅ Crea video TÁCTICO (campo completo)
8. ✅ Crea video SEGUIMIENTO (zoom al balón)
9. ✅ Guarda en Drive con nombre del equipo
10. ✅ TODO EN UN COMANDO

---

## 💡 Tips

- **Palmada:** Da una palmada fuerte al inicio para sincronizar
- **Múltiples archivos:** El script concatena automáticamente
- **Nombres:** Usa nombres cortos sin espacios (ej: "CD_Alcala")
- **Limpieza:** Borra videos raw después de procesar (ocupan mucho)

---

## 🔧 Solución de Problemas

### "No se encontraron videos"
→ Verifica que los videos estén en `~/Desktop/raw_video_left` y `raw_video_right`

### "Falta homografía"
→ Ejecuta primero: `python3 scripts/configurar_homografia.py`

### Videos no se sincronizan bien
→ Asegúrate de dar palmada fuerte al inicio

---

**¡Así de simple! Copia videos → Ejecuta → Listo** 🚀
