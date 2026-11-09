# Marcas de los clientes

Cada cliente tiene su carpeta en `clientes/`. Ahí vive todo lo suyo, y nada se mezcla
entre clientes.

```
brand/
  clientes/
    _plantilla/         copiala para dar de alta un cliente nuevo
    <cliente>/          una carpeta por cliente, con su marca completa
  cta/                  outro opcional del kit para los videos horizontales
  music/                música sin derechos, si se usa (también sirve VIBE_MUSIC)
```

## Qué hay en la carpeta de un cliente

| Archivo | Para qué |
|---|---|
| `perfil.md` | todas las decisiones de marca, en palabras. Es la fuente de verdad |
| `cliente.json` | lo que leen las herramientas: placa final y su condición, paleta, música |
| `subtitulos.json` | el preset de subtítulos: tipografía, colores, posición, sombra |
| `logos/` | logos en PNG con fondo transparente |
| `cta/` | la placa final, si la marca usa una |
| `referencias/` | capturas de estilo y pruebas, para no repetir decisiones |

## Dar de alta un cliente nuevo

En Claude Code, dentro de esta carpeta:

> "Damos de alta un cliente nuevo: hacé la entrevista de marca y guardá todo en su carpeta."

Hace las preguntas de a una (nombre, logo, tipografía, estilo de subtítulos, música, temas,
cómo abre y cierra un clip, preferencias de edición), arma `brand/clientes/<cliente>/` a partir
de `_plantilla/` y deja cada respuesta escrita en `perfil.md`.

A mano es lo mismo: copiá `_plantilla/`, renombrala con el nombre del cliente en minúsculas y
con guiones, y completá los archivos.

## Cómo se elige el cliente al cortar

En el `proyecto.json` de cada proyecto va el campo `cliente`, con el nombre de la carpeta.
Si falta, Claude lo pregunta antes de empezar.
