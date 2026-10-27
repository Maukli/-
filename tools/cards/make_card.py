# Карточка упражнения: фото начала и конца (free-exercise-db, Unlicense) + схема тела спереди и сзади
# с мышцами по тирам участия (схемы проекта wger) + легенда. Рендер через Playwright.
# Запуск: python3 tools/cards/make_card.py <spec.json> <out.png>
# spec: {"title","photos":["Barbell_Squat/0","Barbell_Squat/1"],"tiers":{"1":[10,8],"2":[],"3":[11,7,15],"4":[6]},"names":{"1":"...","2":"...","3":"...","4":"..."},"also":"..."}
import base64, json, os, re, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache'); os.makedirs(CACHE, exist_ok=True)
COLORS = {'1': '#9b1b2c', '2': '#e8736c', '3': '#45a852', '4': '#3a70d8'}
LABELS = {'1': 'Главные', '2': 'Вторые', '3': 'Помощники', '4': 'В тонусе'}
FRONT = {1, 2, 3, 4, 6, 10, 13, 14}  # id мышц wger на схеме спереди; остальные сзади: 5, 7, 8, 9, 11, 12, 15


def fetch(url, name):
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        urllib.request.urlretrieve(url, p)
    return p


def svg_inner(path, fill=None):
    s = open(path).read()
    s = s[s.index('<svg'):]
    if fill:
        s = re.sub(r'fill:#fc0000', f'fill:{fill}', s)
        s = re.sub(r'opacity:0\.52424239', 'opacity:0.92', s)
    return re.sub(r'(width|height)="\d+"', '', s, count=2) if not fill else re.sub(r'<svg', '<svg width="100%" height="100%" viewBox="0 0 200 369"', s, count=1)


def body(front, tiers):
    base = fetch(f'https://wger.de/static/images/muscles/muscular_system_{"front" if front else "back"}.svg', f'base_{"f" if front else "b"}.svg')
    s = open(base).read(); s = s[s.index('<svg'):]
    layers = [re.sub(r'<svg', '<svg width="100%" height="100%" viewBox="0 0 200 369"', s, count=1)]
    for t in '4321':  # сначала слабые, поверх главные
        for mid in tiers.get(t, []):
            if (mid in FRONT) == front:
                layers.append(svg_inner(fetch(f'https://wger.de/static/images/muscles/main/muscle-{mid}.svg', f'm{mid}.svg'), COLORS[t]))
    return ''.join(f'<div class="layer">{l}</div>' for l in layers)


def uri(p):
    return 'data:image/jpeg;base64,' + base64.b64encode(open(p, 'rb').read()).decode()


def main(spec_path, out):
    sp = json.load(open(spec_path))
    photos = [uri(fetch(f'https://cdn.jsdelivr.net/gh/yuhonas/free-exercise-db@main/exercises/{p}.jpg', p.replace('/', '_') + '.jpg')) for p in sp['photos']]
    tiers = sp['tiers']
    legend = ''.join(f'<div class="row"><i style="background:{COLORS[t]}"></i><b>{LABELS[t]}</b> {sp["names"][t]}</div>' for t in '1234' if sp['names'].get(t))
    if sp.get('also'):
        legend += f'<div class="row also"><i style="background:#9aa0a6"></i><b>Также работают</b> {sp["also"]}</div>'
    html = f'''<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}}body{{margin:0;width:1500px;background:#fff;font:500 25px/1.35 Inter,sans-serif;color:#1d2125}}
h1{{margin:0;padding:26px 36px 8px;font:800 40px Inter,sans-serif}}
.top{{display:flex;gap:16px;padding:8px 36px}}.ph{{flex:1;height:420px;border-radius:14px;overflow:hidden;background:#f1f1f1;position:relative}}
.ph img{{width:100%;height:100%;object-fit:cover}}.ph span{{position:absolute;left:12px;top:10px;background:rgba(0,0,0,.6);color:#fff;font:700 21px Inter;padding:3px 12px;border-radius:8px}}
.bodies{{width:420px;height:420px;display:flex;gap:6px;background:#f6f6f6;border-radius:14px;padding:10px}}.b{{flex:1;position:relative}}.layer{{position:absolute;inset:0}}
.legend{{padding:14px 36px 26px}}.row{{margin-top:7px;display:flex;align-items:flex-start;gap:12px}}.row i{{width:24px;height:24px;border-radius:6px;flex:none;margin-top:3px}}.row b{{font-weight:800;white-space:nowrap}}.also{{color:#555}}
</style><h1>{sp["title"]}</h1>
<div class="top"><div class="ph"><img src="{photos[0]}"><span>Начало</span></div><div class="ph"><img src="{photos[1]}"><span>Конец</span></div>
<div class="bodies"><div class="b">{body(True, tiers)}</div><div class="b">{body(False, tiers)}</div></div></div>
<div class="legend">{legend}</div>'''
    tmp = out + '.html'; open(tmp, 'w').write(html)
    js = f'''const {{chromium}}=require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1500,height:100}}}});
await p.goto('file://{os.path.abspath(tmp)}');await p.screenshot({{path:'{out}',fullPage:true}});await b.close();}})();'''
    open(tmp + '.js', 'w').write(js)
    subprocess.run(['node', tmp + '.js'], check=True)
    os.remove(tmp); os.remove(tmp + '.js')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
