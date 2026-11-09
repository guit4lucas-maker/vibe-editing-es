#!/usr/bin/env python3
"""Arma un clip vertical (1080x1920) a partir de una ficha de clip.

Uso:
    python3 tools/build_clip.py <proyecto>/10_WORK/clips/<clip>.json

La ficha del clip:
    {
      "id": "01_el-precio-que-duele",
      "titulo": "El precio que duele",
      "rangos": [[274.6, 281.0], [281.2, 293.2]],   // segundos del video fuente
      "enfasis": ["precio", "miedo"],                // palabras resaltadas
      "remate": ["duele"],                           // palabras del remate (peso máximo)
      "correcciones": {"137": "crecer"}              // arreglos puntuales de transcripción
    }

La configuración del proyecto, en <proyecto>/proyecto.json:
    {
      "cliente": "marca-personal",
      "fuente": "00_SOURCE/clase.mp4",
      "fps": 24,
      "subtitulos_y": 76,              // % desde arriba
      "calidad": "crf 22",             // "crf N" o "bitrate 8M"
      "layout": { ... }                // ver tools/README.md
    }

Los rangos son aproximados: el script ajusta el final al silencio más cercano
y saca las pausas internas de más de 0,3 s.
"""
import json, os, re, subprocess, sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PLUGIN = KIT / 'plugins' / 'vibe-editing'
GEN = PLUGIN / 'skills' / 'caption-clips' / 'scripts' / 'generate_spice.py'
W, H = 1080, 1920

# Errores de transcripción frecuentes -> forma correcta (solo afecta al subtítulo)
CORRECCIONES_GLOBALES = {
    'ormosi': 'Hormozi', 'hermosi': 'Hormozi', 'homosis': 'Hormozi', 'hormosi': 'Hormozi',
    'hormosio': 'Hormozi', 'ormosia': 'Hormozi', 'homosi': 'Hormozi', 'omosi': 'Hormozi',
    'ormozi': 'Hormozi', 'homoossi': 'Hormozi',
}
# Nombres propios y siglas que conservan su mayúscula en medio de una frase
PROPIOS = {'chile', 'santiago', 'vegas', 'nueva', 'york', 'europa', 'estados', 'unidos',
           'latinoamérica', 'covid', 'instagram', 'linkedin', 'tiktok', 'whatsapp', 'youtube',
           'hormozi', 'bcl', 'ltv', 'cac', 'sop', 'sops', 'loom', 'flow'}


def run(cmd, env=None):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env)
    if r.returncode:
        sys.exit(f'FALLÓ: {" ".join(str(c) for c in cmd)[:300]}\n{r.stderr[-1500:]}')
    return r.stdout


def norm(p):
    return re.sub(r'[^\wáéíóúñü]', '', p.lower())


def filtro_layout(cfg, idx, entrada):
    """Devuelve el filtro ffmpeg que arma el cuadro vertical de un segmento."""
    tipo = cfg.get('tipo', 'pantalla_completa')
    fondo = cfg.get('fondo', '0x111111')
    fps = cfg.get('fps', 24)
    base = f"color=c={fondo}:s={W}x{H}:r={fps}[bg{idx}];"
    if tipo == 'slide_y_camara':
        s, c = cfg['slide'], cfg['camara']
        return (f"[{entrada}]split=2[s{idx}][c{idx}];"
                f"[s{idx}]crop={s['recorte']},scale={s.get('ancho', W)}:-2:flags=lanczos[sl{idx}];"
                f"[c{idx}]crop={c['recorte']},scale={c['ancho']}:-2:flags=lanczos,"
                f"unsharp=5:5:{c.get('nitidez', 0.7)}[cam{idx}];"
                + base +
                f"[bg{idx}][sl{idx}]overlay={s.get('x', 0)}:{s['y']}:shortest=1[t{idx}];"
                f"[t{idx}][cam{idx}]overlay={c['x']}:{c['y']}:shortest=1,format=yuv420p[v{idx}]")
    # pantalla_completa: el cuadro entero, centrado, sin recortar
    rec = cfg.get('recorte')
    corte = f"crop={rec}," if rec else ''
    return (f"[{entrada}]{corte}scale={cfg.get('ancho', W)}:-2:flags=lanczos,"
            f"unsharp=5:5:{cfg.get('nitidez', 0.5)}[vid{idx}];"
            + base +
            f"[bg{idx}][vid{idx}]overlay={cfg.get('x', 0)}:{cfg['y']}:shortest=1,format=yuv420p[v{idx}]")


def plan_segmentos(fuente, rangos, env, hueco_min=0.30, colchon=0.10, umbral=-48.0):
    """Ajusta cada rango al silencio real y saca las pausas largas de adentro."""
    import numpy as np, soundfile as sf
    salida, tmp = [], Path(os.getenv('TMPDIR', '/tmp')) / '_vibe_plan.wav'
    for a, b in rangos:
        lo, hi = a - 0.5, b + 0.6
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{lo:.3f}', '-t', f'{hi - lo:.3f}', '-i', fuente,
             '-vn', '-ac', '1', '-ar', '16000', tmp], env)
        x, sr = sf.read(str(tmp)); salto = int(sr * 0.01)
        db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + salto] ** 2)) + 1e-9)
                       for i in range(0, len(x) - salto, salto)])
        callado = db < umbral
        t = lambda i: lo + i / 100
        ia, ib = int((a - lo) * 100), int((b - lo) * 100)
        # El inicio se respeta tal cual (buscarlo hacia atrás arrastra el final de la palabra previa)
        cand = [i for i in range(max(0, ib - 5), min(len(callado), ib + 15)) if callado[i]]
        fin = min(cand) if cand else min(range(max(0, ib - 8), min(len(db), ib + 10)), key=lambda i: db[i])
        cur, i = ia, ia + 1
        while i < fin:
            if callado[i]:
                j = i
                while j < fin and callado[j]:
                    j += 1
                if (j - i) / 100 > hueco_min:
                    salida.append([round(t(cur), 2), round(t(i) + colchon, 2)])
                    cur = j - int(colchon * 100)
                i = j
            else:
                i += 1
        salida.append([round(t(cur), 2), round(t(fin) + 0.04, 2)])
    return [s for s in salida if s[1] - s[0] > 0.08]


def transcribir_clip(video, trabajo, env):
    """Transcribe el audio ya cortado: así el subtítulo coincide exacto con lo que se oye."""
    import requests
    claves = (PLUGIN / 'config' / 'keys.env')
    clave = next((l.split('=', 1)[1].strip() for l in claves.read_text().splitlines()
                  if l.startswith('GROQ_API_KEY=') and len(l) > 14), None)
    if not clave:
        sys.exit('Falta GROQ_API_KEY en plugins/vibe-editing/config/keys.env')
    wav = trabajo / 'audio_clip.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-vn', '-ac', '1', '-ar', '16000', wav], env)
    cache = trabajo / 'transcripcion_clip.json'
    if not cache.exists() or cache.stat().st_mtime < wav.stat().st_mtime:
        with open(wav, 'rb') as fh:
            r = requests.post('https://api.groq.com/openai/v1/audio/transcriptions',
                              headers={'Authorization': f'Bearer {clave}'},
                              files={'file': ('clip.wav', fh, 'audio/wav')},
                              data=[('model', 'whisper-large-v3'), ('language', 'es'),
                                    ('response_format', 'verbose_json'),
                                    ('timestamp_granularities[]', 'word')], timeout=180)
        if r.status_code != 200:
            sys.exit(f'Error de Groq {r.status_code}: {r.text[:300]}')
        cache.write_text(r.text)

    crudo, unidas = json.loads(cache.read_text())['words'], []
    for p in crudo:  # une nombres que el dictado parte en dos ("Homo Ossi" -> "Hormozi")
        if unidas and norm(unidas[-1]['word']) + norm(p['word']) in CORRECCIONES_GLOBALES:
            unidas[-1] = {'word': unidas[-1]['word'] + p['word'].strip(),
                          'start': unidas[-1]['start'], 'end': p['end']}
        else:
            unidas.append(dict(p))

    palabras, venia_punto = [], True
    for p in unidas:
        txt = p['word'].strip()
        if not txt:
            continue
        if norm(txt) in CORRECCIONES_GLOBALES:
            txt = re.sub(r'[\wáéíóúñü]+', CORRECCIONES_GLOBALES[norm(txt)], txt, count=1)
        if not venia_punto and txt[:1].isupper() and norm(txt) not in PROPIOS:
            # El dictado pone mayúscula al abrir su propio segmento: lo usamos como corte de
            # frase para los subtítulos (la coma no se muestra), pero la palabra va en minúscula.
            if palabras and not palabras[-1]['word'].endswith(','):
                palabras[-1]['word'] += ','
            txt = txt[0].lower() + txt[1:]
        if venia_punto and txt[:1].islower():
            txt = txt[0].upper() + txt[1:]
        palabras.append({'word': txt, 'start': round(p['start'], 3), 'end': round(p['end'], 3)})
        venia_punto = txt.rstrip().endswith(('.', '?', '!'))
    return palabras


def main(ficha_path):
    ficha = json.loads(Path(ficha_path).read_text())
    proyecto = Path(ficha_path).resolve().parents[2]
    cfg = json.loads((proyecto / 'proyecto.json').read_text())
    fuente = proyecto / cfg['fuente']
    if not fuente.exists():
        sys.exit(f'No encuentro el video fuente: {fuente}')

    cliente_dir = KIT / 'brand' / 'clientes' / cfg.get('cliente', '_plantilla')
    cliente = {}
    if (cliente_dir / 'cliente.json').exists():
        cliente = json.loads((cliente_dir / 'cliente.json').read_text())

    calidad = cfg.get('calidad', 'crf 22').split()
    venc = (['-c:v', 'libx264', '-preset', 'veryfast', '-crf', calidad[1], '-pix_fmt', 'yuv420p']
            if calidad[0] == 'crf' else
            ['-c:v', 'libx264', '-preset', 'veryfast', '-b:v', calidad[1], '-pix_fmt', 'yuv420p'])
    env = {**os.environ, 'VIBE_BURN_VENC': ' '.join(venc)}

    cid = ficha['id']
    fps = cfg.get('fps', 24)
    segs = ficha.get('segmentos') or plan_segmentos(fuente, ficha['rangos'], env)
    print(f'{cid}: {len(segs)} segmentos, {sum(b - a for a, b in segs):.1f}s')

    trabajo = proyecto / '10_WORK' / 'clips' / cid
    trabajo.mkdir(parents=True, exist_ok=True)
    entrega = proyecto / '20_DELIVER'
    entrega.mkdir(exist_ok=True)

    # 1) cortar, armar el cuadro vertical y normalizar el audio, en una sola pasada
    t0 = max(0.0, min(a for a, _ in segs) - 2.0)
    layout = {**cfg['layout'], 'fps': fps}
    partes, fc = [], []
    for k, (a, b) in enumerate(segs):
        fc.append(f"[0:v]trim={a - t0:.3f}:{b - t0:.3f},setpts=PTS-STARTPTS[raw{k}]")
        fc.append(filtro_layout(layout, k, f'raw{k}'))
        fc.append(f"[0:a]atrim={a - t0:.3f}:{b - t0:.3f},asetpts=PTS-STARTPTS,"
                  f"afade=t=in:d=0.012,afade=t=out:st={b - a - 0.012:.3f}:d=0.012[a{k}]")
        partes.append(f'[v{k}][a{k}]')
    fc.append(''.join(partes) + f'concat=n={len(segs)}:v=1:a=1[vc][ac]')
    fc.append('[ac]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[an]')
    cuerpo = trabajo / 'cuerpo.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.3f}',
         '-t', f'{max(b for _, b in segs) - t0 + 0.5:.3f}', '-i', fuente,
         '-filter_complex', ';'.join(fc), '-map', '[vc]', '-map', '[an]', '-r', fps,
         *venc, '-c:a', 'aac', '-b:a', '192k', cuerpo], env)

    # 2) subtítulos a partir del audio ya cortado
    palabras = transcribir_clip(cuerpo, trabajo, env)
    for i, txt in ficha.get('correcciones', {}).items():
        palabras[int(i)]['word'] = re.sub(r'[\wáéíóúñü]+', txt, palabras[int(i)]['word'], count=1)
    (trabajo / 'palabras.json').write_text(json.dumps({'words': palabras}, ensure_ascii=False, indent=1))
    (trabajo / 'segmentos.json').write_text(json.dumps(segs))

    # 3) resaltado: las palabras de la ficha toman el peso (y el color) del preset del cliente
    enf = {norm(x) for x in ficha.get('enfasis', [])}
    rem = {norm(x) for x in ficha.get('remate', [])}
    estilo = {'words': {}}
    for i, p in enumerate(palabras):
        n = norm(p['word'])
        if n in rem:
            estilo['words'][str(i)] = {'w': 'payoff'}
        elif n in enf:
            estilo['words'][str(i)] = {'w': 'emphasis'}
    (trabajo / 'estilo.json').write_text(json.dumps(estilo))

    preset_cliente = cliente_dir / 'subtitulos.json'
    preset_base = (preset_cliente if preset_cliente.exists()
                   else PLUGIN / 'skills' / 'caption-clips' / 'presets' / 'spice.json')
    preset = json.loads(preset_base.read_text())
    preset['layout']['y_percent_from_top'] = cfg.get('subtitulos_y', 72)
    preset.setdefault('timing', {})['pause_split_s'] = 0.35
    (trabajo / 'preset.json').write_text(json.dumps(preset, ensure_ascii=False, indent=1))

    final = entrega / f'{cid}.mp4'
    (trabajo / 'subtitulos.log').write_text(
        run(['python3', GEN, trabajo / 'palabras.json', '--preset', trabajo / 'preset.json',
             '--style', trabajo / 'estilo.json', '--out', trabajo / 'subtitulos.ass',
             '--burn', cuerpo, '--burn-out', final], env))

    # 4) placa final: solo si el cliente la usa y la frase se dice en el clip
    placa = cliente.get('placa_final')
    dicho = ' '.join(norm(p['word']) for p in palabras)
    if placa and norm(placa.get('frase_gatillo', '')) in dicho.replace(' ', ''):
        img = cliente_dir / placa['archivo']
        dur = placa.get('segundos', 2.0)
        tmp = final.with_suffix('.tmp.mp4')
        run(['ffmpeg', '-v', 'error', '-y', '-i', final,
             '-loop', '1', '-t', dur, '-framerate', fps, '-i', img,
             '-f', 'lavfi', '-t', dur, '-i', 'anullsrc=r=48000:cl=stereo',
             '-filter_complex',
             f'[1:v]scale={W}:{H}:flags=lanczos,format=yuv420p,setsar=1[ec];[0:v]setsar=1[mv];'
             f'[0:a]aformat=sample_rates=48000:channel_layouts=stereo[ma];'
             f'[mv][ma][ec][2:a]concat=n=2:v=1:a=1[v][a]',
             '-map', '[v]', '-map', '[a]', '-r', fps, *venc,
             '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', tmp], env)
        tmp.replace(final)
        nota = f'con placa final ("{placa["frase_gatillo"]}")'
    else:
        nota = 'sin placa final'

    dur = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
               '-of', 'csv=p=0', final], env).strip()
    print(f'LISTO {final} ({float(dur):.1f}s, {nota})')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
