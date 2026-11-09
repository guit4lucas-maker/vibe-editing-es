# Herramientas del equipo

Tres scripts que cubren el camino completo: transcribir, armar el clip y revisarlo.
Los escribimos sobre el kit porque el flujo original (`/edit`) asume una sola marca,
material en inglés y grabaciones en buena resolución; el material real del equipo son
clases por Meet y apariciones en TV, en español.

No hace falta correrlos a mano: en Claude Code alcanza con pedir "hacé clips de este video".
Esta página es para entender qué hace cada uno y cómo se configura.

## Estructura de un proyecto

```
proyectos/<cliente>/<fecha>_<tema>/
  proyecto.json          configuración (cliente, fuente, formato del cuadro)
  00_SOURCE/             el video original
  10_WORK/               transcripción, fichas de clips, archivos intermedios
  20_DELIVER/            los clips terminados
```

## 1. Transcribir

```bash
python3 tools/transcribir.py proyectos/<...>/00_SOURCE/clase.mp4 proyectos/<...>/10_WORK
```

Deja `<nombre>.txt` (texto con marcas de tiempo, para leer y elegir momentos) y
`<nombre>.json` (cada palabra con su tiempo exacto, para fijar los cortes).
Va por tramos de 10 minutos y los cachea: si se corta, retoma donde quedó.
Necesita la clave gratuita de Groq en `plugins/vibe-editing/config/keys.env`.

## 2. Armar el clip

```bash
python3 tools/build_clip.py proyectos/<...>/10_WORK/clips/01_mi-clip.json
```

La ficha del clip:

```json
{
  "id": "01_el-precio-que-duele",
  "titulo": "El precio que duele",
  "rangos": [[274.63, 281.00], [281.25, 293.20]],
  "enfasis": ["precio", "miedo"],
  "remate": ["duele"],
  "correcciones": { "137": "crecer" }
}
```

- **rangos**: tramos del video original, en segundos. Pueden ser aproximados: el script
  ajusta el final al silencio más cercano y saca las pausas internas de más de 0,3 s.
  Se pueden poner en cualquier orden, así se arma un clip con partes de distintos momentos.
- **enfasis** / **remate**: palabras que se resaltan en el subtítulo, con el color y el peso
  que defina el preset del cliente.
- **correcciones**: arregla una palabra puntual que el dictado escuchó mal. La clave es la
  posición de la palabra en `10_WORK/clips/<id>/palabras.json`.

Los subtítulos se generan transcribiendo el audio **ya cortado**, no el video entero: por eso
el texto y los tiempos coinciden exactamente con lo que se oye, incluso cuando el clip pega
partes de momentos distintos.

## 3. Revisar antes de entregar

```bash
python3 tools/revisar.py proyectos/<...>
```

Marca duración fuera de rango, volumen lejos de −16 LUFS, silencio al arrancar y emojis.
Además imprime con qué frase abre y con cuál cierra cada clip: ahí se ven los cortes a mitad
de idea y los arranques flojos, que son el error más común.

## El formato del cuadro (`layout`)

En `proyecto.json`. Dos formatos cubren casi todo:

**Grabación de Meet o Zoom** (una slide y la cámara en un recuadro):

```json
"layout": {
  "tipo": "slide_y_camara",
  "fondo": "0x1D1E1C",
  "slide":  { "recorte": "720:405:0:67",    "ancho": 1080, "x": 0,   "y": 330 },
  "camara": { "recorte": "234:117:723:204", "ancho": 648,  "x": 216, "y": 990 }
}
```

**Cuadro completo** (TV, podcast, cualquier 16:9 con más de una persona):

```json
"layout": { "tipo": "pantalla_completa", "fondo": "0x111111", "ancho": 1080, "y": 560 }
```

`recorte` es `ancho:alto:x:y` sobre el video original. Los números cambian en cada grabación:
Claude los mide tomando un cuadro del video, no hay que calcularlos a mano. Conviene recortar
un par de píxeles hacia adentro del recuadro de cámara, para sacarle el borde y la etiqueta
con el nombre que pone Meet.

Cuánto se puede agrandar la cámara sin que se note: hasta unas 3 veces su tamaño original.
Más que eso se ve pastoso y conviene dejarla más chica.

## Calidad de salida

`"calidad": "crf 22"` en `proyecto.json`. El kit original exporta a 14 Mbps, pensado para
material 4K: con una grabación de pantalla eso da archivos de 45 MB para 35 segundos, sin
ninguna mejora visible. Con `crf 22` el mismo clip pesa 5 MB. Para material realmente bueno,
`crf 18` o `bitrate 12M`.
