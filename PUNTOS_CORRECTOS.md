# 🎯 PUNTOS CORRECTOS PARA PANORAMA

## 📍 Situación de las Cámaras

```
                BANDA CONTRARIA (NORTE)
    ═══════════════════════════════════════════════
    │                                              │
    │  [Vista Cámara IZQ]    [Vista Cámara DER]  │
    │         ↓                     ↓              │
    │    ┌─────────┐          ┌─────────┐        │
    │    │         │          │         │         │
    │    │  Área   │   ZONA   │  Área   │        │
    │    │  IZQ    │   CENTRO │  DER    │         │
    │    │         │ (SOLAPA) │         │         │
    │    └─────────┘          └─────────┘        │
    │                                              │
    ═══════════════════════════════════════════════
         BANDA CERCANA (SUR) - donde están cámaras
```

## 🎯 LOS 6 PUNTOS (en ZONA CENTRAL que ambas cámaras ven)

```
                BANDA CONTRARIA (lejos, arriba)
    ════════════════════════════════════════════════
    ⑤                                            ⑥
    │              ②                              │
    │              │                              │
    │    ③─────────┼─────────④                   │
    │              │                              │
    │              ①                              │
    │              │                              │
    ════════════════════════════════════════════════
         BANDA CERCANA (cerca, abajo - cámaras aquí)
```

### Descripción de cada punto:

1. **① Centro del campo** (círculo central)
   - El punto MÁS IMPORTANTE
   - Centro absoluto del campo
   - Marca el punto blanco del círculo central

2. **② Medio campo con BANDA CONTRARIA** (arriba)
   - Intersección de línea medio campo con banda contraria
   - Está lejos, arriba en la imagen
   - Fácil de ver en ambas cámaras

3. **③ Área grande IZQ con medio campo**
   - Esquina superior izquierda del área grande (lado medio campo)
   - Donde línea medio campo cruza con línea lateral área grande izquierda

4. **④ Área grande DER con medio campo**
   - Esquina superior derecha del área grande (lado medio campo)
   - Donde línea medio campo cruza con línea lateral área grande derecha

5. **⑤ BANDA CONTRARIA con línea área IZQ**
   - Intersección banda contraria con línea lateral área grande izquierda
   - Esquina superior del área grande izquierda

6. **⑥ BANDA CONTRARIA con línea área DER**
   - Intersección banda contraria con línea lateral área grande derecha
   - Esquina superior del área grande derecha

## ✅ Por Qué Estos Puntos

- **Todos están en la ZONA CENTRAL del campo**
- **AMBAS cámaras los ven claramente**
- **Definen bien la geometría del campo**
- **Están en las líneas pintadas** (fáciles de identificar)
- **No están en las esquinas alejadas**

## ❌ Puntos que NO sirven

- ❌ Esquinas del campo (muy alejadas, solo una cámara las ve bien)
- ❌ Área pequeña en esquinas (muy alejado de zona de solapamiento)
- ❌ Banda cercana (donde están las cámaras, difícil de ver)

## 🎯 Proceso

1. **Imagen IZQUIERDA**: Marca los 6 puntos en el orden indicado
2. **Imagen DERECHA**: Marca **EXACTAMENTE LOS MISMOS 6 puntos** (mismos lugares físicos)
3. El script calcula homografía que alinea ambas imágenes
4. Se genera el panorama con solapamiento correcto

## 💡 Tips

- **Punto ①** (centro): Es el más crítico, márcalo con precisión
- **Puntos ②, ⑤, ⑥**: Están en la banda contraria (lejos, arriba)
- **Puntos ③, ④**: Esquinas del área grande en medio campo
- **Zoom in**: Si necesitas más precisión, acércate a la pantalla
- **Mismo orden**: Marca en el MISMO ORDEN en ambas imágenes

---

## 🚀 Ejecutar

```bash
source futbol_processor_env/bin/activate
python3 configurar_panorama_V2.py
```

Marca los 6 puntos en cada imagen y revisa el resultado en:
```
~/futbol_output/panorama_resultado.jpg
```
