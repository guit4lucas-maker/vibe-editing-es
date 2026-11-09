#!/usr/bin/env python3
"""Revisa los clips entregados antes de mostrárselos a nadie.

Uso:
    python3 tools/revisar.py <proyecto>

Chequea, por cada mp4 de 20_DELIVER: duración, volumen integrado, que la voz
arranque en el primer cuadro, que no haya emojis en los subtítulos, y muestra
con qué frase abre y con cuál cierra (ahí se ven los cortes a mitad de idea).
"""
import json, re, subprocess, sys
from pathlib import Path


def sh(cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def main(proyecto):
    proyecto = Path(proyecto).resolve()
    entrega = proyecto / '20_DELIVER'
    trabajo = proyecto / '10_WORK' / 'clips'
    cfg = {}
    if (proyecto / 'proyecto.json').exists():
        cfg = json.loads((proyecto / 'proyecto.json').read_text())
    minimo, maximo = cfg.get('duracion_min', 28), cfg.get('duracion_max', 62)

    archivos = sorted(entrega.rglob('*.mp4'))
    if not archivos:
        sys.exit(f'No hay clips en {entrega}')
    alertados = 0
    for f in archivos:
        cid = f.stem
        dur = float(sh(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', f]).stdout or 0)
        lufs = (re.findall(r'I:\s+(-?[\d.]+) LUFS',
                           sh(['ffmpeg', '-i', f, '-af', 'ebur128', '-f', 'null', '-']).stderr) or ['?'])[-1]
        sd = sh(['ffmpeg', '-i', f, '-t', '1.5', '-af', 'silencedetect=n=-40dB:d=0.04',
                 '-f', 'null', '-']).stderr
        m = re.search(r'silence_start: (-?[\d.]+)[\s\S]*?silence_end: ([\d.]+)', sd)
        arranque = float(m.group(2)) if m and float(m.group(1)) <= 0.02 else 0.0

        ass = trabajo / cid / 'subtitulos.ass'
        lineas = [re.sub(r'\{[^}]*\}', '', l.split(',', 9)[9]).strip()
                  for l in ass.read_text().splitlines() if l.startswith('Dialogue: 1')] if ass.exists() else []

        alertas = []
        if not (minimo <= dur <= maximo):
            alertas.append(f'dura {dur:.0f}s (fuera de {minimo}-{maximo})')
        if arranque > 0.15:
            alertas.append(f'arranca con {arranque:.2f}s de silencio')
        if lufs != '?' and abs(float(lufs) + 16) > 1.5:
            alertas.append(f'volumen {lufs} LUFS')
        if re.search(r'[\U0001F300-\U0001FAFF\u2600-\u27BF]', ' '.join(lineas)):
            alertas.append('hay emojis en los subtítulos')
        if alertas:
            alertados += 1
        print(f'{"⚠" if alertas else "✓"} {cid[:46]:46} {dur:5.1f}s {lufs:>6} LUFS '
              f'{f.stat().st_size / 1e6:5.1f}MB ' + ('| ' + '; '.join(alertas) if alertas else ''))
        if lineas:
            print(f'    abre: {lineas[0]}  ···  cierra: {lineas[-1]}')
    print(f'\n{len(archivos)} clips, {alertados} con alertas')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
