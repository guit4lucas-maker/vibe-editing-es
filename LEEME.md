# Vibe Editing — edición de clips del equipo

Convierte una grabación larga (una clase por Meet, un podcast, una entrevista de TV) en clips
verticales con subtítulos, listos para publicar. Se trabaja hablándole a Claude Code en español:
no hay que aprender comandos.

Esta copia es la del equipo: está en español, trabaja con **varios clientes** y trae las
herramientas que fuimos ajustando con el material real. Parte del kit original de Acquisition.com
([maddexritter-rgb/vibe-editing](https://github.com/maddexritter-rgb/vibe-editing), licencia MIT).

## Instalar en una Mac nueva

1. Instalá **Claude Code** desde [claude.com/claude-code](https://claude.com/claude-code) e iniciá
   sesión (hace falta plan Pro o Max).
2. Cloná esta carpeta y abrila en Claude Code.
3. Copiá el archivo de claves y pegá la tuya de Groq (gratis, en
   [console.groq.com](https://console.groq.com)):

   ```bash
   cp plugins/vibe-editing/config/keys.env.ejemplo plugins/vibe-editing/config/keys.env
   ```

   La clave es personal: si varios usan la misma, se agota el límite gratuito.
4. En Claude Code, pedile: **"instalá lo que falte para que esto funcione y avisame cuando esté
   listo"**. Él revisa qué falta (ffmpeg, Python 3.10 o superior, yt-dlp, tesseract) y lo instala.
   Si la Mac no tiene permisos de administrador, decíselo: hay una vía que no pide contraseña.

## Usarlo

Abrí la carpeta en Claude Code y pedí lo que necesitás, en español:

- "Hacé clips de este video para <cliente>" y arrastrás el archivo o pegás un link.
- "Los subtítulos más grandes", "cortá más apretado", "sacá la placa final".
- "Subí los clips a Drive, en una carpeta con el nombre del video."

Los clips terminados quedan en `20_DELIVER`, dentro de la carpeta del proyecto.

## Un cliente nuevo

Cada cliente tiene su carpeta en `brand/clientes/`: su perfil de marca, su preset de subtítulos,
sus logos y su placa final. Para dar de alta uno nuevo, pedile a Claude Code:

> "Damos de alta un cliente nuevo: hacé la entrevista de marca y guardá todo en su carpeta."

Te va a preguntar de a una cosa por vez (nombre, logo, tipografía, estilo de subtítulos, música,
de qué tratan los videos, cómo abre y cierra un clip) y deja todo guardado para las próximas veces.

Esta copia no trae clientes cargados: cada equipo da de alta los suyos.

| Cliente | Estilo |
|---|---|
| `_plantilla` | base para copiar y dar de alta el primero |
| `_plantilla` | base para copiar |

## Cómo está armado

| Carpeta | Qué hay |
|---|---|
| `brand/clientes/` | la marca de cada cliente |
| `tools/` | transcribir, armar clips y revisarlos — ver [`tools/README.md`](tools/README.md) |
| `plugins/vibe-editing/` | el kit original: skills, presets, tipografías, modelo de detección de caras |
| `proyectos/` | el trabajo de cada video (no se sube al repositorio) |

## Reglas que valen para todos los clientes

- Sin emojis en los subtítulos.
- Nunca cortar a mitad de frase.
- Abrir con el gancho, nunca con un saludo o una muletilla.
- Entre 30 y 60 segundos, salvo que el perfil del cliente diga otra cosa.
- Revisar con `tools/revisar.py` antes de entregar: avisa de cortes raros, volumen disparejo y
  clips fuera de duración.
