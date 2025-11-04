# 🧪 Modo Prueba - Verificación Rápida

## ¿Por Qué Este Script?

Procesar 8 horas para descubrir que algo está mal es terrible. Este script procesa **solo 60 segundos** para verificar rápidamente que la homografía y el panorama funcionan correctamente.

## 🚀 Ejecutar Prueba

```bash
source futbol_processor_env/bin/activate
python3 procesar_partido_PRUEBA.py
```

## 📝 Pasos

1. **Introduce nombre del equipo** (ej: "PRUEBA")
2. **Marca los 6 puntos** en ambas imágenes (mismo orden)
3. **Observa el panorama en tiempo real**:
   - Se abre ventana mostrando el panorama
   - Puedes ver si las cámaras se unen correctamente
   - Presiona `SPACE` para pausar y examinar
   - Presiona `Q` para salir si ves errores

## 🔍 Qué Verificar

### ✅ El panorama debe verse así:
- Las dos imágenes se unen en el centro del campo
- La zona de solapamiento debe verse natural (sin doble imagen)
- Todo el campo debe ser visible (izquierda + centro + derecha)
- No debe haber zonas negras grandes

### ❌ Problemas Comunes:

**Problema 1: Imagen derecha cortada o negra**
→ El canvas del panorama es demasiado pequeño

**Problema 2: Imágenes no se solapan bien**
→ Los puntos no están bien marcados o en orden diferente

**Problema 3: Distorsión extrema**
→ Los puntos marcados no son correspondientes

## 📁 Salida

Las muestras se guardan en:
```
~/futbol_output/PRUEBA_{equipo}/
  ├── muestra_frame_00300.jpg   (10 segundos)
  ├── muestra_frame_00600.jpg   (20 segundos)
  ├── muestra_frame_00900.jpg   (30 segundos)
  └── ...
```

Abre estas imágenes para verificar cómo se ve el panorama.

## 🔄 Proceso Iterativo

1. **Ejecuta prueba** → `python3 procesar_partido_PRUEBA.py`
2. **Observa resultado** → ¿Se ve bien?
3. **Si NO se ve bien** → Ajusta código y repite
4. **Si se ve bien** → Ejecuta pipeline completo con `procesar_partido_completo.py`

## 💡 Tips

- **Primera vez**: Probablemente necesitarás 2-3 iteraciones para afinar
- **Canvas grande**: El script usa canvas 3× más ancho para ver todo
- **Pausar**: Usa `SPACE` para congelar la imagen y examinar
- **Muestras**: Si no ves bien en tiempo real, revisa las muestras guardadas

## 🎯 Una vez funcione la prueba

Cuando el panorama de 60 segundos se vea perfecto:
1. Aplicaremos los mismos ajustes al pipeline completo
2. Procesarás el partido entero (8 horas)
3. Los dos videos saldrán correctos

---

**¡No pierdas más 8 horas! Verifica primero con 60 segundos** ⚡
