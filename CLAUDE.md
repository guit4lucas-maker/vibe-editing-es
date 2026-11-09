# Vibe Editing — how to run this project

This folder is **Vibe Editing**: a pipeline that turns a long video into finished, captioned,
face-tracked **vertical clips**, in the creator's own brand. It's built to be run by
**non-technical creators** — so when you help someone here, do the work yourself, never make them
run terminal commands or hand-edit files, and explain what's happening in plain English.

## Making clips (the main job)
When the user gives you a video — a YouTube/URL link or a local file — and asks for clips in ANY
plain-English way ("make clips from this", "cut this up", "shorts from this", "/edit <link>"):

1. Read **`plugins/vibe-editing/skills/edit/SKILL.md`** and follow its spine end-to-end.
2. Put source footage in the project's `00_SOURCE/`, scratch in `10_WORK/`, and finished clips in
   **`20_DELIVER/`**. Show the user the delivered clips when you're done.
3. The pipeline mines the strongest moments, hand-cuts, face-tracks to 9:16, captions, mixes music,
   renders, and runs a 6-gate self-audit — a clip that fails a gate doesn't ship.

You do **not** need the `/edit` slash command or any plugin install — run the workflow directly
from the scripts in `plugins/vibe-editing/`. (A `/edit` shortcut is available if the user wants it:
`/plugin marketplace add .` then `/plugin install vibe-editing@vibe-editing-marketplace`.)

## Horizontal "mid" videos (the highlight skill)
If the user wants HORIZONTAL 16:9 "mid" videos for SUBSCRIBER growth from a long recording —
"mine highlights", "make mids", "highlights channel", "post and schedule these" — read
`plugins/vibe-editing/skills/highlight/SKILL.md` and follow it. These are regular 16:9 videos,
NOT 9:16 shorts (shorts = the edit pipeline above). The CTA outro is user-supplied and optional
at `brand/cta/outro.mp4`. POST mode titles + schedules to the user's OWN YouTube via their own
Google sign-in — never any other account.

## First-time setup (only if it isn't set up yet)
If `plugins/vibe-editing/.venv` is missing, or `python3 plugins/vibe-editing/doctor.py` reports
missing tools, set it up first: install only what's missing yourself (ffmpeg, yt-dlp, tesseract,
rclone via Homebrew; a `.venv` with the kit's deps + faster-whisper). A free Groq key in
`plugins/vibe-editing/config/keys.env` makes transcription ~10× faster; without it, it uses free
offline transcription. Full first-run + brand interview: **`ONBOARDING.md`**.

## Brand it / change it
Brand assets live in `brand/` (logos, fonts, music, caption-style, animations). When the user wants
their brand applied, or any change ("captions bigger", "use this logo", "cut tighter", "don't open
on a question"), update the right config and re-run:
- captions → `plugins/vibe-editing/skills/caption-clips/presets/spice.json`
- font → bundled `plugins/vibe-editing/skills/caption-clips/fonts/` (or their own in `brand/fonts/`)
- what makes a clip worth cutting → `plugins/vibe-editing/skills/edit/prompts/clip_select.md`
- music → `brand/music/`

## ESTA INSTALACIÓN ES MULTI-CLIENTE — leé esto antes de cortar nada

El equipo trabaja con varios clientes y **cada uno tiene su marca**. No hay una marca por defecto.

1. **Preguntá para qué cliente es** antes de empezar, salvo que el usuario ya lo haya dicho o el
   proyecto tenga `proyecto.json` con el campo `cliente`.
2. **Cargá su carpeta:** `brand/clientes/<cliente>/` → `perfil.md` (todas las decisiones de marca,
   es la fuente de verdad), `cliente.json` (placa final, paleta, música), `subtitulos.json`
   (preset de subtítulos), `logos/`, `cta/`, `referencias/`.
3. **Cliente nuevo:** copiá `brand/clientes/_plantilla/`, renombrala con el nombre del cliente en
   minúsculas y con guiones, y hacé la entrevista de marca de `ONBOARDING.md` (una pregunta por vez).
   Guardá cada respuesta en `perfil.md` a medida que las dé; esa carpeta es lo que se reutiliza.
4. **Nunca** apliques la marca de un cliente al material de otro, ni dejes los valores del kit
   (Montserrat, amarillo) si el cliente ya tiene perfil.

Reglas que valen para todos los clientes de este equipo:
- **Español.** El material está en español. La transcripción va en `es` por defecto (variable
  `VIBE_LANGUAGE`). Respetá las mayúsculas naturales del texto: no fuerces todo en mayúscula ni en
  minúscula, y no apliques `spice_format.py`, cuyas reglas son para inglés.
- **Sin emojis** en los subtítulos, nunca.
- **Nunca cortes a mitad de frase**, ni al abrir ni al cerrar.
- **Abrí con el gancho**: la frase más fuerte o contraintuitiva, nunca un saludo, una muletilla ni
  una pregunta suelta. Criterios de selección: `plugins/vibe-editing/skills/edit/prompts/clip_select.md`.
- **Duración** 30–60 s salvo que el perfil del cliente diga otra cosa.
- **Placa final** solo si el `cliente.json` la define y se cumple su condición (por ejemplo, que la
  frase se diga textualmente dentro del clip).

## Herramientas propias del equipo (`tools/`)
Probadas con grabaciones de Meet y con apariciones en TV. Ver `tools/README.md`.
- `tools/transcribir.py <video>` — transcribe en español por tramos, deja texto con marcas de tiempo.
- `tools/build_clip.py <ficha>` — arma el clip vertical: corta, ajusta los cortes al silencio, saca
  pausas, compone el cuadro, normaliza el audio, subtitula con el preset del cliente y agrega la placa.
- `tools/revisar.py <proyecto>` — revisa duración, volumen, arranque, emojis, y con qué frase abre y cierra.

## Rules
- Only use this kit — don't pull tools or keys from anywhere else on the machine.
- Never delete the user's source footage. Re-renders overwrite the delivered clip in place.
- Be patient and plain-spoken; assume they've never used a terminal.
