# -*- coding: utf-8 -*-
import pathlib, subprocess, tempfile, shutil, re, html, sys, json
ROOT = pathlib.Path(r'H:\tool\silkworm-trajectory')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
profile = pathlib.Path(tempfile.gettempdir()) / 'udd-rec48-dump'
if profile.exists(): shutil.rmtree(profile, ignore_errors=True)
url = (ROOT / '_backup/rec43/t_new.html').as_uri() + (sys.argv[1] if len(sys.argv) > 1 else '')
p = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--user-data-dir=' + str(profile), '--virtual-time-budget=5000', '--dump-dom', url], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
s = p.stdout.decode('utf-8', 'replace')
m = re.search(r'<div id="out">(.*?)</div>', s, re.S)
text = html.unescape(m.group(1)) if m else 'NO OUTPUT'
if len(sys.argv) > 2:
    mm = re.search(r'\nrc=(\[.*\])\s*$', text, re.S)
    if mm:
        data = json.loads(mm.group(1))
        if sys.argv[2] == 'all':
            for d in data:
                print(d['idx'], d['W'], d['H2'], [(round(c['cx'], 1), round(c['cy'], 1), round(c['r'], 1), c['full'], round(c['support'], 2), round(c['con'], 2)) for c in d['rc']])
        else:
            print(json.dumps(data[int(sys.argv[2])], ensure_ascii=False, indent=2))
    else:
        print('NO RC DEBUG')
else:
    print(text)
