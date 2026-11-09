#!/usr/bin/env python3
"""Transcribe un video largo con Groq, en español, por tramos de 10 minutos.

Uso:
    python3 tools/transcribir.py <video> [carpeta_de_salida]

Deja dos archivos en la carpeta de salida (por defecto, la del video):
    <nombre>.json  palabras con su tiempo exacto, para elegir los cortes
    <nombre>.txt   el texto con marcas de tiempo, para leerlo y elegir momentos

Los tramos quedan cacheados: si se corta a la mitad, al volver a correrlo sigue
desde donde estaba.
"""
import glob, json, os, re, subprocess, sys, time
from pathlib import Path

import requests

KIT = Path(__file__).resolve().parent.parent
CLAVES = KIT / 'plugins' / 'vibe-editing' / 'config' / 'keys.env'


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def main(video, salida=None):
    video = Path(video).resolve()
    salida = Path(salida).resolve() if salida else video.parent
    salida.mkdir(parents=True, exist_ok=True)
    nombre = slug(video.stem)

    clave = next((l.split('=', 1)[1].strip() for l in CLAVES.read_text().splitlines()
                  if l.startswith('GROQ_API_KEY=') and len(l) > 14), None)
    if not clave:
        sys.exit(f'Falta GROQ_API_KEY en {CLAVES}')

    tramos = salida / f'audio_{nombre}'
    tramos.mkdir(exist_ok=True)
    if not glob.glob(f'{tramos}/tramo_*.mp3'):
        print('separando el audio en tramos…', flush=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vn', '-ac', '1',
                        '-ar', '16000', '-c:a', 'libmp3lame', '-b:a', '32k', '-f', 'segment',
                        '-segment_time', '600', '-reset_timestamps', '1',
                        f'{tramos}/tramo_%02d.mp3'], check=True)

    palabras, frases, desfase = [], [], 0.0
    for tramo in sorted(glob.glob(f'{tramos}/tramo_*.mp3')):
        dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                    '-of', 'csv=p=0', tramo], capture_output=True, text=True).stdout)
        cache = Path(tramo).with_suffix('.json')
        if not cache.exists():
            for intento in range(5):
                with open(tramo, 'rb') as fh:
                    r = requests.post('https://api.groq.com/openai/v1/audio/transcriptions',
                                      headers={'Authorization': f'Bearer {clave}'},
                                      files={'file': (Path(tramo).name, fh, 'audio/mpeg')},
                                      data=[('model', 'whisper-large-v3'),
                                            ('response_format', 'verbose_json'), ('language', 'es'),
                                            ('timestamp_granularities[]', 'word'),
                                            ('timestamp_granularities[]', 'segment')], timeout=600)
                if r.status_code == 200:
                    cache.write_text(r.text)
                    break
                print(f'reintento {Path(tramo).name}: {r.status_code} {r.text[:120]}', flush=True)
                time.sleep(20 * (intento + 1))
            else:
                sys.exit(f'No se pudo transcribir {tramo}')
        j = json.loads(cache.read_text())
        palabras += [{'word': p['word'].strip(), 'start': round(p['start'] + desfase, 3),
                      'end': round(p['end'] + desfase, 3)} for p in j.get('words', [])]
        frases += [{'start': round(s['start'] + desfase, 2), 'end': round(s['end'] + desfase, 2),
                    'text': s['text'].strip()} for s in j.get('segments', [])]
        print(f'{Path(tramo).name}: {len(j.get("words", []))} palabras', flush=True)
        desfase += dur

    (salida / f'{nombre}.json').write_text(
        json.dumps({'fuente': str(video), 'words': palabras, 'segments': frases}, ensure_ascii=False))
    with open(salida / f'{nombre}.txt', 'w') as fh:
        for s in frases:
            m, seg = divmod(int(s['start']), 60)
            h, m = divmod(m, 60)
            marca = f'{h}:{m:02d}:{seg:02d}' if h else f'{m}:{seg:02d}'
            fh.write(f'[{marca}] {s["text"]}\n')
    print(f'listo: {len(palabras)} palabras -> {salida / (nombre + ".txt")}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:3])
